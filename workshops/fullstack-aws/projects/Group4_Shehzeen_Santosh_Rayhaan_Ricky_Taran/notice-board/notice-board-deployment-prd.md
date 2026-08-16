# PRD: Notice Board — Progressive AWS Deployment

**Author:** Student (assignment submission)
**Status:** Draft for execution
**Scope:** Tiers 1–3 mandatory; Tier 4 stretch goal

---

## 1. Overview

### 1.1 Problem
The Notice Board application (React frontend + Python Lambda backend + PostgreSQL on EC2) exists as working code but has no deployment pipeline. It needs to move from "runs on my machine" to a production-shaped AWS deployment, built up in four increasingly mature stages: manual infra, CI/CD automation, CDN/HTTPS hardening, and observability.

### 1.2 Goal
Deploy the Notice Board app to AWS using Infrastructure-as-Code (Terraform), automate deployment via GitHub Actions, harden delivery with CloudFront, and (time permitting) instrument the stack with CloudWatch so failures are diagnosable without reading code.

### 1.3 Non-Goals
- No changes to `backend/lambda_function.py` application logic (Tier 4 explicitly forbids handler changes — observability is infra-only).
- No notification/paging integrations (SNS, email, Slack, PagerDuty) — alarm *state* in the console is sufficient proof.
- No multi-region, autoscaling-of-EC2-Postgres, or database HA — PostgreSQL on EC2 is assumed already running from a prior lab and is out of scope to rebuild.
- No custom domain / Route 53 — CloudFront's default domain is acceptable.

### 1.4 Success Definition
All four tiers' acceptance criteria pass verification (manual click-through + CLI checks), and every AWS resource is uniquely namespaced with a `student-<your-name>` prefix so grading/cleanup is unambiguous.

---

## 2. Architecture

```
User's Browser
      │
      ├── Page Load ─────▶ CloudFront (Tier 3+) ─▶ S3 (private, OAC) [Tier 1-2: S3 public website]
      │
      └── API Calls ──────▶ API Gateway (HTTP API) ──▶ Lambda (Python) ──▶ PostgreSQL on EC2
                                     │
                                     └──▶ CloudWatch Logs / Metrics / Alarms / Dashboard (Tier 4)
```

**Deployment path:** Terraform provisions AWS resources → GitHub Actions (Tier 2+) builds/packages code on every push to `main` → artifacts pushed to Lambda and S3 → CloudFront cache invalidated (Tier 3+).

**Environments:** Single environment, personal/isolated per student via resource-name prefixing (`student-<name>-notice-board`, etc.). No staging/prod split required.

---

## 3. Prerequisites (Definition of Ready)

| # | Requirement | Verification |
|---|---|---|
| 1 | AWS CLI configured (`aws configure`) | `aws sts get-caller-identity` succeeds |
| 2 | Terraform installed | `terraform -v` |
| 3 | Node.js 18+ | `node -v` |
| 4 | Python 3 | `python3 -V` |
| 5 | PostgreSQL running on EC2 (from prior lab) | Can `psql` connect from Lambda's network path |
| 6 | GitHub account + repo for this project | Repo exists, remote configured |

---

## 4. Tier 1 — Manual Deployment (Foundation)

### 4.1 Goal
Stand up the full stack by hand once, proving the architecture works end-to-end before any automation is layered on.

### 4.2 Functional Requirements
| ID | Requirement |
|---|---|
| T1-1 | S3 bucket, static-website-hosting enabled, public read access |
| T1-2 | Lambda function running the Python backend, deployed from `backend/lambda.zip` (produced by `python build.py`) |
| T1-3 | API Gateway (HTTP API type) with a route/integration to the Lambda |
| T1-4 | Lambda has network + credentials to reach PostgreSQL on EC2 |
| T1-5 | React frontend built with `VITE_API_URL` pointed at the deployed API Gateway invoke URL |
| T1-6 | Built frontend (`dist/`) uploaded to the S3 bucket via AWS CLI |
| T1-7 | All resources prefixed `student-<your-name>-...` (e.g., `student-john-smith-notice-board`) |

