import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

from .models import User
from .schemas import RegisterRequest, VerifyResponse


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(409, "Email đã được đăng ký")
    user = User(email=data.email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email đã được đăng ký")
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> tuple[str, User]:
    user = get_user_by_email(db, email)
    # Cùng một thông báo cho "sai email" và "sai mật khẩu" để không lộ email nào đã tồn tại
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    if not user.is_active:
        raise HTTPException(403, "Tài khoản đã bị khóa")
    return create_access_token(user.id, user.role), user


def verify_token(db: Session, token: str) -> VerifyResponse:
    try:
        payload = decode_access_token(token)
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        return VerifyResponse(valid=False)
    if user is None or not user.is_active:
        return VerifyResponse(valid=False)
    return VerifyResponse(valid=True, user_id=user.id, role=user.role)


def set_active(db: Session, user_id: int, is_active: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
