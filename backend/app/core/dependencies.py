"""Các dependency dùng chung: lấy người dùng hiện tại và kiểm tra vai trò."""
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.models import User

from .database import get_db
from .security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(401, "Chưa đăng nhập", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn", headers={"WWW-Authenticate": "Bearer"})

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


def require_role(*roles: str):
    """Dùng: user = Depends(require_role("student")). Vai trò lấy từ DB, không tin dữ liệu client gửi."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Bạn không có quyền thực hiện thao tác này")
        return user

    return checker
