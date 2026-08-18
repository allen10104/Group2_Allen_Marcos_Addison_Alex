"""Authentication primitives: password hashing and JSON Web Tokens.

    password.py     bcrypt hash / verify - the only module that touches a raw password.
    jwt_service.py  mint and verify tokens; the signature is what makes claims safe.
    deps.py         get_current_user / require_admin, the FastAPI dependencies a route
                    declares in order to protect itself.

WHY DEPENDENCIES RATHER THAN MIDDLEWARE: middleware runs on every request, including
/docs and /api/health, so it needs a path-exclusion list that rots as routes are added.
A dependency is declared per route, which makes the requirement visible in the function
signature and puts a padlock beside that route in /docs automatically.

AUTHENTICATION (who are you) lives here. AUTHORIZATION (what may you do) is split on
purpose: gates that are about HTTP live in deps.py (require_admin returns 403), while
rules about the notices themselves live in NoticeService._assert_may_modify.
"""
