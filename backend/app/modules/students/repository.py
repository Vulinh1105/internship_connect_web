from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Student, StudentCV
from app.utils.pagination import paginate


def list_students(db, params):
    return paginate(db, select(Student), params, order_by=[Student.id])


def get_student_by_user_id(db: Session, user_id: int) -> Student | None:
    return db.scalar(select(Student).where(Student.user_id == user_id))


def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def get_cv(db: Session, cv_id: int) -> StudentCV | None:
    return db.get(StudentCV, cv_id)


def list_cvs(db: Session, student: Student) -> list[StudentCV]:
    return list(db.scalars(select(StudentCV).where(StudentCV.student_id == student.id).order_by(StudentCV.id)))
