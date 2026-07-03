from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.application import Application


class ApplicationRepository:
    """Provide persistence operations for job applications."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def create(self, application: Application) -> Application:
        self.database_session.add(application)
        self.database_session.flush()
        return application

    def get_by_id(self, application_id: int) -> Application | None:
        return self.database_session.get(Application, application_id)

    def get_by_resume(self, resume_id: int) -> Sequence[Application]:
        statement = (
            select(Application)
            .where(Application.resume_id == resume_id)
            .order_by(Application.id)
        )
        return self.database_session.scalars(statement).all()

    def get_by_job(self, job_id: int) -> Sequence[Application]:
        statement = (
            select(Application)
            .where(Application.job_id == job_id)
            .order_by(Application.id)
        )
        return self.database_session.scalars(statement).all()

    def update_status(
        self,
        application: Application,
        status: str,
    ) -> Application:
        application.status = status
        updated_application = self.database_session.merge(application)
        self.database_session.flush()
        return updated_application
