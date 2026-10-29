from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.students.schemas import StudentSummary


# ---------- Doanh nghiệp ----------
class CompanyCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    address: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=255)


class CompanyUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    address: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=255)


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    description: str | None = None
    address: str | None = None
    website: str | None = None


# ---------- Tin thực tập ----------
class InternshipCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(None, max_length=10000)
    requirements: str | None = Field(None, max_length=10000)
    location: str | None = Field(None, max_length=255)
    deadline: date | None = None


class InternshipUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=10000)
    requirements: str | None = Field(None, max_length=10000)
    location: str | None = Field(None, max_length=255)
    deadline: date | None = None
    status: Literal["open", "closed"] | None = None


class InternshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company_name: str | None = None
    title: str
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    deadline: date | None = None
    status: str
    created_at: datetime


class InternshipStats(BaseModel):
    total_internships: int
    open_internships: int
    total_applications: int
    applications_by_status: dict[str, int]


# ---------- Ứng tuyển ----------
class ApplicationCreate(BaseModel):
    cover_letter: str | None = Field(None, max_length=5000)
    cv_id: int | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    student_id: int
    cv_id: int | None = None
    cover_letter: str | None = None
    status: str
    applied_at: datetime


class MyApplicationOut(ApplicationOut):
    internship_title: str | None = None
    company_name: str | None = None


class ApplicantOut(ApplicationOut):
    student: StudentSummary | None = None


class ApplicationStatusUpdate(BaseModel):
    status: Literal["reviewing", "accepted", "rejected"]
