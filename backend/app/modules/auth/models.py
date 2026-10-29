from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base
from app.utils.timeutil import utcnow

ROLES = ("student", "company", "staff", "admin")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
