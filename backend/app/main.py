"""Điểm khởi động: tạo ứng dụng FastAPI và đăng ký router của các module."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine

# Import tất cả model để SQLAlchemy biết đủ các bảng và khóa ngoại
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.students import models as _student_models  # noqa: F401
from app.modules.internships import models as _internship_models  # noqa: F401
from app.modules.interviews import models as _interview_models  # noqa: F401

from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.internships.router import router as internships_router
from app.modules.interviews.router import router as interviews_router
from app.modules.students.router import router as students_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("internship_connect")

if "dev-only-secret" in settings.JWT_SECRET:
    log.warning("Đang dùng JWT_SECRET mặc định. Hãy đặt JWT_SECRET trong file .env.")

if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)  # bảng đã có thì bỏ qua

app = FastAPI(
    title="Internship Connect API",
    description="Hệ thống kết nối sinh viên với doanh nghiệp thực tập (M03, M13, M20, phỏng vấn, AI).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(internships_router)
app.include_router(interviews_router)
app.include_router(ai_router)


@app.get("/health", tags=["Hệ thống"])
def health():
    return {"status": "ok"}


# Phục vụ luôn giao diện web tại http://localhost:8000/app/ (cùng nguồn gốc nên không vướng CORS)
_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
