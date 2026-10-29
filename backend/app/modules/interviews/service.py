from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.internships import service as internships_service
from app.modules.internships.models import Application, Internship
from app.modules.students import service as students_service
from app.utils.pagination import PageParams, paginate

from .models import Interview
from .schemas import InterviewCreate, InterviewOut, InterviewRespond, InterviewUpdate


def _naive(dt: datetime) -> datetime:
    """Bỏ thông tin múi giờ nếu có (giữ nguyên giờ người dùng nhập)."""
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def _assert_future(dt: datetime) -> datetime:
    dt = _naive(dt)
    if dt <= datetime.now():  # so với giờ máy chủ
        raise HTTPException(400, "Thời gian phỏng vấn phải ở tương lai")
    return dt


def to_out(db: Session, interview: Interview) -> InterviewOut:
    application = interview.application
    student = students_service.get_student_by_id(db, application.student_id)
    out = InterviewOut.model_validate(interview)
    out.internship_title = application.internship_title
    out.company_name = application.company_name
    out.student_name = student.full_name if student else None
    return out


def _get_interview(db: Session, interview_id: int) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(404, "Không tìm thấy lịch phỏng vấn")
    return interview


def _company_interview(db: Session, user: User, interview_id: int) -> Interview:
    interview = _get_interview(db, interview_id)
    # Kiểm tra lịch này thuộc doanh nghiệp đang đăng nhập
    internships_service.get_application_for_company(db, user, interview.application_id)
    return interview


def create_interview(db: Session, user: User, data: InterviewCreate) -> Interview:
    application = internships_service.get_application_for_company(db, user, data.application_id)
    if application.status in ("rejected", "withdrawn"):
        raise HTTPException(409, f"Không thể mời phỏng vấn hồ sơ đang ở trạng thái '{application.status}'")
    scheduled = _assert_future(data.scheduled_at)

    interview = Interview(
        application_id=application.id,
        scheduled_at=scheduled,
        location=data.location,
        note=data.note,
        status="invited",
    )
    if application.status == "pending":
        application.status = "reviewing"  # mời phỏng vấn nghĩa là đã bắt đầu xem xét
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def update_interview(db: Session, user: User, interview_id: int, data: InterviewUpdate) -> Interview:
    interview = _company_interview(db, user, interview_id)
    if interview.status == "cancelled":
        raise HTTPException(409, "Lịch này đã bị hủy")
    values = data.model_dump(exclude_unset=True)
    if "scheduled_at" in values:
        if values["scheduled_at"] is None:
            raise HTTPException(400, "scheduled_at không hợp lệ")
        values["scheduled_at"] = _assert_future(values["scheduled_at"])
    if "location" in values and not values["location"]:
        raise HTTPException(400, "location không được để trống")
    for key, value in values.items():
        setattr(interview, key, value)
    # Doanh nghiệp đổi lịch thì sinh viên phải xác nhận lại
    interview.status = "invited"
    interview.student_message = None
    db.commit()
    db.refresh(interview)
    return interview


def cancel_interview(db: Session, user: User, interview_id: int) -> Interview:
    interview = _company_interview(db, user, interview_id)
    interview.status = "cancelled"
    db.commit()
    db.refresh(interview)
    return interview


def respond(db: Session, user: User, interview_id: int, data: InterviewRespond) -> Interview:
    student = students_service.require_student_profile(db, user)
    interview = _get_interview(db, interview_id)
    if interview.application.student_id != student.id:
        raise HTTPException(403, "Đây không phải lịch phỏng vấn của bạn")
    if interview.status != "invited":
        raise HTTPException(409, f"Không thể phản hồi lịch đang ở trạng thái '{interview.status}'")

    new_status = {"confirm": "confirmed", "decline": "declined", "reschedule": "reschedule_requested"}[data.action]
    if data.action == "reschedule" and not (data.message and data.message.strip()):
        raise HTTPException(400, "Hãy ghi rõ thời gian bạn muốn đổi sang trong phần message")
    interview.status = new_status
    interview.student_message = data.message
    db.commit()
    db.refresh(interview)
    return interview


def list_mine(db: Session, user: User, params: PageParams):
    stmt = select(Interview).join(Application, Interview.application_id == Application.id)
    if user.role == "student":
        student = students_service.require_student_profile(db, user)
        stmt = stmt.where(Application.student_id == student.id)
    elif user.role == "company":
        company = internships_service.require_company(db, user)
        stmt = stmt.join(Internship, Application.internship_id == Internship.id).where(
            Internship.company_id == company.id
        )
    # staff và admin xem tất cả
    rows, total = paginate(db, stmt, params, order_by=[Interview.scheduled_at.desc()])
    return [to_out(db, r) for r in rows], total
