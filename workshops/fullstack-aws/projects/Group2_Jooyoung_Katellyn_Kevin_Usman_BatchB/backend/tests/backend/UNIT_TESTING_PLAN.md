# Notice Board Backend — Unit Testing Plan

Scope: everything under `Group2_.../backend/` built so far.  
Goal: prove each layer’s rules in isolation, then thin HTTP checks with `TestClient`.

**Stack:** `pytest`, FastAPI `TestClient`, in-memory repo or mocks (no live Supabase in unit tests).

---

## Principles

| Principle | Practice |
|---|---|
| One layer at a time | Unit-test models/auth/service/repo; mock the dependency below |
| No real DB in unit tests | Use `InMemoryNoticeRepository` or a fake; optional separate integration suite for Postgres |
| Deterministic auth | Set `JWT_SECRET` / `JWT_EXPIRE_MINUTES` in tests; do not rely on `.env` secrets |
| Arrange–Act–Assert | Clear setup, one behavior under test, explicit expects |
| Name by behavior | `test_create_notice_stamps_author_from_actor` |

---

## Component map → test files

| Component | Module | Suggested test file | Style |
|---|---|---|---|
| Category | `models/category.py` | (covered via Notice tests) | enum values |
| Notice | `models/notice.py` | `test_models_notice.py` | pure unit |
| User | `models/user.py` | `test_models_user.py` | pure unit |
| Password hashing | `auth/passwords.py` | `test_passwords.py` | pure unit |
| JWT helpers | `auth/jwt_utils.py` | `test_jwt_utils.py` | pure unit |
| In-memory repo | `repositories/notice_repository.py` | `test_notice_repository.py` | pure unit |
| Postgres repo | `repositories/postgres_notice_repository.py` | `test_postgres_notice_repository.py` | **integration only** (optional) |
| NoticeService | `services/notice_service.py` | `test_notice_service.py` | unit + fake repo |
| Auth deps / stubs | `dependencies.py` | `test_auth_dependencies.py` | unit |
| Auth routes | `controllers/auth.py` | `test_controllers_auth.py` | API (TestClient) |
| Notice routes | `controllers/notices.py` | `test_controllers_notices.py` | API (TestClient) |
| App wiring | `main.py` | `test_main.py` | smoke |

---

## Priority

- **P0 — must have:** Notice validation, User.`can_modify`, NoticeService CRUD + authz, passwords, JWT, login + protected routes  
- **P1 — should have:** InMemory repo, filters on `list_notices`, schema/`notice_to_out`, HTTP status mapping  
- **P2 — nice to have:** Postgres integration tests, expire-token edge cases, OpenAPI smoke  

---

## Shared fixtures (`conftest.py`)

Plan to provide:

```python
# examples — implement when writing tests
@pytest.fixture
def alice(): ...          # User id=1, not admin
@pytest.fixture
def bob(): ...            # User id=2, not admin
@pytest.fixture
def admin(): ...          # User is_admin=True
@pytest.fixture
def repo(): ...           # InMemoryNoticeRepository()
@pytest.fixture
def service(repo): ...    # NoticeService(repo)  — do not use the process singleton
@pytest.fixture
def client(service): ...  # TestClient with dependency overrides / patched notice_service
```

**Important:** `notice_service` in `notice_service.py` is a process singleton wired to Postgres. For unit tests, construct `NoticeService(InMemoryNoticeRepository())` locally, or patch `backend.controllers.notices.notice_service`.

Set env for JWT tests:

```python
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
```

Reload or import jwt helpers after setting env if values are read at import time.

---

## 1. `Category` (`models/category.py`) — P1

| ID | Case | Expect |
|---|---|---|
| C1 | Enum members | `ANNOUNCEMENT`, `EVENT`, `GENERAL`, `OTHER` exist |
| C2 | `Category("Announcement")` | succeeds |
| C3 | `Category("not-a-category")` | raises `ValueError` |

---

