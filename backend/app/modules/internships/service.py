"""Logic nghiệp vụ M13: doanh nghiệp, tin thực tập, ứng tuyển, xét duyệt."""
import os
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager

from app.modules.auth.models import User
from app.modules.students import service as students_service
from app.utils.pagination import PageParams, paginate

from .models import APPLICATION_STATUSES, Application, Company, Internship
from .schemas import (
    ApplicantOut,
    ApplicationCreate,
    ApplicationOut,
    CompanyCreate,
    CompanyUpdate,
    InternshipCreate,
    InternshipStats,
    InternshipUpdate,
)

# Trạng thái hiện tại -> các trạng thái được phép chuyển tới
STATUS_TRANSITIONS = {
    "pending": {"reviewing", "accepted", "rejected"},
    "reviewing": {"accepted", "rejected"},
}


# ======================= Doanh nghiệp =======================
def get_company_by_user_id(db: Session, user_id: int) -> Company | None:
    return db.scalar(select(Company).where(Company.user_id == user_id))


def require_company(db: Session, user: User) -> Company:
    company = get_company_by_user_id(db, user.id)
    if company is None:
        raise HTTPException(404, "Bạn chưa tạo hồ sơ doanh nghiệp")
    return company


def create_company(db: Session, user: User, data: CompanyCreate) -> Company:
    if get_company_by_user_id(db, user.id):
        raise HTTPException(409, "Tài khoản này đã có hồ sơ doanh nghiệp")
    company = Company(user_id=user.id, **data.model_dump())
    db.add(company)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Tài khoản này đã có hồ sơ doanh nghiệp")
    db.refresh(company)
    return company


def update_company(db: Session, user: User, data: CompanyUpdate) -> Company:
    company = require_company(db, user)
    values = data.model_dump(exclude_unset=True)
    if "company_name" in values and not values["company_name"]:
        raise HTTPException(400, "company_name không được để trống")
    for key, value in values.items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


