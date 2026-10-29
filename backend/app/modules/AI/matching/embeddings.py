"""Chuyển văn bản thành vector.

Mặc định dùng 'hashing embedder': nhẹ, chạy offline, không cần tải model, hiểu được từ khóa
(Python, FastAPI, SQL...) và bỏ dấu tiếng Việt. Muốn chính xác hơn về ngữ nghĩa thì đặt
EMBEDDING_BACKEND=sentence_transformers và cài thêm gói sentence-transformers.
"""
import hashlib
import logging
import math
import re
import unicodedata

from app.core.config import settings

log = logging.getLogger(__name__)

DIM = 512

# Từ rất phổ biến (đã bỏ dấu) không mang nhiều ý nghĩa
_STOPWORDS = {
    "va", "la", "cua", "cho", "cac", "mot", "nhung", "co", "duoc", "trong", "voi", "de", "khi",
    "se", "da", "can", "tai", "tu", "den", "the", "and", "of", "to", "in", "for", "a", "an", "or",
}


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    text = strip_accents(text.lower())
    tokens = re.findall(r"[a-z0-9+#.]+", text)  # giữ c++, c#, node.js
    tokens = [t.strip(".") for t in tokens]
    return [t for t in tokens if t and t not in _STOPWORDS]


class HashingEmbedder:
    name = "hashing"

    def __init__(self, dim: int = DIM):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        tokens = tokenize(text)
        weights: dict[str, float] = {}
        for tok in tokens:
            weights[tok] = weights.get(tok, 0.0) + 1.0
        for a, b in zip(tokens, tokens[1:]):  # cặp từ liền nhau, trọng số thấp hơn
            key = f"{a}_{b}"
            weights[key] = weights.get(key, 0.0) + 0.6

        vec = [0.0] * self.dim
        for feat, w in weights.items():
            h = int.from_bytes(hashlib.blake2b(feat.encode(), digest_size=8).digest(), "big")
            sign = 1.0 if (h >> 63) & 1 else -1.0
            vec[h % self.dim] += sign * math.sqrt(w)

        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec


class SentenceTransformerEmbedder:
    name = "sentence_transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # chỉ cần khi chọn backend này

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()


_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        if settings.EMBEDDING_BACKEND == "sentence_transformers":
            try:
                _embedder = SentenceTransformerEmbedder(settings.EMBEDDING_MODEL)
            except Exception as exc:
                log.warning("Không tải được sentence-transformers (%s). Dùng hashing embedder.", exc)
        if _embedder is None:
            _embedder = HashingEmbedder()
    return _embedder


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
