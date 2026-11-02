from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Company


def get_company_by_user_id(db: Session, user_id: int) -> Company | None:
    return db.scalar(select(Company).where(Company.user_id == user_id))