## 2. `Notice` (`models/notice.py`) — P0

| ID | Case | Expect |
|---|---|---|
| N1 | Valid construct | fields set; `author` / `author_id` are `None` until stamped |
| N2 | Empty / whitespace title | `ValueError` (“Title is required”) |
| N3 | Empty / whitespace content | `ValueError` (“Content is required”) |
| N4 | Content longer than `MAX_CONTENT_LENGTH` | `ValueError` |
| N5 | Non-`Category` category | `ValueError` |
| N6 | Title/content stripped | leading/trailing spaces removed |
| N7 | Equality | same `id` → equal; different `id` → not equal |
| N8 | Equality with non-Notice | `False` |
| N9 | `validate` callable standalone | same rules as `__init__` |

---

## 3. `User` (`models/user.py`) — P0

| ID | Case | Expect |
|---|---|---|
| U1 | Construct with `password_hash` | attributes set |
| U2 | `can_modify` own notice | `True` |
| U3 | `can_modify` other user’s notice | `False` |
| U4 | Admin `can_modify` any notice | `True` |

---

## 4. Passwords (`auth/passwords.py`) — P0

| ID | Case | Expect |
|---|---|---|
| P1 | `hash_password` | returns bcrypt string (not plaintext) |
| P2 | Same password hashed twice | hashes differ (salt) but both verify |
| P3 | `verify_password` correct | `True` |
| P4 | `verify_password` wrong | `False` |
| P5 | Invalid hash string | `False` (no crash) |

---

## 5. JWT (`auth/jwt_utils.py`) — P0

| ID | Case | Expect |
|---|---|---|
| J1 | `create_access_token` | returns non-empty string |
| J2 | Decode round-trip | `sub`, `email`, `is_admin` match |
| J3 | Tampered token | decode raises |
| J4 | Wrong secret | decode raises |
| J5 | Expired token | decode raises (`exp` in the past) |

---

## 6. `InMemoryNoticeRepository` — P1

| ID | Case | Expect |
|---|---|---|
| R1 | `next_id` | increments 1, 2, 3… |
| R2 | `add` + `get` | returns same notice by id |
| R3 | `get` missing | `None` |
| R4 | `list_all` | all added notices; copy not live alias of internals (mutate return safely) |
| R5 | `update` existing | fields persisted for next `get` |
| R6 | `update` missing | `ValueError` (“Notice not found”) |
| R7 | `delete` | subsequent `get` is `None` |
| R8 | Seed via constructor `notices=[...]` | `_next_id` continues after max id |

---

## 7. `PostgresNoticeRepository` — P2 (integration)

Skip in default unit CI. Mark `@pytest.mark.integration` and require `DATABASE_URL`.

| ID | Case | Expect |
|---|---|---|
| PG1 | Connect + `_ensure_table` | no error |
| PG2 | add → get → update → delete | round-trip |
| PG3 | `next_id` unique | no PK collision on add |

Use a disposable schema/table or cleanup in `finally`.

---

## 8. `NoticeService` — P0 / P1

Inject `InMemoryNoticeRepository`. Do **not** call the module singleton.

| ID | Case | Expect |
|---|---|---|
| S1 | `create_notice` | assigns id; stamps `author` / `author_id` from actor |
| S2 | `create_notice` default date | today’s ISO date when `notice_date` omitted |
| S3 | `create_notice` invalid title/content | `ValueError` from `Notice` |
| S4 | `get_notice` existing | returns notice |
| S5 | `get_notice` missing | `ValueError` “Notice not found” |
| S6 | `update_notice` by owner | fields change; repo updated |
| S7 | `update_notice` by other user | `ValueError` “not authorized” |
| S8 | `update_notice` by admin | succeeds |
| S9 | `update_notice` unknown fields | `ValueError` “Cannot update fields” |
| S10 | `delete_notice` by owner | removed |
| S11 | `delete_notice` by other | not authorized |
| S12 | `delete_notice` by admin | removed |
| S13 | `list_notices` order | newest id first |
| S14 | filter `author_id` | only that author |
| S15 | filter `author` substring | case-insensitive match |
| S16 | filter `category` | enum equality |
| S17 | filter `q` | matches title or content |

