from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.auth.models import User

from . import service
from .schemas import CVOut, SkillCreate, SkillOut, StudentOut, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["M03 - Sinh viên"])


@router.get("")
def list_students(user: User = Depends(require_role("staff", "admin")),
                  db: Session = Depends(get_db),
                  page: int = 1, page_size: int = 20):
    from app.utils.pagination import PageParams, make_page
    from .repository import list_students as list_records
    from .schemas import StudentOut
    from fastapi import HTTPException
    if page < 1 or not 1 <= page_size <= 100:
        raise HTTPException(422, "Phân trang không hợp lệ")
    params = PageParams(page=page, page_size=page_size)
    rows, total = list_records(db, params)
    return make_page([StudentOut.model_validate(s) for s in rows], total, params)

_student_only = require_role("student")


def _load_for_view(db: Session, user: User, student_id: int):
    """Sinh viên chỉ xem được hồ sơ của mình. staff và admin xem được tất cả."""
    student = service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ sinh viên")
    if user.role in ("staff", "admin") or student.user_id == user.id:
        return student
    raise HTTPException(403, "Bạn không có quyền xem hồ sơ này")


# Các route "/me" phải đặt TRƯỚC route "/{student_id}"
@router.get("/me", response_model=StudentOut)
def get_my_profile(user: User = Depends(_student_only), db: Session = Depends(get_db)):
    return service.require_student_profile(db, user)


@router.put("/me", response_model=StudentOut)
def update_my_profile(data: StudentUpdate, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    """Tạo hồ sơ nếu chưa có, cập nhật nếu đã có."""
    return service.upsert_profile(db, user, data)


@router.post("/me/skills", response_model=SkillOut, status_code=201)
def add_my_skill(data: SkillCreate, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    student = service.require_student_profile(db, user)
    return service.add_skill(db, student, data.skill_name)


@router.delete("/me/skills/{skill_id}", status_code=204)
def delete_my_skill(skill_id: int, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    student = service.require_student_profile(db, user)
    service.remove_skill(db, student, skill_id)


@router.get("/me/cvs", response_model=list[CVOut])
def list_my_cvs(user: User = Depends(_student_only), db: Session = Depends(get_db)):
    student = service.require_student_profile(db, user)
    return service.list_cvs(db, student)


@router.post("/me/cvs", response_model=CVOut, status_code=201)
def upload_my_cv(file: UploadFile = File(...), user: User = Depends(_student_only), db: Session = Depends(get_db)):
    student = service.require_student_profile(db, user)
    return service.add_cv(db, student, file)


@router.put("/me/cvs/{cv_id}/primary", response_model=CVOut)
def set_primary_cv(cv_id: int, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    student = service.require_student_profile(db, user)
    return service.set_primary_cv(db, student, cv_id)


@router.get("/me/cvs/{cv_id}/download")
def download_my_cv(cv_id: int, user: User = Depends(_student_only), db: Session = Depends(get_db)):
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    student = service.require_student_profile(db, user)
    cv = service.get_cv(db, cv_id)
    if cv is None or cv.student_id != student.id:
        raise HTTPException(404, "Không tìm thấy CV")
    if not Path(cv.file_path).is_file():
        raise HTTPException(404, "File CV không còn trên máy chủ")
    return FileResponse(cv.file_path, filename=cv.file_name)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _load_for_view(db, user, student_id)


@router.get("/{student_id}/skills", response_model=list[SkillOut])
def get_student_skills(student_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _load_for_view(db, user, student_id).skills
