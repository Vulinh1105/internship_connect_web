"""Kho vector dùng chung cho matching và RAG.

- Ưu tiên Qdrant chạy local (lưu vào thư mục QDRANT_PATH, miễn phí, không cần server).
- Nếu chưa cài qdrant-client hoặc Qdrant lỗi thì tự chuyển sang bộ nhớ trong (mất khi tắt app).
Luôn giữ thêm một bản trong bộ nhớ để làm phương án dự phòng.
"""
import logging
import threading

from app.core.config import settings

log = logging.getLogger(__name__)

# Một item là (id: int, vector: list[float], payload: dict)
Item = tuple[int, list[float], dict]


class MemoryStore:
    def __init__(self):
        self._data: dict[str, dict[int, tuple[list[float], dict]]] = {}

    def replace(self, collection: str, items: list[Item], dim: int) -> None:
        self._data[collection] = {i: (vec, payload) for i, vec, payload in items}

    def search(self, collection: str, vector: list[float], top_k: int) -> list[tuple[int, float, dict]]:
        scored = []
        for i, (vec, payload) in self._data.get(collection, {}).items():
            score = sum(a * b for a, b in zip(vector, vec))  # vector đã chuẩn hóa nên tích vô hướng = cosine
            scored.append((i, score, payload))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class QdrantStore:
    def __init__(self, path: str):
        from qdrant_client import QdrantClient  # import muộn để không bắt buộc phải cài

        self.client = QdrantClient(path=path)

    def replace(self, collection: str, items: list[Item], dim: int) -> None:
        from qdrant_client.models import Distance, PointStruct, VectorParams

        if self.client.collection_exists(collection):
            self.client.delete_collection(collection)
        self.client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        if items:
            points = [PointStruct(id=i, vector=vec, payload=payload) for i, vec, payload in items]
            self.client.upsert(collection_name=collection, points=points)

    def search(self, collection: str, vector: list[float], top_k: int) -> list[tuple[int, float, dict]]:
        result = self.client.query_points(
            collection_name=collection, query=vector, limit=top_k, with_payload=True
        )
        return [(int(p.id), float(p.score), p.payload or {}) for p in result.points]


class VectorStore:
    def __init__(self):
        self._memory = MemoryStore()
        self._qdrant: QdrantStore | None = None
        self._lock = threading.Lock()
        if settings.VECTOR_BACKEND in ("auto", "qdrant"):
            try:
                self._qdrant = QdrantStore(settings.QDRANT_PATH)
                log.info("Vector store: Qdrant local tại %s", settings.QDRANT_PATH)
            except Exception as exc:  # chưa cài, thư mục bị khóa bởi tiến trình khác...
                log.warning("Không dùng được Qdrant (%s). Chuyển sang bộ nhớ trong.", exc)
        else:
            log.info("Vector store: bộ nhớ trong")

    @property
    def backend(self) -> str:
        return "qdrant" if self._qdrant else "memory"

    def replace(self, collection: str, items: list[Item], dim: int) -> None:
        with self._lock:
            self._memory.replace(collection, items, dim)
            if self._qdrant:
                try:
                    self._qdrant.replace(collection, items, dim)
                except Exception as exc:
                    log.warning("Qdrant lỗi khi ghi (%s). Chuyển sang bộ nhớ trong.", exc)
                    self._qdrant = None

    def search(self, collection: str, vector: list[float], top_k: int) -> list[tuple[int, float, dict]]:
        with self._lock:
            if self._qdrant:
                try:
                    return self._qdrant.search(collection, vector, top_k)
                except Exception as exc:
                    log.warning("Qdrant lỗi khi tìm (%s). Chuyển sang bộ nhớ trong.", exc)
                    self._qdrant = None
            return self._memory.search(collection, vector, top_k)


_store: VectorStore | None = None
_store_lock = threading.Lock()


def get_store() -> VectorStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = VectorStore()
        return _store