def get_company(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(404, "Không tìm thấy doanh nghiệp")
    return company


def list_companies(db: Session, params: PageParams):
    return paginate(db, select(Company), params, order_by=[Company.company_name])


# ======================= Tin thực tập =======================
def _is_open_now(internship: Internship) -> bool:
    if internship.status != "open":
        return False
    return internship.deadline is None or internship.deadline >= date.today()


def get_internship(db: Session, internship_id: int) -> Internship:
    internship = db.get(Internship, internship_id)
    if internship is None:
        raise HTTPException(404, "Không tìm thấy vị trí thực tập")
    return internship


def assert_can_manage(db: Session, user: User, internship: Internship) -> None:
    """staff và admin được xem; doanh nghiệp chỉ quản lý tin của chính mình."""
    if user.role in ("staff", "admin"):
        return
    company = get_company_by_user_id(db, user.id)
    if company is None or company.id != internship.company_id:
        raise HTTPException(403, "Vị trí này không thuộc doanh nghiệp của bạn")


def _assert_company_owns(db: Session, user: User, internship: Internship) -> None:
    company = require_company(db, user)
    if company.id != internship.company_id:
        raise HTTPException(403, "Vị trí này không thuộc doanh nghiệp của bạn")


def create_internship(db: Session, user: User, data: InternshipCreate) -> Internship:
    company = require_company(db, user)
    if data.deadline is not None and data.deadline < date.today():
        raise HTTPException(400, "Hạn ứng tuyển không được ở quá khứ")
    internship = Internship(company_id=company.id, **data.model_dump())
    db.add(internship)
    db.commit()
    db.refresh(internship)
    return internship


def update_internship(db: Session, user: User, internship_id: int, data: InternshipUpdate) -> Internship:
    internship = get_internship(db, internship_id)
    _assert_company_owns(db, user, internship)
    values = data.model_dump(exclude_unset=True)
    if "title" in values and not values["title"]:
        raise HTTPException(400, "title không được để trống")
    if "status" in values and values["status"] is None:
        raise HTTPException(400, "status không hợp lệ")
    for key, value in values.items():
        setattr(internship, key, value)
    db.commit()
    db.refresh(internship)
    return internship


def close_internship(db: Session, user: User, internship_id: int) -> Internship:
    internship = get_internship(db, internship_id)
    _assert_company_owns(db, user, internship)
    internship.status = "closed"
    db.commit()
    db.refresh(internship)
    return internship


def list_internships(db: Session, params: PageParams, q: str | None = None, location: str | None = None):
    """Danh sách công khai: chỉ tin đang mở và chưa quá hạn."""
    stmt = (
        select(Internship)
        .join(Company, Internship.company_id == Company.id)
        .where(
            Internship.status == "open",
            or_(Internship.deadline.is_(None), Internship.deadline >= date.today()),
        )
    )
    if q and q.strip():
        term = q.strip()
        stmt = stmt.where(
            or_(
                Internship.title.icontains(term, autoescape=True),
                Internship.description.icontains(term, autoescape=True),
                Internship.requirements.icontains(term, autoescape=True),
                Company.company_name.icontains(term, autoescape=True),
            )
        )
    if location and location.strip():
        stmt = stmt.where(Internship.location.icontains(location.strip(), autoescape=True))
    return paginate(
        db, stmt, params,
        order_by=[Internship.id.desc()],
        options=[contains_eager(Internship.company)],
    )


def list_my_internships(db: Session, user: User, params: PageParams):
    company = require_company(db, user)
    stmt = select(Internship).where(Internship.company_id == company.id)
    return paginate(db, stmt, params, order_by=[Internship.id.desc()])


def get_stats(db: Session) -> InternshipStats:
    total = db.scalar(select(func.count()).select_from(Internship)) or 0
    open_count = db.scalar(
        select(func.count()).select_from(Internship).where(
            Internship.status == "open",
            or_(Internship.deadline.is_(None), Internship.deadline >= date.today()),
        )
    ) or 0
    by_status = {s: 0 for s in APPLICATION_STATUSES}
    for status, count in db.execute(select(Application.status, func.count()).group_by(Application.status)):
        by_status[status] = count
    return InternshipStats(
        total_internships=total,
        open_internships=open_count,
        total_applications=sum(by_status.values()),
        applications_by_status=by_status,
    )


# ======================= Ứng tuyển =======================
def get_application(db: Session, application_id: int) -> Application:
    """Hàm cho module khác (interviews) dùng. Ném 404 nếu không có."""
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ ứng tuyển")
    return application


def get_application_for_company(db: Session, user: User, application_id: int) -> Application:
    """Lấy hồ sơ ứng tuyển, đảm bảo nó thuộc tin của doanh nghiệp đang đăng nhập."""
    application = get_application(db, application_id)
    company = get_company_by_user_id(db, user.id)
    if company is None or application.internship.company_id != company.id:
        raise HTTPException(403, "Hồ sơ này không thuộc doanh nghiệp của bạn")
    return application


def apply(db: Session, user: User, internship_id: int, data: ApplicationCreate) -> Application:
    # Danh tính lấy từ JWT, không nhận student_id từ client
    student = students_service.get_student_by_user_id(db, user.id)
    if student is None:
        raise HTTPException(400, "Hãy tạo hồ sơ sinh viên trước khi ứng tuyển")

    internship = get_internship(db, internship_id)
    if not _is_open_now(internship):
        raise HTTPException(400, "Vị trí này đã đóng hoặc đã hết hạn ứng tuyển")

    if data.cv_id is not None:
        cv = students_service.get_cv(db, data.cv_id)
        if cv is None or cv.student_id != student.id:
            raise HTTPException(400, "CV không hợp lệ")

    duplicate = db.scalar(
        select(Application.id).where(
            Application.internship_id == internship_id, Application.student_id == student.id
        )
    )
    if duplicate:
        raise HTTPException(409, "Bạn đã ứng tuyển vào vị trí này rồi")

    application = Application(
        internship_id=internship_id,
        student_id=student.id,
        cv_id=data.cv_id,
        cover_letter=data.cover_letter,
        status="pending",
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError:  # hai yêu cầu cùng lúc: ràng buộc UNIQUE của DB chặn lại
        db.rollback()
        raise HTTPException(409, "Bạn đã ứng tuyển vào vị trí này rồi")
    db.refresh(application)
    return application


def list_my_applications(db: Session, user: User, params: PageParams):
    student = students_service.require_student_profile(db, user)
    stmt = select(Application).where(Application.student_id == student.id)
    return paginate(db, stmt, params, order_by=[Application.id.desc()])


def list_applicants(
    db: Session, user: User, internship_id: int, params: PageParams, status: str | None = None
):
    internship = get_internship(db, internship_id)
    assert_can_manage(db, user, internship)
    stmt = select(Application).where(Application.internship_id == internship_id)
    if status:
        stmt = stmt.where(Application.status == status)
    rows, total = paginate(db, stmt, params, order_by=[Application.id])
    items = []
    for app in rows:
        student = students_service.get_student_by_id(db, app.student_id)
        summary = students_service.build_summary(student) if student else None
        items.append(ApplicantOut(**ApplicationOut.model_validate(app).model_dump(), student=summary))
    return items, total


def _assert_can_view_application(db: Session, user: User, application: Application) -> None:
    if user.role in ("staff", "admin"):
        return
    if user.role == "student":
        student = students_service.get_student_by_user_id(db, user.id)
        if student and student.id == application.student_id:
            return
    elif user.role == "company":
        company = get_company_by_user_id(db, user.id)
        if company and company.id == application.internship.company_id:
            return
    raise HTTPException(403, "Bạn không có quyền xem hồ sơ ứng tuyển này")


def view_application(db: Session, user: User, application_id: int) -> Application:
    application = get_application(db, application_id)
    _assert_can_view_application(db, user, application)
    return application


def update_status(db: Session, user: User, application_id: int, new_status: str) -> Application:
    application = get_application_for_company(db, user, application_id)
    allowed = STATUS_TRANSITIONS.get(application.status, set())
    if new_status not in allowed:
        raise HTTPException(
            409, f"Không thể chuyển từ '{application.status}' sang '{new_status}'"
        )
    application.status = new_status
    db.commit()
    db.refresh(application)
    return application


def withdraw(db: Session, user: User, application_id: int) -> Application:
    student = students_service.require_student_profile(db, user)
    application = get_application(db, application_id)
    if application.student_id != student.id:
        raise HTTPException(403, "Đây không phải hồ sơ của bạn")
    if application.status not in ("pending", "reviewing"):
        raise HTTPException(409, f"Không thể rút hồ sơ ở trạng thái '{application.status}'")
    application.status = "withdrawn"
    db.commit()
    db.refresh(application)
    return application


def get_application_cv_path(db: Session, user: User, application_id: int) -> tuple[str, str]:
    """Trả về (đường dẫn file, tên file) của CV đính kèm đơn ứng tuyển."""
    application = view_application(db, user, application_id)
    if application.cv_id is None:
        raise HTTPException(404, "Đơn ứng tuyển này không đính kèm CV")
    cv = students_service.get_cv(db, application.cv_id)
    if cv is None or not os.path.isfile(cv.file_path):
        raise HTTPException(404, "Không tìm thấy file CV")
    return cv.file_path, cv.file_name
