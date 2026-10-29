from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StudentUpdate(BaseModel):
    """Mọi trường đều tùy chọn. Lần đầu tạo hồ sơ thì bắt buộc có full_name."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    student_code: str | None = Field(None, min_length=1, max_length=20)
    major: str | None = Field(None, max_length=255)
    gpa: float | None = Field(None, ge=0, le=10)
    phone: str | None = Field(None, max_length=20)
    profile_summary: str | None = Field(None, max_length=5000)
    internship_status: Literal["not_started", "searching", "interning", "completed"] | None = None


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_name: str


class CVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    is_primary: bool
    uploaded_at: datetime


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    student_code: str | None = None
    full_name: str
    major: str | None = None
    gpa: float | None = None
    phone: str | None = None
    profile_summary: str | None = None
    internship_status: str
    skills: list[SkillOut] = []


class StudentSummary(BaseModel):
    """Thông tin rút gọn để module M13 hiển thị cho doanh nghiệp."""

    id: int
    student_code: str | None = None
    full_name: str
    major: str | None = None
    gpa: float | None = None
    phone: str | None = None
    profile_summary: str | None = None
    skills: list[str] = []
