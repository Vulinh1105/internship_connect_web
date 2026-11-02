"""Chuyß╗ân v─ân bß║ún th├ánh vector.

Mß║╖c ─æß╗ïnh d├╣ng 'hashing embedder': nhß║╣, chß║íy offline, kh├┤ng cß║ºn tß║úi model, hiß╗âu ─æ╞░ß╗úc tß╗½ kh├│a
(Python, FastAPI, SQL...) v├á bß╗Å dß║Ñu tiß║┐ng Viß╗çt. Muß╗æn ch├¡nh x├íc h╞ín vß╗ü ngß╗» ngh─⌐a th├¼ ─æß║╖t
EMBEDDING_BACKEND=sentence_transformers v├á c├ái th├¬m g├│i sentence-transformers.
"""
import hashlib
import logging
import math
import re
import unicodedata

from app.core.config import settings

log = logging.getLogger(__name__)

DIM = 512

# Tß╗½ rß║Ñt phß╗ò biß║┐n (─æ├ú bß╗Å dß║Ñu) kh├┤ng mang nhiß╗üu ├╜ ngh─⌐a
_STOPWORDS = {
    "va", "la", "cua", "cho", "cac", "mot", "nhung", "co", "duoc", "trong", "voi", "de", "khi",
    "se", "da", "can", "tai", "tu", "den", "the", "and", "of", "to", "in", "for", "a", "an", "or",
}


def strip_accents(text: str) -> str:
    text = text.replace("─æ", "d").replace("─É", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    text = strip_accents(text.lower())
    tokens = re.findall(r"[a-z0-9+#.]+", text)  # giß╗» c++, c#, node.js
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
        for a, b in zip(tokens, tokens[1:]):  # cß║╖p tß╗½ liß╗ün nhau, trß╗ìng sß╗æ thß║Ñp h╞ín
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
        from sentence_transformers import SentenceTransformer  # chß╗ë cß║ºn khi chß╗ìn backend n├áy

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()


_embedder = None


class OpenAIEmbedder:
    """Reuse the RAG provider; keep matching scoring and ranking unchanged."""
    name = "openai"

    def __init__(self):
        from app.modules.ai.providers.openai_client import create_embeddings
        from fastapi import HTTPException
        if not settings.OPENAI_API_KEY:
            raise HTTPException(503, "Chưa cấu hình OPENAI_API_KEY trong file .env")
        self._model = create_embeddings()
        self.dim = 1536

    def embed(self, text: str) -> list[float]:
        from openai import OpenAIError
        from fastapi import HTTPException
        try:
            vector = self._model.embed_query(text)
        except OpenAIError as exc:
            log.exception("OpenAI matching embedding unavailable")
            raise HTTPException(503, "Không kết nối được OpenAI. Kiểm tra API key và hạn mức tài khoản.") from exc
        self.dim = len(vector)
        return vector


def get_embedder():
    global _embedder
    if _embedder is None:
        if settings.EMBEDDING_BACKEND == "openai":
            _embedder = OpenAIEmbedder()
        if settings.EMBEDDING_BACKEND == "sentence_transformers":
            try:
                _embedder = SentenceTransformerEmbedder(settings.EMBEDDING_MODEL)
            except Exception as exc:
                log.warning("Kh├┤ng tß║úi ─æ╞░ß╗úc sentence-transformers (%s). D├╣ng hashing embedder.", exc)
        if _embedder is None:
            _embedder = HashingEmbedder()
    return _embedder


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