### 4.3 Terraform Deliverables
- `terraform/main.tf` — S3 bucket + website config + bucket policy, Lambda function + IAM role/policy, API Gateway HTTP API + integration + route + stage
- `terraform/variables.tf` — name prefix, region, DB connection details, runtime settings
- `terraform/outputs.tf` — S3 website endpoint, API Gateway invoke URL, Lambda function name/ARN (consumed later by GitHub Secrets)

### 4.4 Process
1. `python build.py` → produces `backend/lambda.zip`
2. `terraform init && terraform apply`
3. Capture `terraform output` values
4. `VITE_API_URL=<api-url> npm run build` in the frontend
5. `aws s3 sync dist/ s3://<bucket-name> --delete`

### 4.5 Acceptance Criteria
- [ ] S3 website URL renders the Notice Board UI
- [ ] Posting a notice persists to PostgreSQL and appears on the page
- [ ] Deleting a notice removes it from the UI and the DB
- [ ] All AWS resources carry the `student-<your-name>` prefix

### 4.6 Risks / Watch-outs
- Lambda execution role needs outbound network access to the EC2 Postgres instance (security group / VPC config) — a common silent-failure point.
- API Gateway CORS must allow the S3 website origin or the frontend will fail silently on POST/DELETE.
- S3 static website endpoints are HTTP-only — acceptable for Tier 1, resolved in Tier 3.

---

## 5. Tier 2 — CI/CD Automation with GitHub Actions

### 5.1 Goal
Remove all manual `terraform apply` / `aws cli` steps for day-to-day changes. A `git push` to `main` is the only action required to ship.

### 5.2 Functional Requirements
| ID | Requirement |
|---|---|
| T2-1 | Workflow file at `.github/workflows/deploy.yml` |
| T2-2 | Triggers on every push to `main` |
| T2-3 | Packages `backend/lambda.zip` and updates the Lambda function code |
| T2-4 | Builds the React frontend with `VITE_API_URL` injected as a build-time env var |
| T2-5 | Syncs built frontend to the S3 bucket |
| T2-6 | Credentials and config sourced entirely from GitHub Secrets (no hardcoded values) |

### 5.3 Required GitHub Secrets
| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | `us-east-1` |
| `LAMBDA_FUNCTION_NAME` | From Terraform output |
| `S3_BUCKET` | From Terraform output |
| `VITE_API_URL` | From Terraform output |

### 5.4 Workflow Shape (high level)
1. Checkout
2. Setup Python → `python build.py`
3. Configure AWS credentials (from secrets)
4. `aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --zip-file fileb://backend/lambda.zip`
5. Setup Node → `npm ci && npm run build` (with `VITE_API_URL` exported)
6. `aws s3 sync dist/ s3://$S3_BUCKET --delete`

### 5.5 Acceptance Criteria
- [ ] Push to `main` triggers the workflow automatically
- [ ] Workflow completes with zero errors
- [ ] Updated app is live with no manual AWS CLI commands run by hand

### 5.6 Risks / Watch-outs
- Least-privilege IAM: the deploy user only needs `lambda:UpdateFunctionCode`, `s3:PutObject/DeleteObject/ListBucket` (and CloudFront invalidation rights once Tier 3 lands) — avoid using root/admin creds in CI.
- Secrets never printed to workflow logs.

---

## 6. Tier 3 — CDN Hardening with CloudFront

### 6.1 Goal
Serve the frontend over HTTPS with edge caching, and stop exposing the S3 bucket directly to the internet.

### 6.2 Functional Requirements
| ID | Requirement |
|---|---|
| T3-1 | CloudFront Origin Access Control (OAC) resource |
| T3-2 | CloudFront distribution with S3 bucket as origin |
| T3-3 | S3 bucket policy updated to allow access **only** from the CloudFront distribution (via OAC) |
| T3-4 | S3 Public Access Block enabled (block all public access) |
| T3-5 | GitHub Actions workflow issues a CloudFront cache invalidation after every frontend deploy |

