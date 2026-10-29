"""Logic quản lý hồ sơ sinh viên. Các module khác (M13, interviews, ai) gọi các hàm ở đây
thay vì tự truy vấn bảng students."""
import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User

from .models import Student, StudentCV, StudentSkill
from .schemas import StudentSummary, StudentUpdate

ALLOWED_CV_EXT = {".pdf", ".doc", ".docx"}
MAX_CV_BYTES = 5 * 1024 * 1024


# ---------- Hàm cho module khác dùng ----------
def get_student_by_user_id(db: Session, user_id: int) -> Student | None:
    return db.scalar(select(Student).where(Student.user_id == user_id))


def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def get_cv(db: Session, cv_id: int) -> StudentCV | None:
    return db.get(StudentCV, cv_id)


def build_summary(student: Student) -> StudentSummary:
    return StudentSummary(
        id=student.id,
        student_code=student.student_code,
        full_name=student.full_name,
        major=student.major,
        gpa=student.gpa,
        phone=student.phone,
        profile_summary=student.profile_summary,
        skills=[s.skill_name for s in student.skills],
    )


# ---------- Hồ sơ ----------
def require_student_profile(db: Session, user: User) -> Student:
    student = get_student_by_user_id(db, user.id)
    if student is None:
        raise HTTPException(404, "Bạn chưa tạo hồ sơ sinh viên")
    return student


def upsert_profile(db: Session, user: User, data: StudentUpdate) -> Student:
    values = data.model_dump(exclude_unset=True)
    if "full_name" in values and not values["full_name"]:
        raise HTTPException(400, "full_name không được để trống")

    student = get_student_by_user_id(db, user.id)
    if student is None:
        if not values.get("full_name"):
            raise HTTPException(400, "Cần có full_name khi tạo hồ sơ lần đầu")
        student = Student(user_id=user.id)
        db.add(student)

    code = values.get("student_code")
    if code:
        other = db.scalar(
            select(Student).where(Student.student_code == code, Student.id != (student.id or 0))
        )
        if other:
            db.rollback()
            raise HTTPException(409, "Mã sinh viên đã được sử dụng")

    for key, value in values.items():
        setattr(student, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã sinh viên đã được sử dụng")
    db.refresh(student)
    return student


# ---------- Kỹ năng ----------
def add_skill(db: Session, student: Student, skill_name: str) -> StudentSkill:
    name = " ".join(skill_name.split())
    if not name:
        raise HTTPException(400, "Tên kỹ năng không được để trống")
    exists = db.scalar(
        select(StudentSkill).where(
            StudentSkill.student_id == student.id,
            func.lower(StudentSkill.skill_name) == name.lower(),
        )
    )
    if exists:
        raise HTTPException(409, "Kỹ năng này đã có trong hồ sơ")
    skill = StudentSkill(student_id=student.id, skill_name=name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def remove_skill(db: Session, student: Student, skill_id: int) -> None:
    skill = db.get(StudentSkill, skill_id)
    if skill is None or skill.student_id != student.id:
        raise HTTPException(404, "Không tìm thấy kỹ năng")
    db.delete(skill)
    db.commit()


# ---------- CV ----------
def list_cvs(db: Session, student: Student) -> list[StudentCV]:
    return list(db.scalars(select(StudentCV).where(StudentCV.student_id == student.id).order_by(StudentCV.id)))


def add_cv(db: Session, student: Student, upload: UploadFile) -> StudentCV:
    original = os.path.basename(upload.filename or "")
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_CV_EXT:
        raise HTTPException(400, "Chỉ nhận file PDF, DOC hoặc DOCX")
    content = upload.file.read(MAX_CV_BYTES + 1)
    if not content:
        raise HTTPException(400, "File rỗng")
    if len(content) > MAX_CV_BYTES:
        raise HTTPException(413, "File quá lớn (tối đa 5MB)")

    folder = Path(settings.UPLOAD_DIR) / "cvs"
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid4().hex}{ext}"  # tên do server đặt, không dùng tên người dùng gửi
    stored_path.write_bytes(content)

    has_primary = db.scalar(
        select(StudentCV.id).where(StudentCV.student_id == student.id, StudentCV.is_primary.is_(True))
    )
    cv = StudentCV(
        student_id=student.id,
        file_name=original[:255] or f"cv{ext}",
        file_path=str(stored_path),
        is_primary=has_primary is None,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def set_primary_cv(db: Session, student: Student, cv_id: int) -> StudentCV:
    cv = db.get(StudentCV, cv_id)
    if cv is None or cv.student_id != student.id:
        raise HTTPException(404, "Không tìm thấy CV")
    for other in list_cvs(db, student):
        other.is_primary = other.id == cv.id
    db.commit()
    db.refresh(cv)
    return cv
