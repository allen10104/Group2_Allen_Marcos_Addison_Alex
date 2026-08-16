# Research Findings

Research pulled from current (2026) sources on the four technology
decisions this project rests on. Each section: what the guidance says,
what we did, and whether the gap (if any) is acceptable for this
project's scope.

## 1. FastAPI on Lambda via Mangum

**Guidance:** Treat Lambda as a transport layer, not a host — Mangum
converts the API Gateway event into an ASGI call, FastAPI handles
routing/validation as normal, and the response gets converted back.
No Uvicorn process runs in Lambda; AWS invokes the `handler` object
directly. Since our app has no startup/shutdown work, the lifespan
protocol should be turned off explicitly (`Mangum(app, lifespan="off")`)
rather than left at its default, to avoid Mangum waiting on lifespan
events that never resolve. Cold starts are the main perf tax — keep
dependencies minimal, since Lambda reimports everything fresh on a
cold start.

**What we did:** `app.py` builds `handler = Mangum(app, lifespan="off")`,
matching current guidance since we have no startup/shutdown handlers,
and payload format 2.0 (HTTP API) end to end. Dependency set is
already minimal (fastapi, mangum, psycopg2-binary, pyjwt, bcrypt,
pydantic) — all resolve to prebuilt manylinux wheels, so no compile
step slows down cold starts.

**Gap:** none remaining for this item.

## 2. JWT authentication

**Guidance (RFC 8725 / current practice):** short-lived access tokens
(5–15 minutes) paired with longer-lived, server-tracked refresh
tokens; HttpOnly cookies over `localStorage` for storage (localStorage
is readable by any script on the page, so a single XSS bug leaks every
session); RS256/ES256 signing over HS256 where multiple services need
to verify tokens; never put secrets/PII in the payload (it's
base64url, not encrypted); a revocation strategy (deny-list by `jti`,
or just let short expiry do the work).

**What we did:** single HS256-signed access token, 60-minute expiry,
no refresh token, stored in `localStorage`. This is the simplest JWT
implementation that satisfies "logged-in users can post/delete,
everyone can read" — appropriate for a class assignment with one
backend service and no sensitive data in notices.

**Gap, ranked by how much it'd matter here:**
1. `localStorage` storage is XSS-exposed. For a toy app with no PII
   and no payment/session-hijacking stakes, this is acceptable; flagged
   in `04-security-plan.md` as the thing to fix first if this app ever
   handled real user data.
2. No refresh token — the assignment's usage pattern (post, walk away,
   come back later) means users will just have to log in again after an
   hour. Not adding refresh-token complexity for this scope.
3. HS256 is fine here since Lambda is the only party that ever verifies
   a token — RS256 only matters once multiple independent services
   need to verify without sharing a secret.

## 3. GitHub Actions → AWS authentication

**Guidance:** OIDC (federated, short-lived STS credentials requested
per workflow run) has become the standard recommendation over static
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets, because static
keys don't expire on their own, get reused across workflows, and
persist indefinitely if leaked.

**What we did:** the assignment brief explicitly specifies static
access-key secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), so
that's what `deploy.yml` uses. This is a deliberate scope match to the
assignment's stated requirements, not an oversight.

**Recommended follow-up (optional, not required by the assignment):**
swap to OIDC — create an `aws_iam_openid_connect_provider` +
assume-role trust policy scoped to this repo/branch, replace
`aws-actions/configure-aws-credentials`'s key-based inputs with
`role-to-assume`, and delete the two key secrets. See
`05-risks-and-open-items.md` for the concrete migration note.

## 4. Terraform state management

**Guidance:** local state (the default, and what we're using) is fine
solo but has no locking, no encryption at rest beyond the filesystem,
and no history — a remote S3 backend with state locking is standard
for anything beyond a single person's laptop. As of Terraform 1.10,
S3-native locking (`use_lockfile = true` in the backend block)
replaces the older DynamoDB-table locking pattern, which is deprecated
as of Terraform 1.11.

**What we did:** local state (default `terraform.tfstate` on disk,
gitignored). Matches the assignment's single-student, single-machine
usage pattern — no team collaboration to protect against.

**Recommended follow-up (optional):** if this project ever needs to
survive a laptop wipe or be shared, move to an S3 backend with
`use_lockfile = true` (not the older DynamoDB-table pattern) — see
`05-risks-and-open-items.md`.
