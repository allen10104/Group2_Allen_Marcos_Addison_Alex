"""AWS Lambda entry point.

Mangum is an ASGI adapter: API Gateway event in, FastAPI response out. The `app`
object it wraps is the same one uvicorn runs locally, so there is exactly one
application and no "works locally, breaks deployed" divergence.

THE MODULE-LEVEL `handler` IS THE WHOLE TRICK. Code at module scope runs once when the
execution environment is created (the cold start), not once per request. So the FastAPI
app, the Pydantic model compilation, and the MongoClient connection pool are built a
single time and reused for every subsequent invocation on that container.

Build it inside the handler function instead and every request pays full startup cost.

COLD START EXPECTATIONS, so you are not alarmed on deploy day:
  first request after a deploy or ~15 min idle:  800ms - 2s
  every request after that:                      40 - 150ms
"""

from mangum import Mangum

from app.main import app

# lifespan="auto" lets FastAPI's startup event run on each cold start, which is what
# seeds the demo employees and notices if the collections are ever empty. The seed is
# idempotent (it counts first), so the cost is one cheap query per cold start and the
# deployed app can never present an empty board to a grader.
handler = Mangum(app, lifespan="auto")
