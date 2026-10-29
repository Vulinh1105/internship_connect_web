import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 255 or not _EMAIL_RE.match(value):
        raise ValueError("Email không hợp lệ")
    return value


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    # Chỉ cho tự đăng ký 2 vai trò này. staff và admin do quản trị tạo.
    role: Literal["student", "company"]

    check_email = field_validator("email")(_clean_email)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    check_email = field_validator("email")(_clean_email)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    valid: bool
    user_id: int | None = None
    role: str | None = None


class ActiveUpdate(BaseModel):
    is_active: bool
