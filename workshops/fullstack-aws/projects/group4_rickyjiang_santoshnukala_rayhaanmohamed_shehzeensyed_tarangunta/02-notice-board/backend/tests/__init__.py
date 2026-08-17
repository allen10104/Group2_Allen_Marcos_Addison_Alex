"""Test package marker.

Present so `tests` is a package and pytest import behaviour stays predictable whether
the suite is run from the repo root or from backend/. conftest.py does the actual
sys.path work that lets `from app...` resolve.

The suite is layered the same way the application is, fastest first:

    test_domain.py          pure entities - no I/O, sub-millisecond
    test_notice_service.py  business rules against the real in-memory repository
    test_jwt.py             tokens and password hashing: round-trip, tamper, expiry
    tests_api.py            the full HTTP surface through the FastAPI TestClient

NOTE: pytest only collects files matching `test_*.py`, so tests_api.py does NOT run
under a plain `pytest` invocation - rename it to test_api.py to include it.
"""
