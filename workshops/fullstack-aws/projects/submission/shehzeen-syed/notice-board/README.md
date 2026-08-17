# Notice Board

React frontend + FastAPI backend (running on Lambda via Mangum) +
PostgreSQL, with JWT auth, deployed to AWS in four progressive tiers.
See `notice-board-deployment-prd.md` for the full requirements
writeup; this file is the practical run-through.

```
backend/       FastAPI app (app.py), build script, requirements
frontend/      Vite + React app (public board, login-gated posting)
terraform/     All infra, gated by enable_cloudfront / enable_observability
postman/       Collection for exercising the API directly
.github/       CI/CD workflow
```

## API

| Method | Path | Auth? | Purpose |
|---|---|---|---|
| POST | `/auth/register` | no | Create a user, returns a JWT |
| POST | `/auth/login` | no | Returns a JWT for an existing user |
| GET | `/notices` | no | List all notices (public read) |
| POST | `/notices` | **yes** | Create a notice, tagged with your username |
| DELETE | `/notices/{id}` | **yes** | Delete a notice (any logged-in user can delete any notice — no ownership restriction) |

Auth is `Authorization: Bearer <token>`. FastAPI's interactive docs
are live at `<api_url>/docs` once deployed — handy for poking at the
API without Postman.

## 0. Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform installed
- Node.js 18+
- Python 3
- A PostgreSQL instance already running on EC2, reachable from where
  Lambda will run (see `lambda_vpc_subnet_ids` note below)
- A GitHub repo for this project

Create `terraform/terraform.tfvars` (gitignored) with at least:

```hcl
name_prefix = "student-your-name"
pg_host     = "<ec2-private-or-public-ip>"
pg_db       = "noticeboard"
pg_user     = "noticeboard_app"
pg_password = "<your-db-password>"
jwt_secret  = "<long random string, e.g. output of: openssl rand -hex 32>"

# Only needed if Postgres is only reachable from inside a VPC:
# lambda_vpc_subnet_ids         = ["subnet-xxxx"]
# lambda_vpc_security_group_ids = ["sg-xxxx"]
```

The app creates its own `users` and `notices` tables on first
request — no manual schema setup needed, as long as the DB itself and
`pg_user` already exist.

## Tier 1 — Manual deploy

```bash
cd backend && python build.py && cd ..
cd terraform
terraform init
terraform apply
cd ..

# Build the frontend against the deployed API
cd frontend
npm install
VITE_API_URL="$(cd ../terraform && terraform output -raw api_url)" npm run build
cd ..

# Upload it
aws s3 sync frontend/dist "s3://$(cd terraform && terraform output -raw s3_bucket_name)" --delete
```

Open the URL from `terraform output s3_website_url`. You'll see the
board (public, no login needed). Click **Log in** → **Sign up** to
create an account, then post and delete a notice to confirm it's
hitting PostgreSQL.

To test the API directly instead of through the UI, import
`postman/notice-board.postman_collection.json` into Postman, set the
`base_url` collection variable to your `api_url` output, and run
Register → List Notices → Create Notice → Delete Notice in order (the
Register/Login requests auto-capture the token into a collection
variable for the rest).

## Tier 2 — GitHub Actions

Add these repo secrets (Settings → Secrets and variables → Actions),
using the Tier 1 `terraform output` values:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key (scoped to Lambda/S3, see below) |
| `AWS_SECRET_ACCESS_KEY` | matching secret key |
| `AWS_REGION` | `us-east-1` |
| `LAMBDA_FUNCTION_NAME` | `terraform output -raw lambda_function_name` |
| `S3_BUCKET` | `terraform output -raw s3_bucket_name` |
| `VITE_API_URL` | `terraform output -raw api_url` |

Push to `main` — `.github/workflows/deploy.yml` builds and deploys
both halves automatically. No `CLOUDFRONT_DISTRIBUTION_ID` secret yet,
so the invalidation step just skips itself.

**IAM note:** don't use your root/admin keys in CI. Create a deploy
user with only `lambda:UpdateFunctionCode`, `s3:PutObject`,
`s3:DeleteObject`, `s3:ListBucket` on this project's resources.

## Tier 3 — CloudFront

```bash
cd terraform
terraform apply -var="enable_cloudfront=true"
```

This flips the S3 bucket to CloudFront-only (public access blocked)
and creates the distribution. Add one more secret:

| Secret | Value |
|---|---|
| `CLOUDFRONT_DISTRIBUTION_ID` | `terraform output -raw cloudfront_distribution_id` |

Push to `main` again — the workflow now also invalidates the
CloudFront cache after each frontend deploy. Load the app at
`terraform output -raw cloudfront_domain_name` — should be HTTPS,
and the raw S3 website URL should now 403.

## Tier 4 — Observability (stretch)

Do this only after Tier 3 is verified working.

If the Lambda has already been invoked (it has, from Tier 1-3
testing), AWS already auto-created its log group with no retention
limit. Import it first so Terraform can manage it:

```bash
terraform import 'aws_cloudwatch_log_group.lambda[0]' \
  "/aws/lambda/$(terraform output -raw lambda_function_name)"
```

Then:

```bash
terraform apply -var="enable_cloudfront=true" -var="enable_observability=true"
```

This adds two log groups (14-day retention), JSON access logging on
the API Gateway stage, two metric alarms (Lambda Errors, API Gateway
5xx), a dashboard, and two saved Logs Insights queries.

**Verify alarms actually fire:** in the Lambda console, temporarily
set the `PG_HOST` environment variable to something unreachable
(e.g. `10.255.255.1`), hit the API a few times from the browser, wait
~5 minutes, then check:

```bash
aws cloudwatch describe-alarms \
  --alarm-names "$(terraform output -raw lambda_function_name)-errors" 2>/dev/null || \
aws cloudwatch describe-alarms --alarm-name-prefix "$(terraform -chdir=terraform output -raw lambda_function_name)"
```

Both alarms should show `ALARM`. **Revert `PG_HOST`** afterward —
this step intentionally breaks the app and it stays broken until you do.

Note `terraform.tfvars` should keep `enable_cloudfront = true` and
`enable_observability = true` set from here on (or pass both `-var`
flags on every apply) so Tier 3/4 resources aren't torn down.

## Every-day workflow (after Tier 2)

Just `git push` to `main`. Terraform is only re-run when infrastructure
itself changes (new tier, new variable) — application code changes
ship through GitHub Actions alone.
