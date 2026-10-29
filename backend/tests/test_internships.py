from datetime import date, datetime, timedelta


def _future(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


def _post_internship(client, company, **overrides):
    body = {
        "title": "Thực tập sinh Python Backend",
        "description": "Xây dựng API",
        "requirements": "Python, FastAPI, SQL",
        "location": "Hà Nội",
        "deadline": _future(),
    }
    body.update(overrides)
    r = client.post("/api/internships", headers=company, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_company_profile_only_once(client, company):
    r = client.post("/api/companies", headers=company, json={"company_name": "Lần hai"})
    assert r.status_code == 409
    assert client.get("/api/companies/me", headers=company).json()["company_name"] == "Cong ty Test"


def test_student_cannot_create_internship(client, student):
    r = client.post("/api/internships", headers=student, json={"title": "X"})
    assert r.status_code == 403


def test_create_requires_company_profile(client, make_user):
    headers = make_user("dn2@example.com", "company")
    assert client.post("/api/internships", headers=headers, json={"title": "X"}).status_code == 404


def test_past_deadline_rejected(client, company):
    r = client.post("/api/internships", headers=company, json={"title": "X", "deadline": "2000-01-01"})
    assert r.status_code == 400


def test_public_list_search_and_pagination(client, company):
    _post_internship(client, company, title="Python Backend Intern")
    _post_internship(client, company, title="Marketing Intern", requirements="SEO", location="Đà Nẵng")
    r = client.get("/api/internships")  # không cần đăng nhập
    assert r.status_code == 200 and r.json()["total"] == 2
    assert client.get("/api/internships?q=python").json()["total"] == 1
    assert client.get("/api/internships?location=nẵng").json()["total"] == 1
    page = client.get("/api/internships?page=1&page_size=1").json()
    assert len(page["items"]) == 1 and page["total"] == 2
    assert page["items"][0]["company_name"] == "Cong ty Test"


def test_search_treats_percent_literally(client, company):
    _post_internship(client, company)
    assert client.get("/api/internships?q=%25").json()["total"] == 0


def test_close_hides_from_public_list(client, company):
    item = _post_internship(client, company)
    assert client.post(f"/api/internships/{item['id']}/close", headers=company).json()["status"] == "closed"
    assert client.get("/api/internships").json()["total"] == 0
    assert client.get("/api/internships/mine", headers=company).json()["total"] == 1


def test_other_company_cannot_edit(client, company, make_user):
    item = _post_internship(client, company)
    other = make_user("dn3@example.com", "company")
    client.post("/api/companies", headers=other, json={"company_name": "Cong ty Khac"})
    r = client.put(f"/api/internships/{item['id']}", headers=other, json={"title": "Hack"})
    assert r.status_code == 403
    assert client.post(f"/api/internships/{item['id']}/close", headers=other).status_code == 403


def test_apply_flow_and_duplicate(client, company, student):
    item = _post_internship(client, company)
    url = f"/api/internships/{item['id']}/applications"
    r = client.post(url, headers=student, json={"cover_letter": "Em muốn ứng tuyển"})
    assert r.status_code == 201
    assert r.json()["status"] == "pending"
    assert client.post(url, headers=student, json={}).status_code == 409

    mine = client.get("/api/applications/me", headers=student).json()
    assert mine["total"] == 1
    assert mine["items"][0]["internship_title"] == "Thực tập sinh Python Backend"


def test_apply_requires_profile_and_role(client, company, make_user):
    item = _post_internship(client, company)
    url = f"/api/internships/{item['id']}/applications"
    no_profile = make_user("moi@example.com", "student")
    assert client.post(url, headers=no_profile, json={}).status_code == 400
    assert client.post(url, headers=company, json={}).status_code == 403
    assert client.post(url, json={}).status_code == 401


def test_apply_to_closed_internship(client, company, student):
    item = _post_internship(client, company)
    client.post(f"/api/internships/{item['id']}/close", headers=company)
    r = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={})
    assert r.status_code == 400


def test_apply_to_missing_internship(client, student):
    assert client.post("/api/internships/9999/applications", headers=student, json={}).status_code == 404


def test_company_reviews_applicants_and_updates_status(client, company, student):
    item = _post_internship(client, company)
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={}).json()["id"]
    client.post("/api/students/me/skills", headers=student, json={"skill_name": "Python"})

    r = client.get(f"/api/internships/{item['id']}/applications", headers=company)
    assert r.status_code == 200 and r.json()["total"] == 1
    applicant = r.json()["items"][0]
    assert applicant["student"]["full_name"] == "Nguyen Van A"
    assert applicant["student"]["skills"] == ["Python"]

    r = client.patch(f"/api/applications/{app_id}/status", headers=company, json={"status": "reviewing"})
    assert r.status_code == 200 and r.json()["status"] == "reviewing"
    # sinh viên thấy trạng thái mới
    assert client.get("/api/applications/me", headers=student).json()["items"][0]["status"] == "reviewing"

    assert client.patch(f"/api/applications/{app_id}/status", headers=company, json={"status": "accepted"}).status_code == 200
    # đã có kết quả cuối thì không đổi được nữa
    assert client.patch(f"/api/applications/{app_id}/status", headers=company, json={"status": "rejected"}).status_code == 409
    # giá trị ngoài danh sách bị chặn
    assert client.patch(f"/api/applications/{app_id}/status", headers=company, json={"status": "hired"}).status_code == 422


