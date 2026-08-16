# Architecture Decisions

Concrete decisions made while building this project, why, and what
else was considered.

## D1. Single Lambda running a full FastAPI app, not per-route Lambdas

**Decision:** one Lambda function, one FastAPI app with 5 routes
(`/auth/register`, `/auth/login`, `/notices` GET/POST,
`/notices/{id}` DELETE), API Gateway proxies everything to it via a
single `ANY /{proxy+}` route.

**Alternative considered:** one Lambda per endpoint (classic
"Lambda-lith avoidance" pattern), with API Gateway routing each method
to its own function.

**Why this way:** the assignment scopes a single Python backend
Lambda from Tier 1 onward. Per-route Lambdas would mean 5x the cold
starts to reason about, 5x the IAM/env-var wiring, and no meaningful
benefit at this traffic scale — FastAPI's internal router already
gives clean route separation in code without the operational
overhead. This is the right call for an app this size; it stops being
the right call once individual routes have wildly different scaling
or memory needs.

## D2. Auth model: public read, JWT-gated write

**Decision:** `GET /notices` requires no token; `POST /notices` and
`DELETE /notices/{id}` require a valid bearer token. Any authenticated
user can delete any notice — no per-notice ownership check.

**Alternative considered:** (a) everything behind auth, including
reads; (b) ownership-scoped deletes (only the author can delete their
own notice).

**Why this way:** (a) was rejected — a notice board that requires
login just to *look at it* defeats the point of a public board. (b)
was deliberately left out: the assignment never specified an ownership
model, and adding one means deciding what happens to anonymous vs.
un-authored legacy notices, admin overrides, etc. — scope not asked
for. Flagged explicitly in the README and in
`05-risks-and-open-items.md` so it's a visible decision, not a silent
gap.

## D3. Tier progression via Terraform variables, not separate configs

**Decision:** one Terraform codebase for all 4 tiers, gated by
`enable_cloudfront` and `enable_observability` booleans using
resource-level `count`, rather than 4 separate Terraform directories
or branches.

**Alternative considered:** a `terraform/tier1/`, `terraform/tier2/`,
... directory per tier, each a superset of the last.

**Why this way:** duplicated directories drift — a fix made in
`tier3/main.tf` has to be manually ported to `tier4/main.tf` or the
grader sees inconsistent behavior between tiers. A single codebase
with toggles means `terraform apply -var="enable_cloudfront=true"` is
the entire Tier 3 upgrade, and the state history shows the literal
progression the assignment describes. Trade-off: the `.tf` files are
denser (more `count = var.x ? 1 : 0` and `dynamic` blocks) than a
naive per-tier copy would be — acceptable given the alternative's
maintenance cost.

## D4. Table creation: app-managed (`CREATE TABLE IF NOT EXISTS`), not a migration tool

**Decision:** `ensure_tables()` runs on every request and
idempotently creates `users`/`notices` if missing. No Alembic, no
separate migration step in the deploy pipeline.

**Alternative considered:** Alembic migrations run as a GitHub Actions
step before the Lambda code deploy.

**Why this way:** two tables, no foreign keys, no schema evolution
expected during the assignment's lifetime. A migration tool earns its
keep once there's a second developer or a schema that actually
changes over time — introducing one here would be solving a problem
this project doesn't have yet. Explicitly called out as something to
revisit if the schema grows (see `05-risks-and-open-items.md`).

## D5. `psycopg2` (sync) over an async driver

**Decision:** synchronous `psycopg2` calls inside FastAPI's sync route
handlers (not `async def`), despite FastAPI being an async framework.

**Alternative considered:** `asyncpg` or `psycopg[async]` with
`async def` routes, matching the "use async DB clients to reduce I/O
bottlenecks" guidance found during research.

**Why this way:** each Lambda invocation handles exactly one request
at a time — there's no concurrent-request-per-invocation scenario for
async I/O to help with here (that benefit shows up under Uvicorn
serving many concurrent connections on one process, which is not our
deployment model). `psycopg2-binary` also has a simpler, more battle-
tested Lambda packaging story than the async alternatives. Worth
revisiting only if this ever moves off Lambda onto a long-running
server process.
