def test_login_good_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jane.doe@example.com", "password": "password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_bad_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jane.doe@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_with_bearer_token(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "jane.doe@example.com", "password": "password"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "jane.doe@example.com"
    assert body["id"] == 2


def test_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


def test_me_with_garbage_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
