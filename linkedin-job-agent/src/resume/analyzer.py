"""Resume analyzer using Claude AI."""

import json
from typing import Any

from ..ai.claude_client import ClaudeClient
from ..database.models import ResumeData


class ResumeAnalyzer:
    """Analyze resumes using Claude AI for deeper insights."""

    def __init__(self, claude_client: ClaudeClient | None = None):
        """Initialize analyzer with Claude client."""
        self.claude_client = claude_client or ClaudeClient()

    async def analyze(self, resume_data: ResumeData) -> dict[str, Any]:
        """Analyze resume data for enhanced insights."""
        prompt = self._build_analysis_prompt(resume_data)

        try:
            response = await self.claude_client.analyze_text(prompt)
            return self._parse_analysis_response(response)
        except Exception:
            # Fallback to basic analysis if Claude fails
            return self._basic_analysis(resume_data)

    async def extract_key_strengths(self, resume_data: ResumeData) -> list[str]:
        """Extract key strengths from resume."""
        prompt = f"""
        Based on this resume, identify the top 5 key strengths:

        Name: {resume_data.name}
        Skills: {', '.join(resume_data.skills[:20])}
        Experience: {len(resume_data.experience)} positions

        Return as JSON: {{"strengths": ["strength1", "strength2", ...]}}
        """

        try:
            response = await self.claude_client.analyze_text(prompt)
            result = json.loads(response)
            return result.get("strengths", [])
        except Exception:
            return self._extract_basic_strengths(resume_data)

    async def suggest_job_titles(self, resume_data: ResumeData) -> list[str]:
        """Suggest relevant job titles based on resume."""
        prompt = f"""
        Based on this professional profile, suggest 5 relevant job titles to search for:

        Current/Recent Role: {resume_data.experience[0]['title'] if resume_data.experience else 'Not specified'}
        Skills: {', '.join(resume_data.skills[:15])}
        Preferred Roles: {', '.join(resume_data.preferred_roles)}

        Return as JSON: {{"titles": ["title1", "title2", ...]}}
        """

        try:
            response = await self.claude_client.analyze_text(prompt)
            result = json.loads(response)
            return result.get("titles", [])
        except Exception:
            return self._suggest_basic_titles(resume_data)

    async def calculate_experience_level(self, resume_data: ResumeData) -> str:
        """Calculate experience level from resume."""
        if not resume_data.experience:
            return "entry"

        # Estimate total years of experience
        total_years = 0
        for exp in resume_data.experience:
            duration = exp.get("duration", "")
            years = self._extract_years_from_duration(duration)
            total_years += years

        if total_years < 2:
            return "entry"
        elif total_years < 5:
            return "junior"
        elif total_years < 10:
            return "mid"
        else:
            return "senior"

    def _build_analysis_prompt(self, resume_data: ResumeData) -> str:
        """Build prompt for resume analysis."""
        return f"""
        Analyze this resume and provide structured insights:

        Name: {resume_data.name}
        Location: {resume_data.location}
        Email: {resume_data.email}

        Skills: {', '.join(resume_data.skills)}

        Experience ({len(resume_data.experience)} positions):
        {self._format_experience(resume_data.experience[:3])}

        Education:
        {self._format_education(resume_data.education[:2])}

        Preferred Roles: {', '.join(resume_data.preferred_roles)}

        Provide analysis as JSON with:
        1. skill_categories: Group skills by category
        2. experience_summary: Brief summary of experience
        3. key_qualifications: Top 5 qualifications
        4. recommended_job_searches: Suggested search terms
        5. estimated_salary_range: Based on experience and skills
        """

    def _format_experience(self, experience: list[dict[str, str]]) -> str:
        """Format experience for prompt."""
        if not experience:
            return "No experience listed"

        formatted = []
        for exp in experience:
            formatted.append(
                f"- {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')} "
                f"({exp.get('duration', 'Unknown')})"
            )
        return "\n".join(formatted)

    def _format_education(self, education: list[dict[str, str]]) -> str:
        """Format education for prompt."""
        if not education:
            return "No education listed"

        formatted = []
        for edu in education:
            formatted.append(f"- {edu.get('degree', 'Unknown')} ({edu.get('year', 'Unknown')})")
        return "\n".join(formatted)

    def _parse_analysis_response(self, response: str) -> dict[str, Any]:
        """Parse Claude's analysis response."""
        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Parse as text if not JSON
            return {
                "raw_analysis": response,
                "skill_categories": {},
                "experience_summary": response[:200],
                "key_qualifications": [],
                "recommended_job_searches": [],
            }

    def _basic_analysis(self, resume_data: ResumeData) -> dict[str, Any]:
        """Provide basic analysis without AI."""
        # Categorize skills
        skill_categories = self._categorize_skills(resume_data.skills)

        # Generate experience summary
        exp_summary = f"Professional with {len(resume_data.experience)} positions"
        if resume_data.experience:
            recent = resume_data.experience[0]
            exp_summary = f"{recent.get('title', 'Professional')} with experience at {recent.get('company', 'various companies')}"

        return {
            "skill_categories": skill_categories,
            "experience_summary": exp_summary,
            "key_qualifications": resume_data.skills[:5],
            "recommended_job_searches": resume_data.preferred_roles or ["Software Engineer"],
            "estimated_salary_range": {"min": 80000, "max": 150000},
        }

    def _categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """Categorize skills into groups."""
        categories = {
            "Programming Languages": [],
            "Frameworks": [],
            "Databases": [],
            "Cloud & DevOps": [],
            "Other": [],
        }

        programming = {"Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust"}
        frameworks = {"React", "Angular", "Vue", "Django", "Flask", "Spring", "Node.js"}
        databases = {"SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra"}
        cloud = {"AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins"}

        for skill in skills:
            if skill in programming:
                categories["Programming Languages"].append(skill)
            elif skill in frameworks:
                categories["Frameworks"].append(skill)
            elif skill in databases:
                categories["Databases"].append(skill)
            elif skill in cloud:
                categories["Cloud & DevOps"].append(skill)
            else:
                categories["Other"].append(skill)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _extract_basic_strengths(self, resume_data: ResumeData) -> list[str]:
        """Extract basic strengths without AI."""
        strengths = []

        # Based on skills count
        if len(resume_data.skills) > 10:
            strengths.append("Diverse technical skill set")

        # Based on experience
        if len(resume_data.experience) > 3:
            strengths.append("Extensive professional experience")

        # Based on specific skills
        if any(s in resume_data.skills for s in ["Python", "Java", "JavaScript"]):
            strengths.append("Strong programming foundation")

        if any(s in resume_data.skills for s in ["AWS", "Azure", "GCP"]):
            strengths.append("Cloud platform expertise")

        if any(s in resume_data.skills for s in ["Docker", "Kubernetes"]):
            strengths.append("Container and orchestration experience")

        return strengths[:5]

    def _suggest_basic_titles(self, resume_data: ResumeData) -> list[str]:
        """Suggest basic job titles without AI."""
        titles = []

        # Use preferred roles if available
        if resume_data.preferred_roles:
            titles.extend(resume_data.preferred_roles)

        # Add based on skills
        skill_set = set(resume_data.skills)

        if {"Python", "Django", "Flask"} & skill_set:
            titles.append("Python Developer")

        if {"React", "Angular", "Vue"} & skill_set:
            titles.append("Frontend Developer")

        if {"Node.js", "Express"} & skill_set:
            titles.append("Backend Developer")

        if {"Docker", "Kubernetes", "Jenkins"} & skill_set:
            titles.append("DevOps Engineer")

        if {"AWS", "Azure", "GCP"} & skill_set:
            titles.append("Cloud Engineer")

        # Default fallback
        if not titles:
            titles = ["Software Engineer", "Developer", "Programmer"]

        return titles[:5]

    def _extract_years_from_duration(self, duration: str) -> int:
        """Extract years from duration string."""
        import re

        # Look for year patterns
        year_match = re.search(r"(\d+)\s*(?:years?|yrs?)", duration, re.IGNORECASE)
        if year_match:
            return int(year_match.group(1))

        # Look for date range (e.g., "2020-2023")
        range_match = re.search(r"(\d{4})\s*-\s*(\d{4}|Present)", duration, re.IGNORECASE)
        if range_match:
            start_year = int(range_match.group(1))
            if range_match.group(2).lower() == "present":
                from datetime import datetime
                end_year = datetime.now().year
            else:
                end_year = int(range_match.group(2))
            return end_year - start_year

        return 1  # Default to 1 year if can't parse