---

## 9. Auth dependencies (`dependencies.py`) — P0

| ID | Case | Expect |
|---|---|---|
| D1 | `authenticate_user` valid Jane | returns user id 2 |
| D2 | Wrong password | `None` |
| D3 | Unknown email | `None` |
| D4 | `create_token_for_user` + `get_current_user` | resolves same user (call dependency with fake credentials or decode path) |
| D5 | `get_current_user` bad token | HTTP 401 |

For D4/D5, either unit-test the helpers used inside `get_current_user`, or use `TestClient` on `/auth/me`.

---

## 10. Auth controller (`controllers/auth.py`) — P0

| ID | Case | Expect |
|---|---|---|
| A1 | `POST /api/v1/auth/login` good creds | 200; `access_token` + `token_type=bearer` |
| A2 | Bad password | 401 |
| A3 | `GET /api/v1/auth/me` with Bearer | 200; email/id match |
| A4 | `/me` without token | 401/403 |
| A5 | `/me` with garbage token | 401 |

---

## 11. Notice controller (`controllers/notices.py`) — P0 / P1

Patch service to in-memory before requests (or override app dependency if you later inject via `Depends`).

| ID | Case | Expect |
|---|---|---|
| H1 | `GET /` health | 200 `{"status":"ok"}` |
| H2 | `GET /api/v1/notices` public | 200 list (no auth) |
| H3 | `POST /api/v1/notices` no auth | 401/403 |
| H4 | `POST` with valid JWT | 201; body matches `NoticeOutSchema`; author stamped |
| H5 | `POST` empty content | 400 or 422 |
| H6 | `GET /api/v1/notices/{id}` | 200 |
| H7 | `GET` missing id | 404 |
| H8 | `PUT` as non-owner | 403 |
| H9 | `PUT` as owner | 200; title updated |
| H10 | `DELETE` as non-owner | 403 |
| H11 | `DELETE` as admin | 200 `{"deleted": id}` |
| H12 | `GET /api/v1/notices?q=...` | filtered subset |
| H13 | `GET ...?author_id=` | filtered |
| H14 | `GET ...?category=Event` | filtered |
| H15 | Invalid category on create | 422 (Pydantic) |

---

## 12. Schemas (`schemas/notice.py`, `schemas/auth.py`) — P1

| ID | Case | Expect |
|---|---|---|
| SC1 | `notice_to_out` | `category` is `.value` string; `date` is str; author fields present |
| SC2 | `NoticeCreateSchema` rejects bad category | validation error |
| SC3 | `NoticeUpdateSchema` all-optional | empty update allowed by schema |
| SC4 | `LoginRequest` requires email + password | validation error if missing |

---

## 13. `main.py` smoke — P1

| ID | Case | Expect |
|---|---|---|
| M1 | App imports | `app` exists; routes include `/api/v1/auth/login` and `/api/v1/notices` |
| M2 | OpenAPI | `/openapi.json` 200 |

---

## Suggested implementation order

1. `conftest.py` fixtures (users, in-memory repo, service)  
2. Models + passwords + JWT (no FastAPI)  
3. InMemory repository  
4. NoticeService  
5. Auth + notice controllers with `TestClient`  
6. Optional Postgres integration mark  

---

## Out of scope (for now)

- Frontend / React tests  
- Terraform / CI deploy tests  
- Load / security penetration tests  
- Real email delivery  

---

## Definition of done

- [ ] P0 cases automated under `tests/backend/`  
- [ ] `pytest tests/backend -v` passes without `DATABASE_URL`  
- [ ] Controllers covered for 401 / 403 / 404 / 201 happy paths  
- [ ] No plaintext password assertions against stored user hashes  
