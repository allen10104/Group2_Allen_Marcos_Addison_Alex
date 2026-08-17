# Notice Board (Bank) — Remaining Build & Deploy Stages

Derived from `ASSIGNMENT.md` plus a scan of this workspace on 16-Aug-2026.

> **Scope correction:** `ASSIGNMENT.md` says "You are given a working Notice Board
> application... You do not need to write frontend or backend code." That is not true for
> this group — no code is being handed out. **You build the whole thing from scratch**,
> then do the four deployment tiers. Stage 0 below is the part the assignment text omits.

---

## Where you actually are

| Thing needed | Status |
|---|---|
| `frontend/` React app | **Not started** |
| `backend/lambda_function.py` | **Not started** |
| `backend/requirements.txt` | Exists but wrong — has `fastapi/pymongo/PyJWT/bcrypt/mangum`, needs `pg8000` |
| `build.py` | **Not started** |
| `terraform/{main,variables,outputs}.tf` | **Not started** |
| `backend/app/**` skeleton | Empty `__init__.py` files left over from chapters 1–5 — not used by this app |
| PostgreSQL on EC2 | Unverified — confirm before Tier 1 |
| Local tooling | All present: Terraform 1.15.8, aws-cli 2.36.19, Node 24.19, Python 3.14 |

**Architecture reference in this repo:** `workshops/fullstack-aws/projects/01-task-tracker/`
is a complete working instance of the *same* architecture (Vite React → API Gateway HTTP
API → `pg8000` Lambda → PostgreSQL on EC2, with S3 + CloudFront Terraform). Read it when
you get stuck on wiring. Write your own app code; the Terraform/infra boilerplate is fair
to adapt — that is what the repo provides it for.

---

## Workspace-specific gotchas (do not skip)

1. **Your branch is `master`, not `main`.** Every `on: push: branches: [main]` in the
   assignment must be `[master]` for `github.com/snukala1234/noticeboard`.
2. **Your project is nested** under
   `workshops/fullstack-aws/projects/group4_.../02-notice-board/`. Put the workflow at the
   **repo root** `.github/workflows/` and use `working-directory:` or full paths. Give it a
   unique filename (e.g. `deploy-group4-notice-board.yml`) — that folder already holds
   other students' workflows.
3. **Tagging is enforced.** Per `workshops/fullstack-aws/README.md`, a nightly script
   deletes any resource missing `workshop=full-stack`, `autodelete=true`,
   `date=16-Aug-2026`. Use a provider `default_tags` block so every resource gets them.
4. **Naming prefix:** every resource must be `student-<slug>-notice-board-...`.
5. **Lambda IAM role is instructor-provided.** Pass it in as `lambda_role_arn`; do not
   create your own role.
6. **Local Python is 3.14, the Lambda runtime is 3.12.** Fine here because `pg8000` is
   pure Python. If you ever add a compiled dependency, build the zip on Linux or in CI.
7. **Never commit** `terraform.tfvars`, the DB password, or AWS keys. The `.gitignore`
   already covers `terraform.tfvars`, `*.zip`, `.terraform/`, `.venv/` — keep it that way.

---

# Stage 0 — Build the application

## 0.1 Clean up and fix dependencies

- Replace `backend/requirements.txt` with exactly `pg8000==1.31.2` — the FastAPI/Mongo
  stack is not used by a Lambda handler.
- Delete the unused `backend/app/**` package skeleton. Keep `backend/tests/` if you plan
  to write unit tests (worth doing — chapter 04 asks for `pytest`).

## 0.2 Write `backend/lambda_function.py`

A single-file Lambda handler for an API Gateway **HTTP API (payload format 2.0)** event.

- Read config from env: `PG_HOST`, `PG_PORT` (default 5432), `PG_DATABASE`
  (default `noticeboard`), `PG_USER`, `PG_PASSWORD`.
- `get_connection()` via `pg8000.native.Connection(..., timeout=5)`.
- `ensure_table(conn)` — idempotent `CREATE TABLE IF NOT EXISTS notices (id SERIAL PRIMARY
  KEY, name TEXT NOT NULL, message TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT
  now())`. Cache a module-level flag so it runs once per warm container.
