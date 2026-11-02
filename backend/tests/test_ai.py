from datetime import date, timedelta

from app.modules.ai.matching.embeddings import cosine, get_embedder
from app.modules.ai.matching.ranking import matched_skills, rank_candidates


# ---------- Kiểm thử đơn vị (không cần DB) ----------
def test_embedding_similarity_orders_correctly():
    e = get_embedder()
    query = e.embed("Công nghệ thông tin. Python FastAPI SQL")
    relevant = e.embed("Thực tập sinh Python Backend. Yêu cầu Python, FastAPI, SQL")
    irrelevant = e.embed("Thực tập sinh Marketing. Yêu cầu viết nội dung, SEO, Facebook Ads")
    assert cosine(query, relevant) > cosine(query, irrelevant)


def test_skill_matching_uses_whole_words():
    assert matched_skills(["Java"], "Yêu cầu JavaScript") == []
    assert matched_skills(["Python", "SQL"], "Cần Python và sql") == ["Python", "SQL"]


def test_rank_candidates_prefers_skill_overlap():
    hits = [(1, 0.30, {"text": "marketing seo"}), (2, 0.30, {"text": "python fastapi sql"})]
    ranked = rank_candidates(hits, ["Python", "SQL"], top_k=2)
    assert ranked[0]["internship_id"] == 2


# ---------- Kiểm thử API ----------
def _post(client, company, title, requirements):
    r = client.post(
        "/api/internships",
        headers=company,
        json={"title": title, "requirements": requirements, "deadline": (date.today() + timedelta(days=30)).isoformat()},
    )
    assert r.status_code == 201


def test_recommendations_rank_relevant_first(client, company, student):
    _post(client, company, "Thực tập sinh Marketing", "Content, SEO, Facebook Ads")
    _post(client, company, "Thực tập sinh Python Backend", "Python, FastAPI, SQL")
    client.post("/api/students/me/skills", headers=student, json={"skill_name": "Python"})
    client.post("/api/students/me/skills", headers=student, json={"skill_name": "SQL"})

    r = client.get("/api/ai/recommendations?top_k=2", headers=student)
    assert r.status_code == 200, r.text
    items = r.json()
    assert items[0]["internship"]["title"] == "Thực tập sinh Python Backend"
    assert set(items[0]["matched_skills"]) == {"Python", "SQL"}
    assert items[0]["score"] >= items[1]["score"]


def test_recommendations_need_profile_content(client, make_user):
    headers = make_user("trong@example.com", "student")
    assert client.get("/api/ai/recommendations", headers=headers).status_code == 404  # chưa có hồ sơ
    client.put("/api/students/me", headers=headers, json={"full_name": "Trống"})
    assert client.get("/api/ai/recommendations", headers=headers).status_code == 400  # hồ sơ trống


def test_recommendations_student_only(client, company):
    assert client.get("/api/ai/recommendations", headers=company).status_code == 403


def test_chat_exposes_existing_pipeline_result(client, student, monkeypatch):
    from app.modules.ai.rag import rag_pipeline
    calls = []
    def run(query, session_id, **kwargs):
        calls.append((query, session_id))
        return {"answer": "Câu trả lời từ pipeline", "citations": [{"source": "guide.pdf", "pages": [1]}],
                "top_rerank_score": 0.8}
    monkeypatch.setattr(rag_pipeline, "run_rag", run)
    r = client.post("/api/ai/chat", headers=student, json={"question": "Làm sao để rút hồ sơ ứng tuyển?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "rag"
    assert body["answer"] == "Câu trả lời từ pipeline"
    assert body["sources"][0]["source"] == "guide.pdf"
    assert calls[0][1].startswith("user:")


def test_chat_requires_login(client):
    assert client.post("/api/ai/chat", json={"question": "xin chào bạn"}).status_code == 401


def test_agent_dispatches_explicit_matching_tool(client, company, student):
    _post(client, company, "Thực tập sinh Python Backend", "Python, FastAPI")
    client.post("/api/students/me/skills", headers=student, json={"skill_name": "Python"})
    r = client.post("/api/ai/agent", headers=student, json={"message": "Gợi ý cho tôi vị trí phù hợp", "tool": "recommend_internships"})
    assert r.status_code == 200 and r.json()["tool"] == "recommend_internships"
    assert r.json()["data"]["items"][0]["matched_skills"] == ["Python"]


def test_reindex_staff_only(client, student):
    assert client.post("/api/ai/reindex", headers=student).status_code == 403
