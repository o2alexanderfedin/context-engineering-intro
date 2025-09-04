"""Job filtering based on criteria."""

from datetime import datetime, timedelta

from ..database.models import JobCriteria, JobListing


class JobFilter:
    """Filter jobs based on criteria."""

    def __init__(self, criteria: JobCriteria):
        """Initialize filter with criteria."""
        self.criteria = criteria

    def filter_jobs(self, jobs: list[JobListing]) -> list[JobListing]:
        """Apply all filters to job list."""
        filtered = jobs

        # Apply filters in sequence
        filtered = self.filter_by_date(filtered)
        filtered = self.filter_by_location(filtered)
        filtered = self.filter_by_work_arrangement(filtered)
        filtered = self.filter_by_company(filtered)

        return filtered

    def filter_by_date(self, jobs: list[JobListing]) -> list[JobListing]:
        """Filter jobs by posting date."""
        if not self.criteria.posting_age_days:
            return jobs

        cutoff_date = datetime.now() - timedelta(days=self.criteria.posting_age_days)
        filtered = []

        for job in jobs:
            # Include if posting date is recent or unknown
            if not job.posting_date or job.posting_date >= cutoff_date:
                filtered.append(job)

        return filtered

    def filter_by_location(self, jobs: list[JobListing]) -> list[JobListing]:
        """Filter jobs by location."""
        location_config = self.criteria.location
        if not location_config:
            return jobs

        filtered = []
        high_demand_areas = location_config.get("high_demand_areas", [])

        for job in jobs:
            # Always include remote jobs
            if job.work_arrangement == "remote":
                filtered.append(job)
                continue

            # Check high demand areas
            if high_demand_areas and job.location:
                for area in high_demand_areas:
                    if area.lower() in job.location.lower():
                        filtered.append(job)
                        break
            else:
                # If no specific location filter, include all
                filtered.append(job)

        return filtered

    def filter_by_work_arrangement(self, jobs: list[JobListing]) -> list[JobListing]:
        """Filter jobs by work arrangement."""
        if not self.criteria.work_arrangements:
            return jobs

        allowed_arrangements = set(
            arr.lower() for arr in self.criteria.work_arrangements
        )

        filtered = []
        for job in jobs:
            if not job.work_arrangement:
                # Include if arrangement is unknown
                filtered.append(job)
            elif job.work_arrangement.lower() in allowed_arrangements:
                filtered.append(job)

        return filtered

    def filter_by_company(self, jobs: list[JobListing]) -> list[JobListing]:
        """Filter out excluded companies."""
        if not self.criteria.excluded_companies:
            return jobs

        excluded = set(
            company.lower() for company in self.criteria.excluded_companies
        )

        filtered = []
        for job in jobs:
            if not job.company_name:
                filtered.append(job)
            elif job.company_name.lower() not in excluded:
                filtered.append(job)

        return filtered

    def filter_by_salary(self, jobs: list[JobListing]) -> list[JobListing]:
        """Filter jobs by salary range."""
        if not self.criteria.salary_range:
            return jobs

        min_salary = self.criteria.salary_range.get("min", 0)
        max_salary = self.criteria.salary_range.get("max")

        filtered = []
        for job in jobs:
            if not job.salary_range:
                # Include if salary unknown
                filtered.append(job)
                continue

            job_min = job.salary_range.get("min", 0)
            job_max = job.salary_range.get("max", float("inf"))

            # Check if ranges overlap
            if min_salary and job_max < min_salary:
                continue  # Job pays less than minimum

            if max_salary and job_min > max_salary:
                continue  # Job requires more than maximum

            filtered.append(job)

        return filtered
