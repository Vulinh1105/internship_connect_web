from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.utils.pagination import Page, PageParams, make_page, paginate

from . import service
from .models import User
from .schemas import (
    ActiveUpdate,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    VerifyRequest,
    VerifyResponse,
)

router = APIRouter(prefix="/api/auth", tags=["M20 - Tài khoản & phân quyền"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return service.register(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token, user = service.login(db, data.email, data.password)
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/verify", response_model=VerifyResponse)
def verify(data: VerifyRequest, db: Session = Depends(get_db)):
    """API nội bộ tùy chọn: kiểm tra một token còn hiệu lực không."""
    return service.verify_token(db, data.token)


@router.get("/users", response_model=Page[UserOut])
def list_users(
    params: PageParams = Depends(),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows, total = paginate(db, select(User), params, order_by=[User.id])
    return make_page([UserOut.model_validate(r) for r in rows], total, params)


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_user_active(
    user_id: int,
    data: ActiveUpdate,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return service.set_active(db, user_id, data.is_active)
