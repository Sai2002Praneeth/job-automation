from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.company import Company


class CompanyRepository:
    """Provide persistence operations for companies."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def create(self, company: Company) -> Company:
        self.database_session.add(company)
        self.database_session.flush()
        return company

    def get_by_id(self, company_id: int) -> Company | None:
        return self.database_session.get(Company, company_id)

    def get_by_name(self, name: str) -> Company | None:
        statement = (
            select(Company)
            .where(Company.name == name)
            .order_by(Company.id)
        )
        return self.database_session.scalars(statement).first()

    def list_all(self) -> Sequence[Company]:
        statement = select(Company).order_by(Company.id)
        return self.database_session.scalars(statement).all()

    def update(self, company: Company) -> Company:
        updated_company = self.database_session.merge(company)
        self.database_session.flush()
        return updated_company

    def delete(self, company: Company) -> None:
        self.database_session.delete(company)
        self.database_session.flush()