def test_company_cannot_touch_other_companys_applications(client, company, student, make_user):
    item = _post_internship(client, company)
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={}).json()["id"]
    other = make_user("dn4@example.com", "company")
    client.post("/api/companies", headers=other, json={"company_name": "Doi thu"})
    assert client.get(f"/api/internships/{item['id']}/applications", headers=other).status_code == 403
    assert client.patch(f"/api/applications/{app_id}/status", headers=other, json={"status": "accepted"}).status_code == 403
    assert client.get(f"/api/applications/{app_id}", headers=other).status_code == 403


def test_student_cannot_change_status(client, company, student):
    item = _post_internship(client, company)
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={}).json()["id"]
    assert client.patch(f"/api/applications/{app_id}/status", headers=student, json={"status": "accepted"}).status_code == 403


def test_withdraw(client, company, student):
    item = _post_internship(client, company)
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={}).json()["id"]
    assert client.post(f"/api/applications/{app_id}/withdraw", headers=student).json()["status"] == "withdrawn"
    assert client.post(f"/api/applications/{app_id}/withdraw", headers=student).status_code == 409


def test_cv_must_belong_to_applicant(client, company, student, make_user):
    item = _post_internship(client, company)
    other = make_user("khac@example.com", "student")
    client.put("/api/students/me", headers=other, json={"full_name": "Khac"})
    cv = client.post("/api/students/me/cvs", headers=other, files={"file": ("cv.pdf", b"%PDF-1.4 x", "application/pdf")}).json()
    r = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={"cv_id": cv["id"]})
    assert r.status_code == 400


def test_company_can_download_attached_cv(client, company, student):
    item = _post_internship(client, company)
    cv = client.post("/api/students/me/cvs", headers=student, files={"file": ("cv.pdf", b"%PDF-1.4 hello", "application/pdf")}).json()
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={"cv_id": cv["id"]}).json()["id"]
    r = client.get(f"/api/applications/{app_id}/cv", headers=company)
    assert r.status_code == 200 and r.content == b"%PDF-1.4 hello"


def test_stats_staff_only(client, company, make_user):
    _post_internship(client, company)
    assert client.get("/api/internships/stats", headers=company).status_code == 403


def test_interview_flow(client, company, student):
    item = _post_internship(client, company)
    app_id = client.post(f"/api/internships/{item['id']}/applications", headers=student, json={}).json()["id"]
    when = (datetime.now() + timedelta(days=3)).replace(microsecond=0).isoformat()

    r = client.post("/api/interviews", headers=company, json={"application_id": app_id, "scheduled_at": when, "location": "Văn phòng"})
    assert r.status_code == 201, r.text
    iv = r.json()
    assert iv["status"] == "invited" and iv["student_name"] == "Nguyen Van A"
    # mời phỏng vấn thì hồ sơ chuyển sang reviewing
    assert client.get(f"/api/applications/{app_id}", headers=company).json()["status"] == "reviewing"

    past = (datetime.now() - timedelta(days=1)).replace(microsecond=0).isoformat()
    assert client.post("/api/interviews", headers=company, json={"application_id": app_id, "scheduled_at": past, "location": "X"}).status_code == 400

    # sinh viên đề nghị đổi lịch phải có lời nhắn
    assert client.post(f"/api/interviews/{iv['id']}/respond", headers=student, json={"action": "reschedule"}).status_code == 400
    r = client.post(f"/api/interviews/{iv['id']}/respond", headers=student, json={"action": "confirm"})
    assert r.status_code == 200 and r.json()["status"] == "confirmed"
    # đã phản hồi rồi thì không phản hồi lại
    assert client.post(f"/api/interviews/{iv['id']}/respond", headers=student, json={"action": "decline"}).status_code == 409

    mine = client.get("/api/interviews/me", headers=student).json()
    assert mine["total"] == 1
    assert client.get("/api/interviews/me", headers=company).json()["total"] == 1
