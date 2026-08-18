"""API tests through FastAPI's TestClient.

TestClient sends real requests through the real ASGI app - routing, Pydantic
validation, and the exception handlers all execute - over an in-process transport, so
no socket and no server.

The dependency overrides are the key move: the app is wired to Mongo via .env, and we
swap in the in-memory repository and a fixed identity for the test. That is FastAPI's
DI paying off - no monkeypatching, no environment juggling.

SECURITY MODEL UNDER TEST: reads are public, writes require a token. That is what lets
an anonymous visitor hitting the deployed S3/CloudFront URL see the board immediately,
which is the Tier 1 acceptance criterion, while still preventing anyone from posting.
"""

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_notice_repository
from app.domain.enums import Role
from app.main import app
from app.repositories.memory import InMemoryNoticeRepository
from app.schemas.auth import CurrentUser
from app.security.deps import get_current_user

# The identity a test request arrives with - same shape the real dependency builds from
# a decoded token, so a test cannot pass while production rejects.
TEST_USER = CurrentUser(
    username="p.raman", employee_id="E10001", full_name="Priya Raman",
    department="COMPLIANCE", roles=[Role.MANAGER],
)


@pytest.fixture
def client():
    """Authenticated client - the default for write tests.

    WHY OVERRIDE INSTEAD OF MINTING A REAL TOKEN? These tests are about ROUTING and
    CONTRACTS, not cryptography. A real JWT would couple every API test to the signing
    key and to clock behaviour. The token itself is tested in test_jwt.py."""
    repo = InMemoryNoticeRepository()
    app.dependency_overrides[get_notice_repository] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    with TestClient(app) as c:
        yield c
    # Always clear, or overrides leak into the next test file and you lose an hour to a
    # "passes alone, fails in the suite" mystery.
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    """No auth override - the REAL dependency runs. Reads succeed, writes 401."""
    repo = InMemoryNoticeRepository()
    app.dependency_overrides[get_notice_repository] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------- public: anyone can read ----------------

def test_board_is_public(anon_client):
    """Reading the board needs no token - that is what makes the deployed site show
    content to an anonymous visitor."""
    r = anon_client.get("/api/notices")
    assert r.status_code == 200


def test_single_notice_is_public(anon_client):
    """Whatever get_board allows, get_one must allow too - otherwise a shared link to
    a notice 401s while the list renders fine.

    404 (not found), NOT 401 - proves the request got past auth into the handler."""
    r = anon_client.get("/api/notices/000000000000000000000000")
    assert r.status_code == 404


def test_health_is_public(anon_client):
    """Health must stay unauthenticated - it is what tells you on deploy day whether
    the Lambda is even starting."""
    assert anon_client.get("/api/health").status_code == 200


# ---------------- protected: writes need a token ----------------

def test_create_requires_authentication(anon_client):
    """THE security assertion. With reads open, this is the boundary that matters:
    anyone can look, only an authenticated employee can post."""
    r = anon_client.post("/api/notices", json={"title": "x", "body": "y"})
    assert r.status_code == 401
    # Our ApiError shape, not FastAPI's default {"detail": ...} - proves the
    # StarletteHTTPException handler is wired up.
    assert r.json()["status"] == 401
    assert r.json()["error"] == "Unauthorized"


def test_delete_requires_authentication(anon_client):
    r = anon_client.delete("/api/notices/000000000000000000000000")
    assert r.status_code == 401


# ---------------- authenticated behaviour ----------------

def test_get_board_returns_derived_fields(client):
    r = client.get("/api/notices")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 1
    # Proves NoticeResponse.from_domain computed the derived fields - the frontend
    # depends on these and nothing else would catch a regression.
    assert "category_label" in body[0]
    assert "acknowledgement_required" in body[0]


def test_create_returns_201_with_location(client):
    r = client.post("/api/notices", json={
        "title": "Sanctions list updated",
        "body": "Rescreen all accounts opened in the last 30 days.",
        "category": "COMPLIANCE", "priority": "URGENT",
    })
    assert r.status_code == 201
    assert r.headers["Location"].startswith("/api/notices/")
    assert r.json()["category_label"] == "Compliance & Regulatory"


def test_author_comes_from_token_not_body(client):
    """The body tries to claim a different author. It must be ignored - a client that
    could set author_employee_id could post as the Chief Compliance Officer.
    NoticeCreate has no such field, so Pydantic discards it; this pins that."""
    r = client.post("/api/notices", json={
        "title": "Posted by Priya", "body": "Author must come from the token.",
        "author_employee_id": "E99999", "author_name": "Chief Compliance Officer",
    })
    assert r.status_code == 201
    assert r.json()["author_employee_id"] == "E10001"
    assert r.json()["author_name"] == "Priya Raman"


def test_blank_title_returns_400_with_field_errors(client):
    r = client.post("/api/notices", json={"title": "   ", "body": "Body"})
    assert r.status_code == 400
    assert "title" in r.json()["field_errors"]


def test_bad_enum_is_rejected(client):
    r = client.post("/api/notices", json={
        "title": "Test", "body": "Body", "category": "NONSENSE",
    })
    assert r.status_code == 400


def test_missing_returns_404_in_api_error_shape(client):
    r = client.get("/api/notices/000000000000000000000000")
    assert r.status_code == 404
    assert r.json()["status"] == 404
    assert r.json()["error"] == "Not Found"


def test_delete_returns_204_and_removes_from_board(client):
    created = client.post("/api/notices", json={
        "title": "Temporary notice", "body": "Will be archived.",
    }).json()

    assert client.delete(f"/api/notices/{created['id']}").status_code == 204

    remaining = [n["id"] for n in client.get("/api/notices").json()]
    assert created["id"] not in remaining
    