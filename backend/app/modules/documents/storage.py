from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from app.core.config import settings

MAX_SIZE = 10 * 1024 * 1024


def save_upload(upload):
    name = Path(upload.filename or "").name
    if Path(name).suffix.lower() not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(400, "Chỉ hỗ trợ PDF, DOCX, TXT")
    content = upload.file.read(MAX_SIZE + 1)
    if not content or len(content) > MAX_SIZE:
        raise HTTPException(400, "Tài liệu phải có nội dung và không quá 10 MB")
    folder = Path(settings.UPLOAD_DIR).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (uuid4().hex + Path(name).suffix.lower())
    path.write_bytes(content)
    return name, str(path), len(content)


def remove(path):
    target = Path(path).resolve()
    if not target.is_relative_to(Path(settings.UPLOAD_DIR).resolve()):
        raise HTTPException(400, "Đường dẫn lưu trữ không hợp lệ")
    target.unlink(missing_ok=True)
