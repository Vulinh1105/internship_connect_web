from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.timeutil import utcnow

INTERNSHIP_STATUSES = ("open", "closed")
APPLICATION_STATUSES = ("pending", "reviewing", "accepted", "rejected", "withdrawn")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(String(255))
    website = Column(String(255))

    internships = relationship("Internship", back_populates="company")


class Internship(Base):
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    location = Column(String(255))
    deadline = Column(Date)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, default=utcnow)

    company = relationship("Company", back_populates="internships")
    applications = relationship("Application", back_populates="internship")

    @property
    def company_name(self) -> str | None:
        return self.company.company_name if self.company else None


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("internship_id", "student_id"),)

    id = Column(Integer, primary_key=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    cv_id = Column(Integer, ForeignKey("student_cvs.id"), nullable=True)
    cover_letter = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
    applied_at = Column(DateTime, nullable=False, default=utcnow)

    internship = relationship("Internship", back_populates="applications")

    @property
    def internship_title(self) -> str | None:
        return self.internship.title if self.internship else None

    @property
    def company_name(self) -> str | None:
        return self.internship.company_name if self.internship else None
