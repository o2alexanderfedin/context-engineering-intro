"""Data access layer for LinkedIn Job Agent."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Application, ApplicationCreate, ApplicationUpdate


class ApplicationRepository:
    """Repository for application database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, application: ApplicationCreate) -> Application:
        """Create a new application record."""
        db_application = Application(
            job_id=application.job_id,
            job_title=application.job_title,
            company_name=application.company_name,
            location=application.location,
            work_arrangement=application.work_arrangement,
            posting_date=application.posting_date,
            job_url=application.job_url,
            job_description=application.job_description,
            match_score=application.match_score,
            salary_range=application.salary_range,
            skills_matched=application.skills_matched,
            notes=application.notes,
            status=application.status,
        )

        try:
            self.session.add(db_application)
            self.session.commit()
            self.session.refresh(db_application)
            return db_application
        except IntegrityError:
            self.session.rollback()
            # Job already exists, return existing
            return self.get_by_job_id(application.job_id)

    def get(self, application_id: UUID) -> Application | None:
        """Get application by ID."""
        return self.session.query(Application).filter(
            Application.application_id == application_id
        ).first()

    def get_by_job_id(self, job_id: str) -> Application | None:
        """Get application by job ID."""
        return self.session.query(Application).filter(
            Application.job_id == job_id
        ).first()

    def update(
        self, application_id: UUID, update_data: ApplicationUpdate
    ) -> Application | None:
        """Update an application record."""
        application = self.get(application_id)
        if not application:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(application, field, value)

        self.session.commit()
        self.session.refresh(application)
        return application

    def delete(self, application_id: UUID) -> bool:
        """Delete an application record."""
        application = self.get(application_id)
        if not application:
            return False

        self.session.delete(application)
        self.session.commit()
        return True

    def list_all(
        self,
        status: str | None = None,
        company: str | None = None,
        min_score: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Application]:
        """List applications with optional filters."""
        query = self.session.query(Application)

        if status:
            query = query.filter(Application.status == status)
        if company:
            query = query.filter(Application.company_name.ilike(f"%{company}%"))
        if min_score is not None:
            query = query.filter(Application.match_score >= min_score)

        return query.order_by(desc(Application.application_date)).limit(limit).offset(
            offset
        ).all()

    def get_recent(self, days: int = 7) -> list[Application]:
        """Get applications from the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Application).filter(
            Application.application_date >= cutoff_date
        ).order_by(desc(Application.application_date)).all()

    def get_stats(self) -> dict:
        """Get application statistics."""
        total = self.session.query(func.count(Application.application_id)).scalar()

        status_counts = dict(
            self.session.query(
                Application.status, func.count(Application.application_id)
            ).group_by(Application.status).all()
        )

        avg_score = self.session.query(func.avg(Application.match_score)).scalar()

        top_companies = self.session.query(
            Application.company_name, func.count(Application.application_id)
        ).group_by(Application.company_name).order_by(
            desc(func.count(Application.application_id))
        ).limit(10).all()

        return {
            "total_applications": total or 0,
            "status_breakdown": status_counts,
            "average_match_score": float(avg_score) if avg_score else 0.0,
            "top_companies": [
                {"company": company, "count": count} for company, count in top_companies
            ],
        }

    def get_todays_count(self) -> int:
        """Get count of applications submitted today."""
        today = datetime.utcnow().date()
        return self.session.query(func.count(Application.application_id)).filter(
            func.date(Application.application_date) == today
        ).scalar() or 0

    def exists(self, job_id: str) -> bool:
        """Check if application already exists for job."""
        return self.session.query(
            self.session.query(Application).filter(
                Application.job_id == job_id
            ).exists()
        ).scalar()

    def cleanup_old(self, days: int = 90) -> int:
        """Delete applications older than N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.session.query(Application).filter(
            and_(
                Application.application_date < cutoff_date,
                Application.status.in_(["rejected", "expired"]),
            )
        ).delete()
        self.session.commit()
        return deleted
