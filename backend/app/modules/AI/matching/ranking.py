"""Tính điểm phù hợp và xếp hạng Top-K. Không phụ thuộc DB nên dễ kiểm thử."""
import re

from app.modules.ai.matching.embeddings import strip_accents

W_SEMANTIC = 0.6   # trọng số độ tương đồng vector
W_SKILL = 0.4      # trọng số trùng kỹ năng
SKILL_SATURATION = 3  # trùng từ 3 kỹ năng trở lên thì đạt điểm kỹ năng tối đa


def _norm(text: str) -> str:
    return strip_accents(text.lower())


def matched_skills(skills: list[str], text: str) -> list[str]:
    """Các kỹ năng của sinh viên có xuất hiện (nguyên từ) trong nội dung tin thực tập."""
    haystack = _norm(text)
    found = []
    for skill in skills:
        needle = _norm(skill).strip()
        if not needle:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack):
            found.append(skill)
    return found


def score(cosine_value: float, n_matched: int) -> float:
    semantic = max(0.0, min(1.0, cosine_value))
    skill = min(1.0, n_matched / SKILL_SATURATION)
    return round(W_SEMANTIC * semantic + W_SKILL * skill, 4)


def rank_candidates(hits: list[tuple[int, float, dict]], student_skills: list[str], top_k: int) -> list[dict]:
    """hits: danh sách (internship_id, cosine, payload) lấy từ kho vector."""
    ranked = []
    for internship_id, cos, payload in hits:
        found = matched_skills(student_skills, payload.get("text", ""))
        ranked.append(
            {
                "internship_id": internship_id,
                "score": score(cos, len(found)),
                "matched_skills": found,
            }
        )
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:top_k]
