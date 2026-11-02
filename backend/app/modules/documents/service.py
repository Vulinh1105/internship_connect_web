"""Managed, public knowledge documents; student CVs stay in students module."""
from fastapi import HTTPException
from .models import Document
from .repository import DocumentRepository
from . import storage


def upload(db, user, file):
    name, path, size = storage.save_upload(file)
    try:
        return DocumentRepository(db).save(Document(
            owner_id=user.id, original_filename=name, file_path=path,
            size=size, status="pending", access_level="public"))
    except Exception:
        storage.remove(path)
        raise


def get(db, document_id):
    document = DocumentRepository(db).get_by_id(document_id)
    if document is None:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return document


def index(db, document_id):
    from app.core.config import settings
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "Chưa cấu hình OPENAI_API_KEY trong file .env")
    from app.modules.ai.rag.ingestion.pipeline import run_pipeline_for_document
    from app.modules.ai.rag.service import reset_index
    document = get(db, document_id)
    result = run_pipeline_for_document(document_id, db)
    document.status = result.status.value
    DocumentRepository(db).save(document)
    reset_index()
    return result.to_dict()


def reindex_knowledge(db):
    return [index(db, d.id) for d in DocumentRepository(db).list_all()]


def delete(db, document_id):
    from app.modules.ai.rag.retrieval.qdrant_store import delete_chunks_by_document
    from app.modules.ai.rag.service import reset_index
    document = get(db, document_id)
    # Pending uploads have no points. Deleting them must not require Qdrant.
    if document.status != "pending":
        delete_chunks_by_document(document_id)
    storage.remove(document.file_path)
    db.delete(document)
    db.commit()
    reset_index()