- Route on `event["requestContext"]["http"]["method"]` and `event["rawPath"]`:

  | Method | Path | Behavior |
  |---|---|---|
  | `OPTIONS` | any | 200 + CORS headers (preflight) |
  | `GET` | `/notices` | 200, JSON array newest-first |
  | `POST` | `/notices` | 201, body `{ "name": "...", "message": "..." }` |
  | `DELETE` | `/notices/{id}` | 200 on delete, 404 if no such id |

- Validate input: reject empty/missing `name` or `message` with 400. Use **parameterized
  queries** (`conn.run("... :name", name=...)`) — never string-format SQL.
- Return `Access-Control-Allow-Origin: *` on every response, and serialize `created_at`
  with `.isoformat()`.
- Wrap the handler body in `try/except` returning 500 with the error message, and `print()`
  the request line — Tier 4 reads these logs.

## 0.3 Write `build.py`

Project-root script that packages the zip. Pattern (see
`01-task-tracker/build-lambda-pkg.py`):

1. Wipe and recreate `backend/_build/`
2. `pip install -r backend/requirements.txt -t backend/_build -q`
3. Copy `backend/lambda_function.py` into `backend/_build/`
4. Zip the contents (not the folder) to `backend/lambda.zip`, skipping `__pycache__`/`.pyc`

Verify: `python build.py` prints a zip path and a size.

## 0.4 Build the React frontend

```
npm create vite@latest frontend -- --template react
cd frontend && npm install
```

- `src/api.js` — base URL from `import.meta.env.VITE_API_URL`; export `getNotices()`,
  `createNotice({ name, message })`, `deleteNotice(id)`.
- Components: `NoticeForm.jsx` (name + message, clears on submit), `NoticeList.jsx`
  (fetch on mount via `useEffect`, loading + empty states), `NoticeCard.jsx` (name,
  message, formatted `created_at`, delete button).
- `App.jsx` holds the notices array in `useState` and re-fetches (or optimistically
  updates) after create/delete.
- Bank framing goes here: this is a **bank** notice board, so use banking language in the
  header/labels (branch announcements, teller notices, etc.). Chapter 01's domain notes
  give you the vocabulary.

Verify: `npm run dev` against the deployed API URL once Tier 1 is up.

## 0.5 PostgreSQL on EC2

Prerequisite for everything below. You need an EC2 instance with Postgres running, port
**5432** open in its security group, a `noticeboard` database, and a user + password.
Confirm from your laptop before touching Terraform:

```
psql -h <ec2-ip> -U <user> -d noticeboard -c "select 1"
```

---

# Stage 1 — Tier 1: Manual deployment

## 1.1 Write the Terraform

`terraform/main.tf`:

- `terraform { required_providers { aws ~> 5.0, random ~> 3.0 } }`
- `provider "aws"` with `region = var.aws_region` and a `default_tags` block carrying the
  three enforced tags
- `random_id.suffix` + `locals { name = "student-${var.student_name}-${var.project_name}-${random_id.suffix.hex}" }`
- **S3 (public website — Tier 1 only, you invert this in Tier 3):**
  `aws_s3_bucket`; `aws_s3_bucket_public_access_block` with all four `block_*` = **false**;
  `aws_s3_bucket_policy` allowing `s3:GetObject` to `Principal = "*"`;
  `aws_s3_bucket_website_configuration` with `index_document = "index.html"` and
  `error_document = "index.html"`
- **Lambda:** `runtime = "python3.12"`, `handler = "lambda_function.lambda_handler"`,
  `filename = "${path.module}/../backend/lambda.zip"`, `role = var.lambda_role_arn`,
  `timeout = 15`, and the five `PG_*` env vars
- **API Gateway:** `aws_apigatewayv2_api` (protocol `HTTP`, `cors_configuration` allowing
  `GET/POST/DELETE/OPTIONS`), `aws_apigatewayv2_integration` (`AWS_PROXY`,
  `payload_format_version = "2.0"`), `aws_apigatewayv2_route` with `route_key = "$default"`,
  `aws_apigatewayv2_stage` (`$default`, `auto_deploy = true`)
