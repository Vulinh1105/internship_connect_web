from fastapi import APIRouter, Depends, File, UploadFile, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role
from . import service
from .repository import DocumentRepository
from .schemas import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["Tài liệu kiến thức"],
                   dependencies=[Depends(require_role("staff", "admin"))])


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return DocumentRepository(db).list_all()


@router.post("", response_model=DocumentOut, status_code=201)
def upload(file: UploadFile = File(...), user=Depends(require_role("staff", "admin")),
           db: Session = Depends(get_db)):
    return service.upload(db, user, file)


@router.get("/{document_id}", response_model=DocumentOut)
def detail(document_id: int, db: Session = Depends(get_db)):
    return service.get(db, document_id)


@router.get("/{document_id}/download")
def download(document_id: int, db: Session = Depends(get_db)):
    from pathlib import Path
    from fastapi import HTTPException
    document = service.get(db, document_id)
    if not Path(document.file_path).is_file():
        raise HTTPException(404, "File tài liệu không còn trên máy chủ")
    return FileResponse(document.file_path, filename=document.original_filename)


@router.post("/{document_id}/index")
def index(document_id: int, db: Session = Depends(get_db)):
    return service.index(db, document_id)


@router.delete("/{document_id}", status_code=204)
def delete(document_id: int, db: Session = Depends(get_db)):
    service.delete(db, document_id)
    return Response(status_code=204)