### 6.3 Terraform Changes
- Add `aws_cloudfront_origin_access_control`
- Add `aws_cloudfront_distribution` (S3 origin, default cache behavior, viewer HTTPS redirect)
- Replace the Tier 1 public bucket policy with an OAC-scoped policy (`Principal: cloudfront.amazonaws.com`, `Condition: AWS:SourceArn = distribution ARN`)
- Enable `aws_s3_bucket_public_access_block` (all four flags `true`)

### 6.4 Workflow Addition
After `aws s3 sync`:
```
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
```
(New secret: `CLOUDFRONT_DISTRIBUTION_ID`, from Terraform output.)

### 6.5 Acceptance Criteria
- [ ] App loads over HTTPS via the CloudFront URL
- [ ] S3 bucket is no longer directly/publicly accessible
- [ ] Push to `main` triggers an automatic CloudFront invalidation
- [ ] Site loads fast from multiple locations (verified via browser DevTools → Network)

### 6.6 Risks / Watch-outs
- Switching from S3-website-endpoint origin to REST-API-endpoint + OAC changes the origin domain format — update Terraform accordingly, don't mix OAC with legacy OAI.
- Invalidations cost money past the free tier at high volume — scope `/*` is fine for a small app but worth noting.
- SPA routing (if using client-side routes) may need a CloudFront custom error response mapping 403/404 → `index.html`.

---

## 7. Tier 4 — Observability with CloudWatch (Stretch Goal)

**Prerequisite:** Tier 3 complete and live. **Constraint:** infra-only changes — `backend/lambda_function.py` is not touched. **Scope boundary:** logs/metrics/alarms/dashboards only; no alerting/notification channels.

### 7.1 Goal
Make failures diagnosable from the AWS console alone — no more "re-read the code to guess why a save failed."

### 7.2 Functional Requirements
| ID | Requirement |
|---|---|
| T4-1 | `aws_cloudwatch_log_group` for Lambda, `retention_in_days = 14` |
| T4-2 | `aws_cloudwatch_log_group` for API Gateway access logs, same 14-day retention |
| T4-3 | API Gateway stage access logging enabled, JSON format |
| T4-4 | CloudWatch alarm: `AWS/Lambda` `Errors` > 0 over 5-minute window |
| T4-5 | CloudWatch alarm: `AWS/ApiGateway` `5xx` > 0 over 5-minute window |
| T4-6 | One CloudWatch dashboard with widgets: Lambda (invocations, errors, p95 duration), API Gateway (count, 4xx, 5xx, latency), CloudFront (4xxErrorRate, 5xxErrorRate) |
| T4-7 | Two saved CloudWatch Logs Insights queries |

### 7.3 Terraform Deliverables
- 2× `aws_cloudwatch_log_group` (Lambda + API Gateway access logs)
- `aws_apigatewayv2_stage.access_log_settings { destination_arn, format }` (JSON log format string)
- 2× `aws_cloudwatch_metric_alarm` (Lambda Errors, API Gateway 5xx)
- 1× `aws_cloudwatch_dashboard` with a `dashboard_body` JSON containing the three widget groups
- 2× saved Logs Insights queries (created via console or `aws logs put-query-definition`)

### 7.4 Process / Sequencing
1. **Import existing log group** if Tier 1 already created one implicitly:
   `terraform import aws_cloudwatch_log_group.lambda /aws/lambda/<your-fn>`
   (Lambda auto-creates a log group with no retention limit on first invoke — this import brings it under Terraform management before the 14-day retention is applied.)
2. Add both log groups + retention.
3. Wire API Gateway stage `access_log_settings`.
4. Add both metric alarms.
5. Add the dashboard resource.
6. `terraform apply`; confirm alarms start `OK`, dashboard renders, and access-log lines appear after hitting the API.
7. **Fault injection test:** set Lambda env var `PG_HOST` to an unreachable value via the console, hit the API a few times, wait ~5 minutes, confirm the Lambda Errors alarm transitions to `ALARM` (`aws cloudwatch describe-alarms --alarm-names <name>` or console). Revert `PG_HOST` afterward.
8. In Logs Insights, paste and **Save** each of the two queries (e.g., `notice-board-5xx-recent`, `notice-board-lambda-p95`).