- `aws_lambda_permission` allowing `apigateway.amazonaws.com` on
  `"${aws_apigatewayv2_api.api.execution_arn}/*/*"`

`terraform/variables.tf`: `student_name` (regex-validated lowercase/hyphen),
`project_name` default `"notice-board"`, `aws_region` default `"us-east-1"`,
`postgres_host`, `postgres_port` (5432), `postgres_db` (`noticeboard`), `postgres_user`,
`postgres_password` (`sensitive = true`), `created_date`, `lambda_role_arn`.

`terraform/outputs.tf`: `website_url`, `api_url`, `s3_bucket`, `lambda_function_name`.
(You add `cloudfront_url` and `cloudfront_distribution_id` in Tier 3.)

## 1.2 Deploy

Put your values in `terraform/terraform.tfvars` (already gitignored) rather than retyping
`-var` flags:

```
student_name      = "<slug>"
created_date      = "16-Aug-2026"
postgres_host     = "<ec2-public-ip>"
postgres_user     = "<user>"
postgres_password = "<password>"
postgres_db       = "noticeboard"
lambda_role_arn   = "<instructor-provided-role-arn>"
```

```
python build.py
cd terraform
terraform init
terraform plan
terraform apply
terraform output
```

## 1.3 Ship the frontend

```
cd frontend
set VITE_API_URL=<api_url from terraform output>
npm run build
aws s3 sync dist/ s3://<bucket>/ --delete
```

(PowerShell: `$env:VITE_API_URL = "<api_url>"`. Vite bakes the value in at build time —
changing it later means rebuilding, not just re-uploading.)

## 1.4 Tier 1 acceptance

- [ ] S3 website URL renders the Notice Board UI
- [ ] Posting a notice persists to PostgreSQL and appears in the list
- [ ] Deleting a notice removes it
- [ ] All resources prefixed `student-<slug>-notice-board`
- [ ] All resources carry the three required tags

---

# Stage 2 — Tier 2: GitHub Actions

Create `.github/workflows/deploy-group4-notice-board.yml` **at the repo root**:

```yaml
name: Deploy Group4 Notice Board
on:
  push:
    branches: [master]                 # NOT main — your default branch is master
    paths:
      - "workshops/fullstack-aws/projects/group4_*/02-notice-board/**"
      - ".github/workflows/deploy-group4-notice-board.yml"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: group4-notice-board
  cancel-in-progress: true
```

Job steps (`runs-on: ubuntu-latest`):

1. `actions/checkout@v4`
2. `aws-actions/configure-aws-credentials@v4` with the three AWS secrets
3. **Backend:** `pip install -r <proj>/backend/requirements.txt -t <proj>/backend/_build -q`;
   copy `lambda_function.py` in; `cd <proj>/backend/_build && zip -r ../lambda.zip .`;
   `aws lambda update-function-code --function-name ${{ secrets.LAMBDA_FUNCTION_NAME }} --zip-file fileb://<proj>/backend/lambda.zip`
4. **Frontend:** `actions/setup-node@v4` (node 20) → `npm ci` → `npm run build` with
   `env: VITE_API_URL: ${{ secrets.VITE_API_URL }}` → `aws s3 sync dist/ s3://${{ secrets.S3_BUCKET }}/ --delete`

## Secrets to add (Settings → Secrets and variables → Actions)

`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` = `us-east-1`,
`LAMBDA_FUNCTION_NAME`, `S3_BUCKET`, `VITE_API_URL` — the last three come straight from
`terraform output`.

## Tier 2 acceptance

- [ ] Push to `master` triggers the workflow
- [ ] Workflow is green end to end
- [ ] App updates with zero manual AWS CLI commands

---

# Stage 3 — Tier 3: CloudFront

1. Add `aws_cloudfront_origin_access_control` — `origin_access_control_origin_type = "s3"`,
   `signing_behavior = "always"`, `signing_protocol = "sigv4"`
