# Security Plan

A plain review of where this system's security posture stands today,
and what "hardened" would look like, so the gap is a documented
decision rather than an unexamined default.

## Authentication

| Aspect | Current | Hardened alternative | Verdict for this project |
|---|---|---|---|
| Token storage | `localStorage` | HttpOnly cookie | Accept current — no PII/payment data at stake, and cookies would require CSRF handling that adds complexity disproportionate to the app |
| Token lifetime | 60 min, no refresh | 5–15 min + refresh token rotation | Accept current — re-login after an hour is a fine UX cost here |
| Signing algorithm | HS256 (shared secret) | RS256/ES256 (asymmetric) | Accept current — only one service (this Lambda) ever verifies tokens, so there's no benefit to asymmetric signing |
| Password hashing | bcrypt, default cost factor | bcrypt/argon2, tuned cost factor | Fine as-is; bcrypt's default work factor is still considered adequate in 2026 guidance |
| Revocation | None (token valid until natural expiry) | Deny-list by `jti`, or refresh-token family tracking | Accept current — 60-minute blast radius on a stolen token for a board with no sensitive data is a reasonable trade |
| Username/password transport | HTTPS only (via CloudFront from Tier 3 on; HTTP in Tier 1/2) | HTTPS always | **Real gap in Tier 1/2**: before CloudFront exists, login credentials cross the wire over the S3 website endpoint's plain HTTP. Acceptable only because Tier 1/2 are meant to be transient states on the way to Tier 3, not a resting state. |

## Secrets handling

| Aspect | Current | Notes |
|---|---|---|
| `JWT_SECRET`, `PG_PASSWORD` | Terraform variables, marked `sensitive = true`, passed as Lambda environment variables | Standard for a project this size. Environment variables are visible to anyone with `lambda:GetFunctionConfiguration` IAM access — acceptable for a single-student AWS account, would want AWS Secrets Manager + rotation in a real multi-tenant environment. |
| `terraform.tfvars` | Gitignored | Correct — never commit this file |
| GitHub Actions secrets | Static AWS access keys | Matches assignment spec; see `01-research-findings.md` §3 for the OIDC alternative if this were a real production pipeline |

## Infrastructure

| Aspect | Current | Notes |
|---|---|---|
| S3 bucket | Public in Tier 1/2, CloudFront-OAC-only from Tier 3 | Expected/intentional per the assignment's own tier design — not a gap, a staged rollout |
| Lambda IAM role | `AWSLambdaBasicExecutionRole` (+ VPC access role if `lambda_vpc_subnet_ids` set) | Least-privilege for what the function does (CloudWatch logs, optional VPC ENI management). No S3/DynamoDB/other AWS API access granted — correct, the function doesn't need it. |
| API Gateway | CORS `allow_origins = ["*"]` | Fine for a public API with no cookies/credentialed CORS requests. If cookie-based auth were adopted later (see token storage above), this would need to tighten to the actual frontend origin. |
| Database access | Lambda ↔ EC2 Postgres over the network path configured in `pg_host`/security groups | **Unresolved** — whether this is a public IP + security-group allowlist or private VPC-only access depends on how the EC2 instance was set up in the prior lab, which wasn't specified. See `05-risks-and-open-items.md`. |

## Application-level

| Aspect | Current | Notes |
|---|---|---|
| SQL injection | All queries use `psycopg2` parameterized queries (`%s` placeholders) | No string-formatted SQL anywhere — correct pattern used throughout |
| Input validation | Pydantic models (`RegisterRequest`, `LoginRequest`, `NoticeCreate`) enforce length bounds | `username` 3–50 chars, `password` 8–128 chars, `message` 1–2000 chars |
| Error messages | Generic ("Invalid username or password") rather than revealing which field was wrong | Correct — avoids username enumeration on login |
| Authorization model | Any authenticated user can delete any notice | Documented deliberate scope decision, not an oversight — see `02-architecture-decisions.md` D2 |
