"""Claude AI client for intelligent job matching."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from ..database.models import JobListing, ResumeData


class ClaudeClient:
    """Client for Claude AI integration."""

    def __init__(self, engine_path: str = "~/claude-eng"):
        """Initialize Claude client."""
        self.engine_path = engine_path
        expanded = os.path.expanduser(engine_path)
        if not Path(expanded).exists():
            print(f"Warning: Claude engine not found at {expanded}")
            print("Using fallback AI analysis (basic keyword matching)")
            self.engine_path = None

    async def analyze_text(self, prompt: str) -> str:
        """Analyze text using Claude."""
        if not self.engine_path:
            return self._fallback_response(prompt)

        try:
            # Expand user path
            expanded_path = os.path.expanduser(self.engine_path)
            
            # Run Claude engine with -p flag
            process = await asyncio.create_subprocess_exec(
                expanded_path,
                "-p",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Get response
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                print(f"Claude engine error: {error_msg}")
                return self._fallback_response(prompt)

            return stdout.decode().strip()

        except Exception as e:
            print(f"Failed to call Claude: {e}")
            return self._fallback_response(prompt)

    async def match_job_to_resume(
        self,
        resume_data: ResumeData,
        job_listing: JobListing,
        job_description: str = "",
    ) -> float:
        """Calculate match score between resume and job."""
        prompt = self._build_match_prompt(resume_data, job_listing, job_description)

        try:
            response = await self.analyze_text(prompt)
            result = self._parse_match_response(response)
            return result.get("score", 0.0)
        except Exception as e:
            print(f"Failed to match job: {e}")
            return self._calculate_basic_match(resume_data, job_listing, job_description)

    async def analyze_resume(self, resume_data: ResumeData) -> dict[str, Any]:
        """Analyze resume for insights."""
        prompt = f"""
        Analyze this resume and provide structured insights:

        Name: {resume_data.name}
        Skills: {', '.join(resume_data.skills[:30])}
        Experience: {len(resume_data.experience)} positions
        Education: {len(resume_data.education)} degrees

        Provide a JSON response with:
        {{
            "skill_level": "entry|junior|mid|senior|expert",
            "top_skills": ["skill1", "skill2", ...],
            "industry_focus": "primary industry",
            "years_experience": estimated_number,
            "salary_range": {{"min": number, "max": number}},
            "best_fit_roles": ["role1", "role2", ...]
        }}
        """

        try:
            response = await self.analyze_text(prompt)
            return json.loads(response)
        except Exception:
            return self._basic_resume_analysis(resume_data)

    async def generate_cover_letter(
        self,
        resume_data: ResumeData,
        job_listing: JobListing,
        company_info: str = "",
    ) -> str:
        """Generate a cover letter for the application."""
        prompt = f"""
        Write a professional cover letter for this job application:

        Candidate: {resume_data.name}
        Position: {job_listing.job_title}
        Company: {job_listing.company_name}

        Candidate Skills: {', '.join(resume_data.skills[:15])}
        Recent Experience: {resume_data.experience[0]['title'] if resume_data.experience else 'Entry level'}

        {f"Company Info: {company_info[:500]}" if company_info else ""}

        Write a 3-paragraph cover letter that:
        1. Shows enthusiasm for the role
        2. Highlights relevant skills and experience
        3. Explains why you're a good fit

        Keep it professional and under 250 words.
        """

        try:
            return await self.analyze_text(prompt)
        except Exception:
            return self._generate_basic_cover_letter(resume_data, job_listing)

    def _build_match_prompt(
        self,
        resume_data: ResumeData,
        job_listing: JobListing,
        job_description: str,
    ) -> str:
        """Build prompt for job matching."""
        return f"""
        Calculate match score between this resume and job:

        RESUME:
        Skills: {', '.join(resume_data.skills[:30])}
        Experience: {self._format_experience(resume_data.experience[:3])}
        Education: {self._format_education(resume_data.education[:2])}
        Location: {resume_data.location}

        JOB:
        Title: {job_listing.job_title}
        Company: {job_listing.company_name}
        Location: {job_listing.location}
        Work Arrangement: {job_listing.work_arrangement}

        JOB DESCRIPTION (first 1000 chars):
        {job_description[:1000] if job_description else 'Not provided'}

        Return a JSON response:
        {{
            "score": 0.0-1.0,
            "matching_skills": ["skill1", "skill2"],
            "missing_skills": ["skill1", "skill2"],
            "experience_match": "under|exact|over",
            "location_match": true/false,
            "reason": "Brief explanation"
        }}
        """

    def _format_experience(self, experience: list) -> str:
        """Format experience for prompt."""
        if not experience:
            return "No experience"

        formatted = []
        for exp in experience:
            formatted.append(f"{exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}")
        return "; ".join(formatted)

    def _format_education(self, education: list) -> str:
        """Format education for prompt."""
        if not education:
            return "No education"

        formatted = []
        for edu in education:
            formatted.append(edu.get('degree', 'Unknown'))
        return "; ".join(formatted)

    def _parse_match_response(self, response: str) -> dict[str, Any]:
        """Parse match response from Claude."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        # Fallback parsing
        score = 0.5
        if "high match" in response.lower() or "excellent" in response.lower():
            score = 0.9
        elif "good match" in response.lower():
            score = 0.75
        elif "moderate" in response.lower():
            score = 0.6
        elif "poor" in response.lower() or "low match" in response.lower():
            score = 0.3

        return {"score": score, "reason": response[:200]}

    def _calculate_basic_match(
        self,
        resume_data: ResumeData,
        job_listing: JobListing,
        job_description: str,
    ) -> float:
        """Calculate basic match score without AI."""
        score = 0.0
        factors = 0

        # Skill matching
        job_text = f"{job_listing.job_title} {job_description}".lower()
        matching_skills = 0
        for skill in resume_data.skills:
            if skill.lower() in job_text:
                matching_skills += 1

        if resume_data.skills:
            skill_score = min(matching_skills / len(resume_data.skills), 1.0)
            score += skill_score * 0.4
            factors += 0.4

        # Title matching
        if resume_data.preferred_roles:
            for role in resume_data.preferred_roles:
                if role.lower() in job_listing.job_title.lower():
                    score += 0.2
                    factors += 0.2
                    break

        # Location matching
        if job_listing.work_arrangement == "remote":
            score += 0.2
            factors += 0.2
        elif resume_data.location.lower() in job_listing.location.lower():
            score += 0.2
            factors += 0.2

        # Experience relevance
        if resume_data.experience:
            score += 0.2
            factors += 0.2

        return score / factors if factors > 0 else 0.5

    def _basic_resume_analysis(self, resume_data: ResumeData) -> dict[str, Any]:
        """Basic resume analysis without AI."""
        # Estimate skill level
        len(resume_data.skills)
        exp_count = len(resume_data.experience)

        if exp_count == 0:
            skill_level = "entry"
        elif exp_count < 2:
            skill_level = "junior"
        elif exp_count < 5:
            skill_level = "mid"
        else:
            skill_level = "senior"

        # Estimate salary range
        salary_ranges = {
            "entry": {"min": 60000, "max": 80000},
            "junior": {"min": 80000, "max": 110000},
            "mid": {"min": 110000, "max": 150000},
            "senior": {"min": 150000, "max": 200000},
        }

        return {
            "skill_level": skill_level,
            "top_skills": resume_data.skills[:5],
            "industry_focus": "Technology",
            "years_experience": exp_count * 2,  # Rough estimate
            "salary_range": salary_ranges[skill_level],
            "best_fit_roles": resume_data.preferred_roles[:3] or ["Software Engineer"],
        }

    def _generate_basic_cover_letter(
        self,
        resume_data: ResumeData,
        job_listing: JobListing,
    ) -> str:
        """Generate basic cover letter without AI."""
        return f"""Dear Hiring Manager,

I am writing to express my interest in the {job_listing.job_title} position at {job_listing.company_name}. With my background in {', '.join(resume_data.skills[:3])}, I believe I would be a valuable addition to your team.

My experience includes {len(resume_data.experience)} professional positions where I have developed expertise in {', '.join(resume_data.skills[3:6])}. I am particularly drawn to this role because it aligns with my career goals and technical interests.

I would welcome the opportunity to discuss how my skills and experience can contribute to {job_listing.company_name}'s continued success. Thank you for considering my application.

Sincerely,
{resume_data.name}"""

    def _fallback_response(self, prompt: str) -> str:
        """Provide fallback response when Claude is unavailable."""
        if "match" in prompt.lower():
            return '{"score": 0.7, "reason": "Claude unavailable, using basic matching"}'
        elif "analyze" in prompt.lower():
            return '{"skill_level": "mid", "top_skills": [], "industry_focus": "Technology"}'
        else:
            return "Claude AI is currently unavailable. Using fallback response."
