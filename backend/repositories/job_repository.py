from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.job import Job


class JobRepository:
    """Provide persistence operations for jobs."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def create(self, job: Job) -> Job:
        self.database_session.add(job)
        self.database_session.flush()
        return job

    def get_by_id(self, job_id: int) -> Job | None:
        return self.database_session.get(Job, job_id)

    def get_by_company(self, company_id: int) -> Sequence[Job]:
        statement = (
            select(Job)
            .where(Job.company_id == company_id)
            .order_by(Job.id)
        )
        return self.database_session.scalars(statement).all()

    def list_all(self) -> Sequence[Job]:
        statement = select(Job).order_by(Job.id)
        return self.database_session.scalars(statement).all()

    def update(self, job: Job) -> Job:
        updated_job = self.database_session.merge(job)
        self.database_session.flush()
        return updated_job

    def delete(self, job: Job) -> None:
        self.database_session.delete(job)
        self.database_session.flush()
