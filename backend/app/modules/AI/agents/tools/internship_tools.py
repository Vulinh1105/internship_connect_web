from fastapi import HTTPException
from app.modules.ai.matching.service import recommend
from app.modules.ai.schemas import RecommendationOut
from app.modules.internships.schemas import InternshipOut
def recommend_internships(db, user, message):
    if user.role != "student":
        raise HTTPException(403, "Chức năng dành cho sinh viên")
    return {"items": [RecommendationOut(
        internship=InternshipOut.model_validate(r["internship"]),
        score=r["score"], matched_skills=r["matched_skills"]
    ).model_dump(mode="json") for r in recommend(db, user)]}
