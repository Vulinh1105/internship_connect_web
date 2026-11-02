from __future__ import annotations
import json
import logging
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)
OUTPUT_CHUNKING_DIR = Path(
    os.getenv(
        "RAG_INDEX_DIR",
        str(Path(__file__).resolve().parents[5] / "data" / "runtime" / "rag-index"),
    )
).resolve()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "internship-connect-openai")
CHUNKS_STORE_FILE = OUTPUT_CHUNKING_DIR / "chunks.json"


def _qdrant_url() -> str:
    return os.getenv(
        "QDRANT_URL",
        f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}",
    )


def _qdrant_api_key() -> str | None:
    value = os.getenv("QDRANT_API_KEY")
    return None if value in {None, "", "None", "null"} else value


_STORE_LOCK = threading.Lock()



def _save_chunks_local(chunks: list[dict], document_id: int) -> None:
    """Luu / cap nhat chunks vao file JSON local RAG_INDEX_DIR/chunks.json.
    Khi re-ingest 1 document, cac chunk cu cua document_id do bi xoa truoc
    khi ghi moi, tranh trung lap.
    """
    OUTPUT_CHUNKING_DIR.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if CHUNKS_STORE_FILE.exists():
        try:
            with CHUNKS_STORE_FILE.open("r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("chunks.json bi loi, se ghi de: %s", exc)
            existing = []

    existing = [c for c in existing if c.get("document_id") != document_id]
    existing.extend(chunks)
    existing.sort(key=lambda c: (c.get("document_id", 0), c.get("chunk_index", 0)))

    try:
        with CHUNKS_STORE_FILE.open("w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        logger.info(
            "Da luu %s chunk cua document_id=%s vao %s (tong: %s chunk).",
            len(chunks),
            document_id,
            CHUNKS_STORE_FILE,
            len(existing),
        )
    except OSError as exc:
        logger.warning("Khong the ghi chunks.json: %s", exc)


# ---------------------------------------------------------------------------
# I/O: luu chunk vao Qdrant
# ---------------------------------------------------------------------------

def load_all_chunks() -> list[dict]:
    """Doc payload chunk tu Qdrant de phuc vu keyword retrieval."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=_qdrant_url(), api_key=_qdrant_api_key())
        if not client.collection_exists(QDRANT_COLLECTION):
            return []
        points, _ = client.scroll(
            QDRANT_COLLECTION, limit=10000, with_payload=True, with_vectors=False
        )
        chunks = []
        for point in points:
            payload = point.payload or {}
            metadata = payload.get("metadata", {})
            content = payload.get("page_content", payload.get("content", ""))
            chunks.append({"content": content, **metadata})
        return chunks
    except Exception as exc:
        logger.warning("Khong the doc chunk tu Qdrant: %s", exc)
        return []


def _delete_qdrant_document(document_id: int) -> None:
    from qdrant_client import QdrantClient, models

    client = QdrantClient(url=_qdrant_url(), api_key=_qdrant_api_key())
    if client.collection_exists(QDRANT_COLLECTION):
        client.delete(
            QDRANT_COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )


def _document_points_exist(document_id: int, expected_count: int) -> bool:
    """Xac nhan Qdrant da ghi du points sau khi client bao timeout."""
    if expected_count <= 0:
        return True
    try:
        from qdrant_client import QdrantClient, models

        client = QdrantClient(url=_qdrant_url(), api_key=_qdrant_api_key())
        if not client.collection_exists(QDRANT_COLLECTION):
            return False
        result = client.count(
            QDRANT_COLLECTION,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            ),
            exact=True,
        )
        return result.count == expected_count
    except Exception as exc:
        logger.warning(
            "Khong the xac nhan points sau timeout cho document_id=%s: %s",
            document_id,
            exc,
        )
        return False


def save_chunks(chunks: list[dict], document_id: int) -> str:
    """
    Xoa cac point cu cua tai lieu roi embedding va upsert chunk moi vao Qdrant.
    Dong thoi luu ban sao vao doc/chunks.json de debug/theo doi.

    embed_content (= contextual_prefix + content) duoc dung de embedding;
    content goc duoc luu trong payload de hien thi cho user.
    Cac truong con lai tro thanh payload metadata cua point.
    """
    with _STORE_LOCK:
        from langchain_core.documents import Document
        from app.modules.ai.rag.retrieval.embeddings import create_vector_db

        _delete_qdrant_document(document_id)

        docs = []
        for chunk in chunks:
            embed_text = chunk.get("embed_content") or chunk["content"]
            metadata = {
                key: value
                for key, value in chunk.items()
                if key not in ("content", "embed_content")
            }
            metadata["content"] = chunk["content"]
            docs.append(Document(page_content=embed_text, metadata=metadata))

        if docs:
            try:
                create_vector_db(docs)
            except Exception:
                if not _document_points_exist(document_id, len(chunks)):
                    raise
                logger.warning(
                    "Qdrant bao loi ghi nhung da co du %s points cho document_id=%s; "
                    "tiep tuc pipeline.",
                    len(chunks),
                    document_id,
                )

        logger.info(
            "Da index %s chunk cho document_id=%s vao collection '%s'.",
            len(chunks),
            document_id,
            QDRANT_COLLECTION,
        )

        try:
            _save_chunks_local(chunks, document_id)
        except Exception as exc:
            logger.warning(
                "Luu chunks.json local that bai (khong anh huong Qdrant): %s", exc
            )

        return QDRANT_COLLECTION


def delete_chunks_by_document(document_id: int) -> int:
    """Xoa toan bo chunk cua 1 document_id khoi kho chung - goi khi tai lieu
    bi xoa (UC-16 "Xoa tai lieu") de tranh chatbot van tra loi dua tren tai
    lieu Admin da xoa (du lieu "mo coi"). Tra ve so chunk da xoa."""
    with _STORE_LOCK:
        before = [
            chunk
            for chunk in load_all_chunks()
            if chunk.get("document_id") == document_id
        ]
        _delete_qdrant_document(document_id)

        if CHUNKS_STORE_FILE.exists():
            try:
                with CHUNKS_STORE_FILE.open("r", encoding="utf-8") as f:
                    existing = json.load(f)
                existing = [c for c in existing if c.get("document_id") != document_id]
                with CHUNKS_STORE_FILE.open("w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Khong the cap nhat chunks.json khi xoa document: %s", exc
                )

        if before:
            logger.info(
                "Da xoa %s chunk cua document_id=%s khoi Qdrant.",
                len(before),
                document_id,
            )
        return len(before)


