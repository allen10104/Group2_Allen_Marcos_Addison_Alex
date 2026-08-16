# Implementation Plan

Tier-by-tier task list. Status reflects what's already built and
verified vs. what's left to run against real AWS (everything so far
has been built and tested locally — Lambda packaging verified, FastAPI
routes verified against a real local Postgres, frontend build
verified — but nothing has been deployed to an actual AWS account yet).

## Tier 1 — Manual deploy

| Task | Status |
|---|---|
| `backend/app.py` — FastAPI app, JWT auth, notice CRUD | ✅ Built, tested locally against real Postgres |
| `backend/build.py` — packages `app.py` + deps for Lambda | ✅ Built, verified produces a valid manylinux-wheel zip |
| `terraform/main.tf` — S3, Lambda, API Gateway, IAM role | ✅ Written, HCL-parses cleanly |
| `terraform/variables.tf` / `outputs.tf` | ✅ Written |
| `frontend/` — React app (public board, login-gated write) | ✅ Built, `npm run build` verified clean |
| Set `lifespan="off"` on the Mangum handler explicitly | ✅ Done — re-verified against real Postgres |
| Run `terraform apply` against a real AWS account | ⬜ Not yet done — needs `terraform.tfvars` with real `pg_host`/`jwt_secret` |
| Confirm EC2 Postgres security group allows Lambda's egress (or configure `lambda_vpc_*` vars if it's VPC-only) | ⬜ Depends on how the EC2 instance from the prior lab is networked — unresolved, see `05-risks-and-open-items.md` |
| Upload frontend build to S3, confirm end-to-end in a browser | ⬜ Blocked on the above |

## Tier 2 — GitHub Actions

| Task | Status |
|---|---|
| `.github/workflows/deploy.yml` | ✅ Written, YAML-validated |
| Repo secrets configured (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `LAMBDA_FUNCTION_NAME`, `S3_BUCKET`, `VITE_API_URL`) | ⬜ Needs a real repo + Tier 1 outputs |
| Create a scoped IAM deploy user (not root/admin) | ⬜ Not yet created — least-privilege policy documented in README but not yet applied |
| Confirm push-to-`main` triggers a clean run | ⬜ Blocked on the above |

## Tier 3 — CloudFront

| Task | Status |
|---|---|
| `terraform/cloudfront.tf` — OAC + distribution, gated by `enable_cloudfront` | ✅ Written, HCL-parses cleanly |
| S3 bucket policy swap (public → OAC-only) wired via `enable_cloudfront` | ✅ Written |
| SPA fallback (403/404 → `/index.html`) | ✅ Written |
| `CLOUDFRONT_DISTRIBUTION_ID` secret + invalidation step in workflow | ✅ Written |
| Apply with `enable_cloudfront=true`, confirm HTTPS + direct-S3 403 | ⬜ Blocked on Tier 1/2 being live first |

## Tier 4 — Observability (stretch)

| Task | Status |
|---|---|
| `terraform/observability.tf` — 2 log groups, 2 alarms, dashboard, 2 saved queries, gated by `enable_observability` | ✅ Written, HCL-parses cleanly |
| API Gateway JSON access logging wired into the stage | ✅ Written |
| README note on importing the auto-created Lambda log group | ✅ Written |
| Apply with `enable_observability=true` | ⬜ Blocked on Tier 3 being live first |
| Fault-injection test (`PG_HOST` → unreachable, confirm alarms fire, then revert) | ⬜ Not yet run — requires a live deployment |

## Cross-cutting / not tied to one tier

| Task | Status |
|---|---|
| Postman collection (`postman/notice-board.postman_collection.json`) | ✅ Built, JSON-validated |
| End-to-end local test: register → login → post → list → delete, against real Postgres | ✅ All assertions passed |
| README with exact commands per tier | ✅ Written |
