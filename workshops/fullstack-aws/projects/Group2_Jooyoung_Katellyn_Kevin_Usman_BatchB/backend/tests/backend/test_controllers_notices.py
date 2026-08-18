def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_notices_public(client):
    response = client.get("/api/v1/notices")
    assert response.status_code == 200
    assert response.json() == []


def test_create_notice_without_auth(client):
    response = client.post(
        "/api/v1/notices",
        json={"title": "A", "content": "B", "category": "Announcement"},
    )
    assert response.status_code in (401, 403)


def test_create_notice_with_jwt(client):
    token = _login(client, "jane.doe@example.com", "password")
    response = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "JWT notice", "content": "from jane", "category": "General"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["author"] == "Jane Doe"
    assert body["author_id"] == 2
    assert body["title"] == "JWT notice"
    assert body["category"] == "General"


def test_create_notice_empty_content(client):
    token = _login(client, "jane.doe@example.com", "password")
    response = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Blank", "content": "  ", "category": "Other"},
    )
    assert response.status_code in (400, 422)


def test_get_notice_by_id(client):
    token = _login(client, "jane.doe@example.com", "password")
    created = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "One", "content": "Body", "category": "Event"},
    ).json()
    response = client.get(f"/api/v1/notices/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "One"


def test_get_missing_notice_returns_404(client):
    response = client.get("/api/v1/notices/999")
    assert response.status_code == 404


def test_put_as_non_owner_returns_403(client):
    jane = _login(client, "jane.doe@example.com", "password")
    created = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {jane}"},
        json={"title": "Mine", "content": "Body", "category": "General"},
    ).json()
    jim = _login(client, "jim.doe@example.com", "password")
    response = client.put(
        f"/api/v1/notices/{created['id']}",
        headers={"Authorization": f"Bearer {jim}"},
        json={"title": "Hacked"},
    )
    assert response.status_code == 403


def test_put_as_owner(client):
    jane = _login(client, "jane.doe@example.com", "password")
    created = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {jane}"},
        json={"title": "Mine", "content": "Body", "category": "General"},
    ).json()
    response = client.put(
        f"/api/v1/notices/{created['id']}",
        headers={"Authorization": f"Bearer {jane}"},
        json={"title": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_delete_as_non_owner_returns_403(client):
    jane = _login(client, "jane.doe@example.com", "password")
    created = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {jane}"},
        json={"title": "Mine", "content": "Body", "category": "General"},
    ).json()
    jim = _login(client, "jim.doe@example.com", "password")
    response = client.delete(
        f"/api/v1/notices/{created['id']}",
        headers={"Authorization": f"Bearer {jim}"},
    )
    assert response.status_code == 403


def test_delete_as_admin(client):
    jane = _login(client, "jane.doe@example.com", "password")
    created = client.post(
        "/api/v1/notices",
        headers={"Authorization": f"Bearer {jane}"},
        json={"title": "Mine", "content": "Body", "category": "General"},
    ).json()
    admin = _login(client, "admin@example.com", "admin123")
    response = client.delete(
        f"/api/v1/notices/{created['id']}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": created["id"]}