### 7.5 Acceptance Criteria
- [ ] Both log groups are Terraform-managed and show 14-day retention (not "Never expire") in console
- [ ] API Gateway access logs appear as one JSON line per request, queryable in Logs Insights
- [ ] Forced Lambda error transitions the Lambda Errors alarm to `ALARM` within 5 minutes
- [ ] Forced 5XX transitions the API Gateway 5xx alarm to `ALARM`
- [ ] Single dashboard shows Lambda + API Gateway + CloudFront widgets at a glance
- [ ] Two saved Logs Insights queries appear under Saved Queries

### 7.6 Risks / Watch-outs
- Forgetting to revert `PG_HOST` leaves the app broken after the fault-injection test — treat this as a required cleanup step, not optional.
- Alarms in `INSUFFICIENT_DATA` state (rather than `OK`/`ALARM`) usually mean the metric dimension names don't match the actual resource — double check Lambda `FunctionName` and API Gateway `ApiId`/`Stage` dimensions.
- CloudFront metrics only exist in `us-east-1` regardless of where the distribution's other resources live — dashboard widgets referencing CloudFront metrics must pin that region explicitly.

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Security | S3 never publicly accessible post-Tier-3; least-privilege IAM for CI deploy user; no secrets committed to the repo |
| Cost | Log retention bounded (14 days) to avoid unbounded CloudWatch storage cost; CloudFront invalidations scoped reasonably |
| Naming | Every resource prefixed `student-<your-name>` for unambiguous grading/cleanup |
| Reproducibility | Entire stack (minus the pre-existing EC2 Postgres) must be creatable from `terraform apply` with no manual console clicks, by Tier 2 |
| Idempotency | Re-running `terraform apply` or re-pushing to `main` should not create duplicate/drifted resources |

---

## 9. Milestones / Suggested Timeline

| Milestone | Deliverable | Gate |
|---|---|---|
| M1 | Tier 1 complete | App reachable via S3 website URL, CRUD works |
| M2 | Tier 2 complete | Push-to-deploy works with zero manual CLI |
| M3 | Tier 3 complete | HTTPS via CloudFront, S3 locked down, auto-invalidation |
| M4 (stretch) | Tier 4 complete | Alarms fire correctly, dashboard + saved queries exist |

Tiers 1–3 are mandatory for the core submission; Tier 4 is picked up only after Tier 3 is verified working and time remains.

---

## 10. Open Questions / Assumptions to Confirm Before Starting
1. Is the EC2 Postgres instance in the same VPC as the Lambda, or does Lambda need VPC config added to reach it? (Not specified in source material — verify against the prior lab setup.)
2. Target AWS region — GitHub Secrets example uses `us-east-1`; confirm this matches where EC2/Postgres already lives.
3. Naming convention for `<your-name>` — confirm exact format (e.g., lowercase-hyphenated) expected by graders.

---

## 11. Appendix — Full Terraform Resource Checklist

- [ ] `aws_s3_bucket` (+ website config, Tier 1) → (+ public access block, Tier 3)
- [ ] `aws_s3_bucket_policy` (public, Tier 1 → OAC-restricted, Tier 3)
- [ ] `aws_lambda_function`
- [ ] `aws_iam_role` + `aws_iam_role_policy` (Lambda execution)
- [ ] `aws_apigatewayv2_api` (HTTP API)
- [ ] `aws_apigatewayv2_integration`
- [ ] `aws_apigatewayv2_route`
- [ ] `aws_apigatewayv2_stage` (+ `access_log_settings`, Tier 4)
- [ ] `aws_cloudfront_origin_access_control` (Tier 3)
- [ ] `aws_cloudfront_distribution` (Tier 3)
- [ ] `aws_cloudwatch_log_group` × 2 (Tier 4)
- [ ] `aws_cloudwatch_metric_alarm` × 2 (Tier 4)
- [ ] `aws_cloudwatch_dashboard` (Tier 4)
