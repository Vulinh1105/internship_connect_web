"""T├¡nh ─æiß╗âm ph├╣ hß╗úp v├á xß║┐p hß║íng Top-K. Kh├┤ng phß╗Ñ thuß╗Öc DB n├¬n dß╗à kiß╗âm thß╗¡."""
import re

from app.modules.ai.matching.embeddings import strip_accents

W_SEMANTIC = 0.6   # trß╗ìng sß╗æ ─æß╗Ö t╞░╞íng ─æß╗ông vector
W_SKILL = 0.4      # trß╗ìng sß╗æ tr├╣ng kß╗╣ n─âng
SKILL_SATURATION = 3  # tr├╣ng tß╗½ 3 kß╗╣ n─âng trß╗ƒ l├¬n th├¼ ─æß║ít ─æiß╗âm kß╗╣ n─âng tß╗æi ─æa


def _norm(text: str) -> str:
    return strip_accents(text.lower())


def matched_skills(skills: list[str], text: str) -> list[str]:
    """C├íc kß╗╣ n─âng cß╗ºa sinh vi├¬n c├│ xuß║Ñt hiß╗çn (nguy├¬n tß╗½) trong nß╗Öi dung tin thß╗▒c tß║¡p."""
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
    """hits: danh s├ích (internship_id, cosine, payload) lß║Ñy tß╗½ kho vector."""
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
