from tests.conftest import PASSWORD


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"email": "A@Example.com", "password": PASSWORD, "role": "student"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"  # email được chuẩn hóa chữ thường
    assert "password" not in r.text

    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["role"] == "student"


def test_duplicate_email_conflict(client):
    payload = {"email": "a@example.com", "password": PASSWORD, "role": "student"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_cannot_self_register_admin(client):
    r = client.post("/api/auth/register", json={"email": "x@example.com", "password": PASSWORD, "role": "admin"})
    assert r.status_code == 422


def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "x@example.com", "password": "123", "role": "student"})
    assert r.status_code == 422


def test_login_wrong_password(client, make_user):
    make_user("a@example.com", "student")
    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "sai-mat-khau"})
    assert r.status_code == 401
    r = client.post("/api/auth/login", json={"email": "khong-ton-tai@example.com", "password": PASSWORD})
    assert r.status_code == 401


def test_me_requires_token(client, make_user):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
    headers = make_user("a@example.com", "student")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200 and r.json()["email"] == "a@example.com"


def test_verify_endpoint(client, make_user):
    headers = make_user("a@example.com", "company")
    token = headers["Authorization"].split()[1]
    r = client.post("/api/auth/verify", json={"token": token})
    assert r.json()["valid"] is True and r.json()["role"] == "company"
    assert client.post("/api/auth/verify", json={"token": token + "x"}).json()["valid"] is False


def test_admin_only_endpoint_forbidden_for_student(client, make_user):
    headers = make_user("a@example.com", "student")
    assert client.get("/api/auth/users", headers=headers).status_code == 403
