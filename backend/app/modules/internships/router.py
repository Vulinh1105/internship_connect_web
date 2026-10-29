from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.auth.models import User
from app.utils.pagination import Page, PageParams, make_page

from . import service
from .schemas import (
    ApplicantOut,
    ApplicationCreate,
    ApplicationOut,
    ApplicationStatusUpdate,
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    InternshipCreate,
    InternshipOut,
    InternshipStats,
    InternshipUpdate,
    MyApplicationOut,
)

router = APIRouter(tags=["M13 - Doanh nghiệp & thực tập"])

_company_only = require_role("company")
_student_only = require_role("student")
_staff_admin = require_role("staff", "admin")


# ======================= Doanh nghiệp =======================
@router.post("/api/companies", response_model=CompanyOut, status_code=201)
def create_company(data: CompanyCreate, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.create_company(db, user, data)


@router.get("/api/companies", response_model=Page[CompanyOut])
def list_companies(params: PageParams = Depends(), db: Session = Depends(get_db)):
    rows, total = service.list_companies(db, params)
    return make_page([CompanyOut.model_validate(r) for r in rows], total, params)


@router.get("/api/companies/me", response_model=CompanyOut)
def get_my_company(user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.require_company(db, user)


@router.put("/api/companies/me", response_model=CompanyOut)
def update_my_company(data: CompanyUpdate, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.update_company(db, user, data)


@router.get("/api/companies/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    return service.get_company(db, company_id)


# ======================= Tin thực tập =======================
@router.post("/api/internships", response_model=InternshipOut, status_code=201)
def create_internship(data: InternshipCreate, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.create_internship(db, user, data)


@router.get("/api/internships", response_model=Page[InternshipOut])
def list_internships(
    q: str | None = Query(None, max_length=100, description="Tìm theo tên vị trí, mô tả, yêu cầu, tên công ty"),
    location: str | None = Query(None, max_length=100),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    rows, total = service.list_internships(db, params, q, location)
    return make_page([InternshipOut.model_validate(r) for r in rows], total, params)


# "/mine" và "/stats" phải đặt TRƯỚC "/{internship_id}"
@router.get("/api/internships/mine", response_model=Page[InternshipOut])
def list_my_internships(
    params: PageParams = Depends(), user: User = Depends(_company_only), db: Session = Depends(get_db)
):
    rows, total = service.list_my_internships(db, user, params)
    return make_page([InternshipOut.model_validate(r) for r in rows], total, params)


@router.get("/api/internships/stats", response_model=InternshipStats)
def internship_stats(_user: User = Depends(_staff_admin), db: Session = Depends(get_db)):
    return service.get_stats(db)


@router.get("/api/internships/{internship_id}", response_model=InternshipOut)
def get_internship(internship_id: int, db: Session = Depends(get_db)):
    return service.get_internship(db, internship_id)


@router.put("/api/internships/{internship_id}", response_model=InternshipOut)
def update_internship(
    internship_id: int, data: InternshipUpdate, user: User = Depends(_company_only), db: Session = Depends(get_db)
):
    return service.update_internship(db, user, internship_id, data)


@router.post("/api/internships/{internship_id}/close", response_model=InternshipOut)
def close_internship(internship_id: int, user: User = Depends(_company_only), db: Session = Depends(get_db)):
    return service.close_internship(db, user, internship_id)


# ======================= Ứng tuyển =======================
@router.post("/api/internships/{internship_id}/applications", response_model=ApplicationOut, status_code=201)
def apply_for_internship(
    internship_id: int, data: ApplicationCreate, user: User = Depends(_student_only), db: Session = Depends(get_db)
):
    return service.apply(db, user, internship_id, data)


@router.get("/api/internships/{internship_id}/applications", response_model=Page[ApplicantOut])
def list_applicants(
    internship_id: int,
    status: str | None = Query(None, pattern="^(pending|reviewing|accepted|rejected|withdrawn)$"),
    params: PageParams = Depends(),
    user: User = Depends(require_role("company", "staff", "admin")),
    db: Session = Depends(get_db),
):
    items, total = service.list_applicants(db, user, internship_id, params, status)
    return make_page(items, total, params)


@router.get("/api/applications/me", response_model=Page[MyApplicationOut])
def list_my_applications(
    params: PageParams = Depends(), user: User = Depends(_student_only), db: Session = Depends(get_db)
):
    rows, total = service.list_my_applications(db, user, params)
    return make_page([MyApplicationOut.model_validate(r) for r in rows], total, params)


@router.get("/api/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.view_application(db, user, application_id)


@router.patch("/api/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    user: User = Depends(_company_only),
    db: Session = Depends(get_db),
):
    return service.update_status(db, user, application_id, data.status)


@router.post("/api/applications/{application_id}/withdraw", response_model=ApplicationOut)
def withdraw_application(application_id: int, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    return service.withdraw(db, user, application_id)


@router.get("/api/applications/{application_id}/cv")
def download_application_cv(application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    path, filename = service.get_application_cv_path(db, user, application_id)
    return FileResponse(path, filename=filename)
