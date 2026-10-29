def test_create_and_get_profile(client, student):
    r = client.get("/api/students/me", headers=student)
    assert r.status_code == 200
    assert r.json()["full_name"] == "Nguyen Van A"


def test_first_profile_requires_full_name(client, make_user):
    headers = make_user("a@example.com", "student")
    assert client.get("/api/students/me", headers=headers).status_code == 404
    assert client.put("/api/students/me", headers=headers, json={"major": "IT"}).status_code == 400


def test_update_profile_partial(client, student):
    r = client.put("/api/students/me", headers=student, json={"phone": "0900000000", "gpa": 3.5})
    assert r.status_code == 200
    body = r.json()
    assert body["phone"] == "0900000000" and body["gpa"] == 3.5
    assert body["full_name"] == "Nguyen Van A"  # trường không gửi lên được giữ nguyên


def test_gpa_out_of_range(client, student):
    assert client.put("/api/students/me", headers=student, json={"gpa": 11}).status_code == 422


def test_skills_add_duplicate_delete(client, student):
    r = client.post("/api/students/me/skills", headers=student, json={"skill_name": "Python"})
    assert r.status_code == 201
    skill_id = r.json()["id"]
    assert client.post("/api/students/me/skills", headers=student, json={"skill_name": "  python "}).status_code == 409
    assert len(client.get("/api/students/me", headers=student).json()["skills"]) == 1
    assert client.delete(f"/api/students/me/skills/{skill_id}", headers=student).status_code == 204
    assert client.get("/api/students/me", headers=student).json()["skills"] == []


def test_cannot_view_other_students_profile(client, student, make_user):
    other = make_user("other@example.com", "student")
    client.put("/api/students/me", headers=other, json={"full_name": "Nguoi Khac"})
    other_id = client.get("/api/students/me", headers=other).json()["id"]
    my_id = client.get("/api/students/me", headers=student).json()["id"]
    assert client.get(f"/api/students/{other_id}", headers=student).status_code == 403
    assert client.get(f"/api/students/{my_id}", headers=student).status_code == 200


def test_company_cannot_use_student_endpoints(client, company):
    assert client.get("/api/students/me", headers=company).status_code == 403


def test_cv_upload_validation(client, student):
    bad = client.post("/api/students/me/cvs", headers=student, files={"file": ("virus.exe", b"MZ", "application/octet-stream")})
    assert bad.status_code == 400
    ok = client.post("/api/students/me/cvs", headers=student, files={"file": ("cv.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert ok.status_code == 201 and ok.json()["is_primary"] is True
    assert "file_path" not in ok.json()  # không lộ đường dẫn trên server
