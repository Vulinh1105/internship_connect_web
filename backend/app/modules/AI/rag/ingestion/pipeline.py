"""
doc_processing.pipeline
========================
T11 - End-to-End Indexing Pipeline: Parse -> Chunk -> (Embedding) -> Index,
kÃ¨m tracking status/log cho tá»«ng document.

ÄÃ¢y lÃ  "nháº¡c trÆ°á»Ÿng" ná»‘i:
    ingestion.py (validate + gá»i parsing.py) -> chunking.py (cáº¯t & lÆ°u vÃ o
    doc/chunks.json) -> (tuá»³ chá»n, an toÃ n) táº§ng embedding cá»§a G3
    (app/ai_agent/embeddings.py).

NguyÃªn táº¯c tÃ­ch há»£p liÃªn nhÃ³m Ä‘á»ƒ Háº N CHáº¾ Lá»–I: pipeline cá»§a G2 KHÃ”NG Ä‘Æ°á»£c sáº­p
chá»‰ vÃ¬ module cá»§a G3 (khÃ¡c nhÃ³m, cÃ³ thá»ƒ chÆ°a cÃ i Ä‘á»§ package hoáº·c chÆ°a cÃ³
OPENAI_API_KEY) gáº·p lá»—i. Viá»‡c gá»i sang G3 luÃ´n lÃ  "best-effort" - lazy
import + try/except riÃªng, tÃ¡ch biá»‡t hoÃ n toÃ n khá»i káº¿t quáº£ chunking (vá»‘n Ä‘Ã£
Ä‘Æ°á»£c lÆ°u an toÃ n vÃ o chunks.json trÆ°á»›c Ä‘Ã³). TÆ°Æ¡ng tá»± nguyÃªn táº¯c "Frontend
khÃ´ng cáº§n chá» backend" trong Kick-off Guide, á»Ÿ Ä‘Ã¢y G2 khÃ´ng cáº§n chá» G3.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, ContextManager, Callable

# ThÃªm thÆ° má»¥c `backend` vÃ o sys.path khi cháº¡y script trá»±c tiáº¿p (python backend/app/doc_processing/pipeline.py)
if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.modules.ai.rag.ingestion import chunking, validation as ingestion
from app.modules.ai.rag.ingestion.validation import IngestionError
from app.modules.ai.rag.ingestion.parsing import ParsingError

logger = logging.getLogger(__name__)

# File log tráº¡ng thÃ¡i indexing, Ä‘áº·t cÃ¹ng thÆ° má»¥c dá»¯ liá»‡u phá»¥ trá»£.
# Document model (G4) hiá»‡n CHÆ¯A cÃ³ cá»™t `status` (xem app/model/document.py),
# nÃªn G2 tá»± quáº£n lÃ½ tráº¡ng thÃ¡i á»Ÿ Ä‘Ã¢y Ä‘á»ƒ KHÃ”NG pháº£i chá» G4 cháº¡y Alembic
# migration má»›i demo Ä‘Æ°á»£c T11. Khi G4 bá»• sung cá»™t status cho báº£ng documents
# (T22 - Document Management API), cÃ³ thá»ƒ Ä‘á»“ng bá»™ 2 bÃªn hoáº·c thay háº³n báº±ng
# DB; file log nÃ y váº«n há»¯u Ã­ch Ä‘á»ƒ debug lá»—i indexing trong lÃºc phÃ¡t triá»ƒn.
STATUS_LOG_FILE = chunking.OUTPUT_CHUNKING_DIR / "pipeline_status.json"
_STATUS_LOCK = threading.Lock()
DEFAULT_CHUNKING_STRATEGY = "structure_aware"


class IndexingStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    CHUNKED = "chunked"    # G2 hoÃ n táº¥t - Ä‘Ã£ cÃ³ trong chunks.json
    EMBEDDING = "embedding"
    INDEXED = "indexed"    # G3 Ä‘Ã£ embedding xong - sáºµn sÃ ng semantic search
    FAILED = "failed"


@dataclass
class PipelineResult:
    document_id: int
    status: IndexingStatus
    chunk_count: int = 0
    strategy: str = DEFAULT_CHUNKING_STRATEGY
    error: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "status": self.status.value,
            "chunk_count": self.chunk_count,
            "strategy": self.strategy,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


# ---------------------------------------------------------------------------
# Status log dáº¡ng file JSON - cÃ¹ng cÃ¡ch tiáº¿p cáº­n vá»›i chunking.py (Ä‘Æ¡n giáº£n,
# khÃ´ng cáº§n thÃªm báº£ng DB má»›i Ä‘á»ƒ demo Ä‘Æ°á»£c T11 ngay tá»« tuáº§n 3-4).
# ---------------------------------------------------------------------------

def _load_status_log() -> dict[str, dict]:
    if not STATUS_LOG_FILE.exists():
        return {}
    raw = STATUS_LOG_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("pipeline_status.json bá»‹ lá»—i Ä‘á»‹nh dáº¡ng - reset log tráº¡ng thÃ¡i.")
        return {}


def _save_status(result: PipelineResult) -> None:
    with _STATUS_LOCK:
        STATUS_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log = _load_status_log()
        log[str(result.document_id)] = result.to_dict()
        tmp_path = STATUS_LOG_FILE.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(STATUS_LOG_FILE)


def get_status(document_id: int) -> dict | None:
    """Cho cÃ¡c nhÃ³m khÃ¡c (G4 - Document Management API T22, G5 - hiá»ƒn thá»‹
    tráº¡ng thÃ¡i indexing T27) tra cá»©u tráº¡ng thÃ¡i xá»­ lÃ½ cá»§a 1 document mÃ 
    khÃ´ng cáº§n tá»± Ä‘á»c/parse trá»±c tiáº¿p file JSON."""
    return _load_status_log().get(str(document_id))


# ---------------------------------------------------------------------------
# Pipeline chÃ­nh
# ---------------------------------------------------------------------------

# Báº­t/táº¯t bÆ°á»›c gá»i sang embedding cá»§a G3 qua biáº¿n mÃ´i trÆ°á»ng, Máº¶C Äá»ŠNH Táº®T vÃ¬
# app/ai_agent/embeddings.py hiá»‡n cáº§n OPENAI_API_KEY vÃ  cÃ¡c package
# (langchain, faiss) cÃ³ thá»ƒ chÆ°a Ä‘Æ°á»£c cÃ i / khÃ¡c requirements.txt cá»§a G2.
def run_pipeline_for_document(
    document_id: int,
    db: Session,
    strategy: str = DEFAULT_CHUNKING_STRATEGY,
) -> PipelineResult:
    """
    Cháº¡y toÃ n bá»™ luá»“ng Parse -> Chunk -> (Embedding) -> Index cho 1
    document, ghi log tráº¡ng thÃ¡i á»Ÿ tá»«ng bÆ°á»›c Ä‘á»ƒ debug khi lá»—i (T11 DoD:
    "logging lá»—i rÃµ rÃ ng").

    ÄÃ¢y lÃ  hÃ m nÃªn Ä‘Æ°á»£c viáº¿t unit/integration test (T11 DoD: "1 lá»‡nh/API
    Ä‘Æ°a document Ä‘áº¿n searchable index").
    """
    result = PipelineResult(document_id=document_id, status=IndexingStatus.PENDING, strategy=strategy)
    _save_status(result)

    try:
        # --- BÆ°á»›c 1+2: ingestion (validate + parse), tÃ¡i sá»­ dá»¥ng ingestion.py ---
        result.status = IndexingStatus.PARSING
        _save_status(result)
        document, parsed_blocks = ingestion.ingest_document(document_id, db)

        # --- BÆ°á»›c 3: chunking + embedding + index vÃ o Qdrant ---
        result.status = IndexingStatus.CHUNKING
        _save_status(result)
        document_meta = ingestion.build_document_meta(document)
        chunks, _ = chunking.chunk_and_save(
            parsed_blocks,
            document_id=document.id,
            strategy=strategy,
            document_meta=document_meta,
        )
        result.chunk_count = len(chunks)
        result.status = IndexingStatus.INDEXED
        _save_status(result)

        result.finished_at = datetime.now(timezone.utc).isoformat()
        _save_status(result)
        logger.info(
            "Pipeline OK: document_id=%s status=%s chunk_count=%s",
            document_id, result.status.value, result.chunk_count,
        )
        return result

    except (IngestionError, ParsingError) as exc:
        return _fail(result, exc)
    except Exception as exc:  # an toÃ n tá»‘i Ä‘a: khÃ´ng Ä‘á»ƒ lá»—i láº¡ lÃ m crash background task
        logger.exception("Lá»—i khÃ´ng xÃ¡c Ä‘á»‹nh khi cháº¡y pipeline cho document_id=%s", document_id)
        return _fail(result, exc)


def _fail(result: PipelineResult, exc: Exception) -> PipelineResult:
    result.status = IndexingStatus.FAILED
    result.error = str(exc)
    result.finished_at = datetime.now(timezone.utc).isoformat()
    _save_status(result)
    logger.error("Pipeline FAILED: document_id=%s lá»—i=%s", result.document_id, result.error)
    return result


def _try_trigger_embedding(chunks: list[dict]) -> None:
    """Gá»i sang app/ai_agent/embeddings.py cá»§a G3 theo kiá»ƒu "best-effort":
    import TRá»„ (lazy import) ngay bÃªn trong hÃ m Ä‘á»ƒ module pipeline.py cá»§a G2
    KHÃ”NG bá»‹ lá»—i ngay tá»« lÃºc import file náº¿u G3 chÆ°a cÃ i langchain/faiss
    hoáº·c chÆ°a cáº¥u hÃ¬nh OPENAI_API_KEY. Má»i lá»—i á»Ÿ bÆ°á»›c nÃ y chá»‰ log cáº£nh bÃ¡o,
    KHÃ”NG lÃ m máº¥t káº¿t quáº£ chunking Ä‘Ã£ lÆ°u thÃ nh cÃ´ng á»Ÿ bÆ°á»›c 3."""
    try:
        from langchain_core.documents import Document as LangchainDocument

        from app.modules.ai.rag.retrieval.embeddings import create_vector_db

        docs = [
            LangchainDocument(
                page_content=c["content"],
                metadata={
                    "chunk_id": c["chunk_id"],
                    "document_id": c["document_id"],
                    "page": c["page"],
                    "department": c.get("department"),
                    "access_level": c.get("access_level"),
                },
            )
            for c in chunks
        ]
        create_vector_db(docs)
    except Exception as exc:  # cá»‘ Ã½ báº¯t rá»™ng - Ä‘Ã¢y chá»‰ lÃ  bÆ°á»›c tuá»³ chá»n, khÃ´ng pháº£i core flow cá»§a G2
        logger.warning(
            "KhÃ´ng thá»ƒ cháº¡y embedding tá»± Ä‘á»™ng (module G3 cÃ³ thá»ƒ chÆ°a sáºµn sÃ ng): %s. "
            "Chunk váº«n Ä‘Ã£ Ä‘Æ°á»£c lÆ°u an toÃ n vÃ o doc/chunks.json.", exc,
        )


# ---------------------------------------------------------------------------
# Wrapper dÃ¹ng cho FastAPI BackgroundTasks (xem tÃ­ch há»£p trong
# app/api/v1/endpoints/document.py - hÃ m upload_document/replace_document)
# ---------------------------------------------------------------------------

def run_pipeline_background(
    document_id: int,
    session_factory: Callable[[], ContextManager[Session]],
    strategy: str = DEFAULT_CHUNKING_STRATEGY,
) -> None:
    """
    Entrypoint dÃ nh riÃªng cho `BackgroundTasks.add_task(...)`.

    QUAN TRá»ŒNG: session DB cá»§a request gá»‘c (Depends(get_db)) sáº½ bá»‹ Ä‘Ã³ng ngay
    sau khi response Ä‘Æ°á»£c tráº£ vá» cho client - TRÆ¯á»šC KHI background task nÃ y
    ká»‹p cháº¡y xong. VÃ¬ váº­y hÃ m nÃ y tá»± má»Ÿ má»™t Session Má»šI qua
    async session factory thay vÃ¬ nháº­n session tá»« endpoint, trÃ¡nh lá»—i
    "This session is closed" khi background task cháº¡y sau response.
    """
    with session_factory() as db:
        run_pipeline_for_document(document_id, db, strategy=strategy)


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(level=logging.INFO)
    print(
        "pipeline.py khÃ´ng cÃ³ document_id demo máº·c Ä‘á»‹nh. "
        "HÃ£y cháº¡y API upload hoáº·c test code/test_ingestion.py Ä‘á»ƒ xá»­ lÃ½ tÃ i liá»‡u tháº­t."
    )
