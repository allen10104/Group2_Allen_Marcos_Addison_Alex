"""
Environment-driven configuration for the API.

Read once at import time so a missing required variable (JWT_SECRET)
fails fast at cold start instead of on the first request.
"""

import os

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

# Comma-separated usernames granted admin permissions: edit/delete any
# notice, and pin/unpin any notice. Set via the ADMIN_USERNAMES env var.
ADMIN_USERNAMES = {u.strip() for u in os.environ.get("ADMIN_USERNAMES", "").split(",") if u.strip()}
