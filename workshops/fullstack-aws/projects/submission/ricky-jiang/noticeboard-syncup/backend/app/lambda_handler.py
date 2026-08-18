# Lambda entry point. This is purely additive - the EC2 deployment (main.py,
# run via `uvicorn app.main:app`) is completely untouched by this file's
# existence. Mangum wraps the *same* FastAPI `app` object, including its
# existing lifespan (connect()/ensure_indexes()/disconnect() in database.py) -
# Mangum runs that lifespan's startup on cold start and reuses the resulting
# Motor client across warm invocations of the same execution environment,
# the same way the module-level _client/_db in database.py were always
# designed to be reused.
from mangum import Mangum

from app.main import app

handler = Mangum(app)
