USER = {"email": "seray@example.com", "password": "gizli1234", "name": "Seray"}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**USER, **overrides})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_user_and_tokens(client):
    res = register(client)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["user"]["email"] == USER["email"]
    assert data["user"]["onboarding_done"] is False
    assert data["access_token"] and data["refresh_token"]


def test_register_duplicate_email(client):
    register(client)
    res = register(client, email="SERAY@example.com")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_short_password(client):
    res = register(client, password="123")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_success_and_wrong_password(client):
    register(client)
    ok = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={"email": USER["email"], "password": "yanlis1234"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_token(client):
    assert client.get("/api/users/me").json()["error"]["code"] == "UNAUTHORIZED"
    assert client.get("/api/users/me", headers=auth_header("bozuk")).status_code == 401


def test_me_and_update(client):
    token = register(client).json()["data"]["access_token"]
    res = client.put("/api/users/me", json={"district": "Çankaya"}, headers=auth_header(token))
    assert res.json()["data"]["district"] == "Çankaya"
    assert client.get("/api/users/me", headers=auth_header(token)).json()["data"]["name"] == "Seray"


def test_refresh(client):
    tokens = register(client).json()["data"]
    res = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    new_access = res.json()["data"]["access_token"]
    assert client.get("/api/users/me", headers=auth_header(new_access)).status_code == 200
    # access token ile refresh yapılamaz
    bad = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert bad.status_code == 401
