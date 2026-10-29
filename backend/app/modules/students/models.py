from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.timeutil import utcnow

INTERNSHIP_STATUSES = ("not_started", "searching", "interning", "completed")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    student_code = Column(String(20), unique=True)
    full_name = Column(String(255), nullable=False)
    major = Column(String(255))
    gpa = Column(Numeric(4, 2, asdecimal=False))
    phone = Column(String(20))
    profile_summary = Column(Text)
    internship_status = Column(String(20), nullable=False, default="not_started")

    skills = relationship(
        "StudentSkill",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="StudentSkill.id",
        lazy="selectin",
    )
    cvs = relationship(
        "StudentCV",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="StudentCV.id",
    )


class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_name"),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)

    student = relationship("Student", back_populates="skills")


class StudentCV(Base):
    __tablename__ = "student_cvs"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    uploaded_at = Column(DateTime, nullable=False, default=utcnow)

    student = relationship("Student", back_populates="cvs")
