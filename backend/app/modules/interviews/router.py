from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.auth.models import User
from app.utils.pagination import Page, PageParams, make_page

from . import service
from .schemas import InterviewCreate, InterviewOut, InterviewRespond, InterviewUpdate

router = APIRouter(prefix="/api/interviews", tags=["Lịch phỏng vấn"])

_company_only = require_role("company")
_student_only = require_role("student")


@router.post("", response_model=InterviewOut, status_code=201)
def create_interview(data: InterviewCreate, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.to_out(db, service.create_interview(db, user, data))


@router.get("/me", response_model=Page[InterviewOut])
def list_my_interviews(
    params: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    items, total = service.list_mine(db, user, params)
    return make_page(items, total, params)


@router.patch("/{interview_id}", response_model=InterviewOut)
def update_interview(
    interview_id: int, data: InterviewUpdate, user: User = Depends(_company_only), db: Session = Depends(get_db)
):
    return service.to_out(db, service.update_interview(db, user, interview_id, data))


@router.post("/{interview_id}/cancel", response_model=InterviewOut)
def cancel_interview(interview_id: int, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.to_out(db, service.cancel_interview(db, user, interview_id))


@router.post("/{interview_id}/respond", response_model=InterviewOut)
def respond_to_interview(
    interview_id: int, data: InterviewRespond, user: User = Depends(_student_only), db: Session = Depends(get_db)
):
    return service.to_out(db, service.respond(db, user, interview_id, data))
