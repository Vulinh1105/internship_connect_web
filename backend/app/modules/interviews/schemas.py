from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InterviewCreate(BaseModel):
    application_id: int
    scheduled_at: datetime
    location: str = Field(min_length=1, max_length=255, description="Địa điểm hoặc link họp online")
    note: str | None = Field(None, max_length=2000)


class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    location: str | None = Field(None, min_length=1, max_length=255)
    note: str | None = Field(None, max_length=2000)


class InterviewRespond(BaseModel):
    action: Literal["confirm", "decline", "reschedule"]
    message: str | None = Field(None, max_length=1000)


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    scheduled_at: datetime
    location: str
    note: str | None = None
    status: str
    student_message: str | None = None
    created_at: datetime
    internship_title: str | None = None
    company_name: str | None = None
    student_name: str | None = None