2. Add `aws_cloudfront_distribution` — origin is the bucket's
   `bucket_regional_domain_name` with `origin_access_control_id` attached;
   `default_root_object = "index.html"`; `viewer_protocol_policy = "redirect-to-https"`;
   allowed/cached methods `["GET","HEAD"]`; a `custom_error_response` mapping 404 → 200 →
   `/index.html` for SPA routing; `geo_restriction { restriction_type = "none" }`;
   `cloudfront_default_certificate = true`
3. **Flip** `aws_s3_bucket_public_access_block` — all four `block_*` back to `true`
4. **Replace** the bucket policy with the OAC form:
   `Principal = { Service = "cloudfront.amazonaws.com" }` plus
   `Condition.StringEquals."AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn`
5. Add `cloudfront_url` and `cloudfront_distribution_id` outputs, then `terraform apply`
6. Add repo secret `CF_DISTRIBUTION_ID`
7. Append after `s3 sync` in the workflow:
   `aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} --paths "/*"`

Note: your API Gateway is a different domain from the CloudFront domain, so keep
`allow_origins = ["*"]` on the API's CORS config (or narrow it to the CloudFront domain
once it exists). Distribution creation/propagation takes several minutes.

## Tier 3 acceptance

- [ ] App loads over HTTPS at the CloudFront URL
- [ ] Direct S3 website URL now returns 403
- [ ] Push to `master` invalidates the cache automatically

---

# Stage 4 — Tier 4 (optional): CloudWatch observability

1. `aws_cloudwatch_log_group.lambda`, name
   `/aws/lambda/${aws_lambda_function.api.function_name}`, `retention_in_days = 14`.
   It already exists from Tier 1, so import it once before applying:
   `terraform import aws_cloudwatch_log_group.lambda /aws/lambda/<fn>`
2. `aws_cloudwatch_log_group.apigw_access`, name `/aws/apigateway/${local.name}-access`,
   same retention
3. Add `access_log_settings { destination_arn, format = jsonencode({...}) }` to the
   `aws_apigatewayv2_stage` — requestId, ip, method, route, status, responseLength,
   integrationStatus, integrationLatency
4. `aws_cloudwatch_metric_alarm.lambda_errors` — `AWS/Lambda` / `Errors`, `Sum`,
   `period = 300`, `GreaterThanThreshold` 0, `treat_missing_data = "notBreaching"`,
   dimension `FunctionName`. No `alarm_actions` for this tier.
5. `aws_cloudwatch_metric_alarm.apigw_5xx` — `AWS/ApiGateway` / `5xx` (**lowercase**, that
   is the HTTP API metric) with dimension `ApiId`
6. `aws_cloudwatch_dashboard` — three widgets: Lambda (Invocations / Errors / p95
   Duration), API Gateway (Count / 4xx / 5xx / p95 Latency), CloudFront (Requests /
   4xxErrorRate / 5xxErrorRate with `"Region", "Global"` and widget `region = "us-east-1"`,
   correct even if your stack lives elsewhere)
7. Verify alarms fire: set Lambda env `PG_HOST` to a bogus value in the console, hit the
   API a few times, wait ~5 min, then `aws cloudwatch describe-alarms --alarm-names <name>`.
   **Revert `PG_HOST` when done.**
8. Save two Logs Insights queries as `notice-board-5xx-recent` (filter `status >= 500` on
   the access log group) and `notice-board-lambda-p95`
   (`filter @type = "REPORT" | stats pct(@duration, 95) by bin(5m)`)

---

# Stage 5 — Submission and teardown

Walk the `ASSIGNMENT.md` submission checklist. Capture for the writeup: the CloudFront
URL, proof the direct S3 URL 403s, a green Actions run, and (if you do Tier 4) the
dashboard with an alarm in `ALARM`.

Then **`terraform destroy`** when the cohort ends, and stop/terminate the Postgres EC2
instance. The nightly cleanup only catches correctly tagged resources — anything you
created by hand outside Terraform is yours to remove.
