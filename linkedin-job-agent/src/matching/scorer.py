"""Job scoring and matching algorithm."""


from ..ai.claude_client import ClaudeClient
from ..database.models import JobListing, ResumeData


class JobScorer:
    """Score jobs based on resume match."""

    def __init__(self, claude_client: ClaudeClient | None = None):
        """Initialize scorer."""
        self.claude_client = claude_client

    async def score_job(
        self,
        resume: ResumeData,
        job: JobListing,
        use_ai: bool = True,
    ) -> float:
        """Calculate match score for a job."""
        if use_ai and self.claude_client:
            # Use AI for intelligent matching
            score = await self.claude_client.match_job_to_resume(
                resume, job, job.job_description or ""
            )
        else:
            # Fallback to algorithmic scoring
            score = self._calculate_algorithmic_score(resume, job)

        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def score_job_simple(self, resume: ResumeData, job: JobListing) -> float:
        """Simple synchronous scoring without fetching details."""
        return self._calculate_algorithmic_score(resume, job)

    def _calculate_algorithmic_score(
        self,
        resume: ResumeData,
        job: JobListing,
    ) -> float:
        """Calculate score using algorithm."""
        weights = {
            "skills": 0.35,
            "title": 0.25,
            "location": 0.15,
            "experience": 0.15,
            "education": 0.10,
        }

        scores = {
            "skills": self._score_skills(resume, job),
            "title": self._score_title(resume, job),
            "location": self._score_location(resume, job),
            "experience": self._score_experience(resume, job),
            "education": self._score_education(resume, job),
        }

        # Calculate weighted average
        total_score = sum(
            scores[key] * weights[key]
            for key in weights
        )

        return total_score

    def _score_skills(self, resume: ResumeData, job: JobListing) -> float:
        """Score based on skill match."""
        if not resume.skills:
            return 0.5

        # Extract skills from job title and description
        job_text = f"{job.job_title} {job.job_description or ''}".lower()

        matching_skills = 0
        for skill in resume.skills:
            if skill.lower() in job_text:
                matching_skills += 1

        # Calculate percentage match
        match_ratio = matching_skills / len(resume.skills)

        # Boost score if many skills match
        if matching_skills >= 5:
            match_ratio = min(match_ratio * 1.2, 1.0)

        return match_ratio

    def _score_title(self, resume: ResumeData, job: JobListing) -> float:
        """Score based on job title relevance."""
        job_title_lower = job.job_title.lower()

        # Check preferred roles
        if resume.preferred_roles:
            for role in resume.preferred_roles:
                if self._fuzzy_match(role.lower(), job_title_lower):
                    return 1.0

        # Check recent experience
        if resume.experience:
            recent_title = resume.experience[0].get("title", "").lower()
            if self._fuzzy_match(recent_title, job_title_lower):
                return 0.9

        # Check for common keywords
        title_keywords = self._extract_title_keywords(job_title_lower)
        resume_keywords = self._extract_resume_keywords(resume)

        common_keywords = title_keywords & resume_keywords
        if common_keywords:
            return min(len(common_keywords) * 0.25, 0.8)

        return 0.3  # Base score for any job

    def _score_location(self, resume: ResumeData, job: JobListing) -> float:
        """Score based on location match."""
        # Remote jobs always score high
        if job.work_arrangement == "remote":
            return 1.0

        # Hybrid scores moderately
        if job.work_arrangement == "hybrid":
            return 0.8

        # Check location match for onsite
        if resume.location and job.location:
            resume_loc = resume.location.lower()
            job_loc = job.location.lower()

            # Same city/state
            if any(part in job_loc for part in resume_loc.split(",")):
                return 0.9

            # Same state
            state_match = self._extract_state(resume_loc) == self._extract_state(job_loc)
            if state_match:
                return 0.6

        return 0.3  # Different location

    def _score_experience(self, resume: ResumeData, job: JobListing) -> float:
        """Score based on experience relevance."""
        if not resume.experience:
            return 0.3  # Entry level

        # More experience generally scores higher
        exp_count = len(resume.experience)
        if exp_count >= 5:
            return 0.9
        elif exp_count >= 3:
            return 0.8
        elif exp_count >= 1:
            return 0.6
        else:
            return 0.4

    def _score_education(self, resume: ResumeData, job: JobListing) -> float:
        """Score based on education."""
        if not resume.education:
            return 0.5  # Neutral if no education listed

        # Check for advanced degrees
        for edu in resume.education:
            degree = edu.get("degree", "").lower()
            if any(adv in degree for adv in ["master", "phd", "doctorate", "mba"]):
                return 1.0
            elif any(bach in degree for bach in ["bachelor", "b.s.", "b.a."]):
                return 0.8

        return 0.6  # Some education

    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Check if strings are similar."""
        # Direct substring match
        if str1 in str2 or str2 in str1:
            return True

        # Word overlap
        words1 = set(str1.split())
        words2 = set(str2.split())
        common_words = words1 & words2

        # If significant overlap
        if len(common_words) >= min(len(words1), len(words2)) * 0.5:
            return True

        return False

    def _extract_title_keywords(self, title: str) -> set[str]:
        """Extract keywords from job title."""
        # Common title keywords
        keywords = set()

        keyword_map = {
            "engineer": ["engineer", "engineering", "developer", "programmer"],
            "senior": ["senior", "sr", "lead", "principal"],
            "junior": ["junior", "jr", "entry", "associate"],
            "full": ["full", "stack", "fullstack"],
            "front": ["front", "frontend", "ui", "ux"],
            "back": ["back", "backend", "server"],
            "data": ["data", "analytics", "scientist", "analyst"],
            "cloud": ["cloud", "devops", "infrastructure", "sre"],
            "mobile": ["mobile", "ios", "android", "react native"],
        }

        title_lower = title.lower()
        for key, values in keyword_map.items():
            if any(v in title_lower for v in values):
                keywords.add(key)

        return keywords

    def _extract_resume_keywords(self, resume: ResumeData) -> set[str]:
        """Extract keywords from resume."""
        keywords = set()

        # From skills
        for skill in resume.skills:
            skill_lower = skill.lower()
            if "engineer" in skill_lower or "developer" in skill_lower:
                keywords.add("engineer")
            if "full stack" in skill_lower:
                keywords.add("full")
            if "front" in skill_lower or "react" in skill_lower or "vue" in skill_lower:
                keywords.add("front")
            if "back" in skill_lower or "node" in skill_lower or "django" in skill_lower:
                keywords.add("back")
            if "data" in skill_lower or "machine learning" in skill_lower:
                keywords.add("data")
            if "cloud" in skill_lower or "aws" in skill_lower or "azure" in skill_lower:
                keywords.add("cloud")

        # From experience
        if resume.experience:
            for exp in resume.experience[:2]:  # Recent experience
                title = exp.get("title", "").lower()
                keywords.update(self._extract_title_keywords(title))

        return keywords

    def _extract_state(self, location: str) -> str | None:
        """Extract state abbreviation from location."""
        import re

        # Look for 2-letter state code
        state_match = re.search(r"\b([A-Z]{2})\b", location.upper())
        if state_match:
            return state_match.group(1)

        return None

    async def rank_jobs(
        self,
        resume: ResumeData,
        jobs: list[JobListing],
        min_score: float = 0.0,
    ) -> list[tuple[JobListing, float]]:
        """Rank jobs by match score."""
        scored_jobs = []

        for job in jobs:
            score = await self.score_job(resume, job)
            if score >= min_score:
                scored_jobs.append((job, score))

        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[1], reverse=True)

        return scored_jobs
