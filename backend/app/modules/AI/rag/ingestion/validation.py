"""
doc_processing.ingestion
=========================
Táº§ng "ingestion" - Ä‘á»©ng giá»¯a chá»©c nÄƒng upload file ÄÃƒ CÃ“ Sáº´N
(app/api/v1/endpoints/document.py + app/services/document_service.py, do G4
triá»ƒn khai) vÃ  táº§ng parsing/chunking cá»§a G2.

TrÃ¡ch nhiá»‡m (á»©ng vá»›i pháº§n "validate" cá»§a T06 vÃ  bÆ°á»›c Ä‘áº§u vÃ o cá»§a pipeline T11):
    1. Láº¥y record `Document` tá»« DB - TÃI Sá»¬ Dá»¤NG DocumentRepository cá»§a G4
       (KHÃ”NG viáº¿t láº¡i query riÃªng) Ä‘á»ƒ chá»‰ cÃ³ 1 cÃ¡ch duy nháº¥t Ä‘á»c Document
       trong toÃ n há»‡ thá»‘ng, trÃ¡nh 2 nhÃ³m code lá»‡ch nhau.
    2. Validate file trÃªn Ä‘Ä©a: tá»“n táº¡i, Ä‘Ãºng Ä‘á»‹nh dáº¡ng há»— trá»£, khÃ´ng rá»—ng.
    3. Gá»i parsing.parse_document_model() Ä‘á»ƒ láº¥y parsed blocks.
    4. NÃ©m lá»—i rÃµ rÃ ng, cÃ³ ngá»¯ cáº£nh (document_id, filename) Ä‘á»ƒ pipeline.py
       ghi log/status chÃ­nh xÃ¡c thay vÃ¬ Ä‘á»ƒ lá»™ stacktrace chung chung ra ngoÃ i.

Module nÃ y KHÃ”NG phá»¥ thuá»™c FastAPI (khÃ´ng import Request/HTTPException) Ä‘á»ƒ
cÃ³ thá»ƒ tÃ¡i sá»­ dá»¥ng á»Ÿ script CLI, cron job hoáº·c test Ä‘á»™c láº­p, khÃ´ng chá»‰ trong
1 request HTTP.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

# ThÃªm thÆ° má»¥c `backend` vÃ o sys.path khi cháº¡y script trá»±c tiáº¿p (python backend/app/doc_processing/ingestion.py)
if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.ai.rag.ingestion.parsing import (
    SUPPORTED_EXTENSIONS,
    ParsingError,
    UnsupportedFileTypeError,
    parse_document,
)

logger = logging.getLogger(__name__)


class DocumentRecord(Protocol):
    id: int
    owner_id: int
    file_path: str
    original_filename: str


class IngestionError(Exception):
    """Lá»—i táº§ng ingestion - lá»—i nghiá»‡p vá»¥ xáº£y ra TRÆ¯á»šC khi parse (khÃ´ng tÃ¬m
    tháº¥y document, file rá»—ng, file váº­t lÃ½ bá»‹ thiáº¿u...)."""


class DocumentNotFoundError(IngestionError):
    """KhÃ´ng tÃ¬m tháº¥y Document trong DB vá»›i id tÆ°Æ¡ng á»©ng."""


class DocumentFileMissingError(IngestionError):
    """Record Document tá»“n táº¡i trong DB nhÆ°ng file váº­t lÃ½ trÃªn Ä‘Ä©a bá»‹ thiáº¿u
    (Ä‘Ã£ bá»‹ xoÃ¡ thá»§ cÃ´ng, lá»—i storage, Ä‘á»“ng bá»™ cháº­m giá»¯a nhiá»u instance...)."""


class EmptyDocumentError(IngestionError):
    """Parse thÃ nh cÃ´ng vá» máº·t ká»¹ thuáº­t nhÆ°ng khÃ´ng trÃ­ch Ä‘Æ°á»£c báº¥t ká»³ Ä‘oáº¡n
    text nÃ o (file trá»‘ng, hoáº·c PDF toÃ n trang scan/áº£nh khÃ´ng cÃ³ text layer -
    cáº§n OCR, ngoÃ i pháº¡m vi MVP theo Kick-off Guide)."""


# ---------------------------------------------------------------------------
# BÆ°á»›c 1: láº¥y Document tá»« DB
# ---------------------------------------------------------------------------

def get_document_or_raise(document_id: int, db: Session) -> DocumentRecord:
    """Láº¥y Document theo id, tÃ¡i sá»­ dá»¥ng DocumentRepository
    (app/repository/document_repository.py) mÃ  G4 Ä‘Ã£ viáº¿t cho endpoint
    upload, thay vÃ¬ tá»± viáº¿t `select(Document)...` riÃªng á»Ÿ Ä‘Ã¢y."""
    try:
        from app.modules.documents.repository import DocumentRepository
    except ImportError as exc:
        raise IngestionError(
            "RAG document ingestion requires app.modules.documents.repository; "
            "wire this function to the document repository used by the backend."
        ) from exc

    repo = DocumentRepository(db)
    document = repo.get_by_id(document_id)
    if document is None:
        raise DocumentNotFoundError(f"KhÃ´ng tÃ¬m tháº¥y tÃ i liá»‡u vá»›i document_id={document_id} trong DB.")
    return document


# ---------------------------------------------------------------------------
# BÆ°á»›c 2: validate file trÃªn Ä‘Ä©a TRÆ¯á»šC khi Ä‘Æ°a vÃ o parser
# ---------------------------------------------------------------------------

def validate_document_file(document: DocumentRecord) -> Path:
    """Kiá»ƒm tra file váº­t lÃ½ há»£p lá»‡ trÆ°á»›c khi gá»i parser, trÃ¡nh Ä‘á»ƒ lá»—i xáº£y ra
    sÃ¢u bÃªn trong PyMuPDF/python-docx vá»›i thÃ´ng bÃ¡o khÃ³ hiá»ƒu cho ngÆ°á»i debug.

    Tráº£ vá» Path Ä‘Ã£ kiá»ƒm tra há»£p lá»‡, sáºµn sÃ ng truyá»n cho parsing.parse_document().
    """
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    storage_path = upload_dir / str(document.owner_id) / str(document.id)
    paths_to_try = [storage_path]
    stored_file_path = getattr(document, "file_path", None)
    if isinstance(stored_file_path, str) and stored_file_path:
        file_path = Path(stored_file_path)
        if not file_path.is_absolute():
            file_path = upload_dir / file_path
        file_path = file_path.resolve()
        if file_path != storage_path:
            paths_to_try.append(file_path)

    resolved_path = next((path for path in paths_to_try if path.is_file()), None)
    if resolved_path is None:
        for path in paths_to_try:
            legacy_path = path.with_suffix(Path(document.original_filename).suffix.lower())
            if legacy_path.is_file():
                resolved_path = legacy_path
                break
            candidates = list(path.parent.glob(f"{path.name}.*"))
            if len(candidates) == 1:
                resolved_path = candidates[0]
                break

    if resolved_path is None:
        raise DocumentFileMissingError(
            f"Document id={document.id} ('{document.original_filename}') cÃ³ record "
            f"trong DB nhÆ°ng KHÃ”NG tÃ¬m tháº¥y file trong storage '{storage_path.parent}'."
        )
    file_path = resolved_path

    ext = Path(document.original_filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Document id={document.id} cÃ³ Ä‘uÃ´i file '{ext}' chÆ°a Ä‘Æ°á»£c G2 há»— trá»£ parse. "
            f"ÄÃ£ há»— trá»£: {sorted(SUPPORTED_EXTENSIONS)}. LÆ°u Ã½: endpoint upload "
            f"(app/api/v1/endpoints/document.py) Ä‘Ã£ Ä‘Æ°á»£c Ä‘á»“ng bá»™ ALLOWED_FILE_EXTENSIONS "
            f"theo parsing.SUPPORTED_EXTENSIONS nÃªn trÆ°á»ng há»£p nÃ y chá»‰ nÃªn xáº£y ra vá»›i "
            f"dá»¯ liá»‡u cÅ© táº¡o trÆ°á»›c khi tÃ­ch há»£p."
        )

    if file_path.stat().st_size <= 0:
        raise EmptyDocumentError(f"Document id={document.id} cÃ³ kÃ­ch thÆ°á»›c 0 byte - khÃ´ng cÃ³ ná»™i dung Ä‘á»ƒ xá»­ lÃ½.")

    return file_path


# ---------------------------------------------------------------------------
# BÆ°á»›c 3: metadata cho chunk (T10 - Metadata & Document Versioning)
# ---------------------------------------------------------------------------

def build_document_meta(document: DocumentRecord) -> dict:
    """Chuáº©n hoÃ¡ metadata gáº¯n vÃ o tá»«ng chunk theo chuáº©n chunk schema trong
    Kick-off Guide (document_name, department, access_level, version).

    Document model hiá»‡n táº¡i (app/model/document.py) CHÆ¯A cÃ³ field
    department/access_level/version - RBAC (UC-10) vÃ  version history
    (UC-17) chÆ°a Ä‘Æ°á»£c model hoÃ¡, thuá»™c pháº¡m vi T10/T20 (G2 phá»‘i há»£p G4).
    DÃ¹ng `getattr(..., default)` Ä‘á»ƒ hÃ m nÃ y hoáº¡t Ä‘á»™ng Ä‘Ãºng NGAY BÃ‚Y GIá»œ vá»›i
    model hiá»‡n táº¡i, vÃ  tá»± Ä‘á»™ng "nháº­n" field má»›i náº¿u G4 bá»• sung cá»™t tÆ°Æ¡ng á»©ng
    vÃ o báº£ng documents sau nÃ y - khÃ´ng cáº§n sá»­a láº¡i parsing/chunking/pipeline.
    """
    return {
        "document_name": document.original_filename,
        "department": getattr(document, "department", None),
        "access_level": getattr(document, "access_level", "internal"),
        "version": getattr(document, "version", 1),
    }


# ---------------------------------------------------------------------------
# Entrypoint chÃ­nh - dÃ¹ng bá»Ÿi pipeline.py (T11)
# ---------------------------------------------------------------------------

def ingest_document(
    document_id: int,
    db: Session,
) -> tuple[DocumentRecord, list[dict]]:
    """
    Entrypoint chÃ­nh cá»§a táº§ng ingestion.

    Args:
        document_id: id cá»§a Document cáº§n ingest (Ä‘Ã£ Ä‘Æ°á»£c upload trÆ°á»›c Ä‘Ã³
            qua POST /api/v1/documents/).
        db: Session hiá»‡n táº¡i. LÆ¯U Ã QUAN TRá»ŒNG: khi gá»i tá»« FastAPI
            BackgroundTasks, PHáº¢I dÃ¹ng session Má»šI má»Ÿ qua
            app.database.SessionLocal(), KHÃ”NG dÃ¹ng láº¡i session cá»§a
            request gá»‘c vÃ¬ session Ä‘Ã³ Ä‘Ã£ bá»‹ Ä‘Ã³ng ngay sau khi response Ä‘Æ°á»£c
            tráº£ vá» (xem pipeline.run_pipeline_background).

    Returns:
        (document, parsed_blocks): document ORM object (Ä‘á»ƒ láº¥y thÃªm metadata
        nhÆ° owner_id náº¿u cáº§n) vÃ  list parsed block sáºµn sÃ ng cho chunking.py.

    Raises:
        DocumentNotFoundError, DocumentFileMissingError, UnsupportedFileTypeError,
        EmptyDocumentError, ParsingError.
    """
    document = get_document_or_raise(document_id, db)
    file_path = validate_document_file(document)

    logger.info(
        "Ingestion: báº¯t Ä‘áº§u xá»­ lÃ½ document_id=%s file='%s' owner_id=%s path='%s'",
        document.id, document.original_filename, document.owner_id, file_path,
    )

    try:
        parsed_blocks = parse_document(
            file_path,
            document.original_filename,
            document.id,
        )
    except (ParsingError, UnsupportedFileTypeError):
        raise
    except Exception as exc:  # báº¯t má»i lá»—i khÃ´ng lÆ°á»ng trÆ°á»›c phÃ¡t sinh tá»« thÆ° viá»‡n parser
        raise ParsingError(
            f"Lá»—i khÃ´ng xÃ¡c Ä‘á»‹nh khi parse document_id={document.id} "
            f"('{document.original_filename}'): {exc}"
        ) from exc

    if not parsed_blocks:
        raise EmptyDocumentError(
            f"Document id={document.id} ('{document.original_filename}') Ä‘Æ°á»£c parse "
            f"thÃ nh cÃ´ng nhÆ°ng khÃ´ng cÃ³ ná»™i dung text nÃ o (cÃ³ thá»ƒ lÃ  PDF scan/áº£nh "
            f"chÆ°a OCR, hoáº·c file trá»‘ng)."
        )

    logger.info("Ingestion: document_id=%s parse xong, %s block.", document.id, len(parsed_blocks))
    return document, parsed_blocks


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(level=logging.INFO)
    print(
        "ingestion.py khÃ´ng cÃ³ cháº¿ Ä‘á»™ cháº¡y Ä‘á»™c láº­p vá»›i tÃ i liá»‡u thá»­ nghiá»‡m. "
        "HÃ£y dÃ¹ng API upload hoáº·c cháº¡y: "
        "python \"backend/app/doc_processing/test code/test_ingestion.py\" --owner-id <id>"
    )
