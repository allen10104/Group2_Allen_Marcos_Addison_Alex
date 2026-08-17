# Notice Board — SRTRS

A full-stack corkboard-style notice board: React frontend, Python Lambda backend, MongoDB database (substituted for PostgreSQL per the assignment's allowed substitution), deployed to AWS with Terraform and automated via GitHub Actions.

👉 See [ASSIGNMENT.md](./ASSIGNMENT.md) for the original assignment instructions and submission checklist.

**Status: Tiers 1, 2, and 3 complete.**

---

## Live app

**https://d1lveptcxmslzd.cloudfront.net**

Served over HTTPS through CloudFront. The underlying S3 bucket (`student-rayhaan-notice-board`) is private — it's no longer reachable directly; only CloudFront (via Origin Access Control) can read from it.

---

## Architecture

```
Browser
  │  HTTPS
  ▼
CloudFront (OAC)  ──── origin ────▶  S3 bucket (private, static frontend build)
  │
  │  fetch() to API Gateway
  ▼
API Gateway (HTTP API)
  │  AWS_PROXY integration
  ▼
Lambda (student-rayhaan-notice-board-api, Python 3.12, NOT VPC-attached — see note below)
  │  mongodb:// over the public internet
  ▼
MongoDB on EC2 (self-managed, Amazon Linux 2023, installed via user-data)
```

**Why the Lambda isn't VPC-attached:** this account's IAM user only has permission to use one pre-existing shared role (`quicklabs-fullstack-shared-lambda-exec`), and that role lacks `ec2:CreateNetworkInterface`, which Lambda needs to attach to a VPC. Rather than being able to fix the role's permissions (blocked — this is a locked-down lab/training account), the Lambda runs outside the VPC and reaches MongoDB over its **public** IP instead of a private one. As a consequence, the Mongo EC2 security group allows port 27017 from `0.0.0.0/0` rather than scoping it to the Lambda's own security group, since a non-VPC Lambda has no fixed outbound IP to scope to. This is a deliberate trade-off documented in `terraform/main.tf`, not an oversight.

---

## Deployed AWS resources

All resources are prefixed `student-rayhaan`, region `us-east-1`:

| Resource | Value |
|---|---|
| S3 bucket (frontend, private) | `student-rayhaan-notice-board` |
| CloudFront distribution | `d1lveptcxmslzd.cloudfront.net` (ID `E2TB7JQBWD8M6M`) |
| API Gateway base URL | `https://7x4gb8kgwi.execute-api.us-east-1.amazonaws.com` |
| Lambda function | `student-rayhaan-notice-board-api` |
| MongoDB EC2 instance | Amazon Linux 2023, MongoDB 7.0 via `terraform/scripts/mongo-userdata.sh` |

---

## Tier status

- **Tier 1 (manual deploy)** — done. `python build.py` packages the Lambda; `terraform apply` provisions S3, CloudFront-ready bucket policy, the HTTP API, the Lambda, and the Mongo EC2 box; the frontend is built with `VITE_API_URL` baked in and synced to S3.
- **Tier 2 (GitHub Actions CI/CD)** — done. See [CI/CD](#cicd) below for where the workflow actually lives.
- **Tier 3 (CloudFront + HTTPS)** — done. CloudFront distribution with Origin Access Control in front of a fully private S3 bucket (`terraform/cloudfront.tf`); GitHub Actions invalidates the CloudFront cache on every deploy.

---

## CI/CD

This project's folder lives deep inside a shared team monorepo (`workshops/fullstack-aws/projects/g4_rayhaan_ricky_santosh_shehzeen_taran_SRTRS/02-notice-board/`), but **GitHub Actions only ever reads workflow files from the repository root's `.github/workflows/` folder** — not nested ones. So the actual workflow that runs this project's CI/CD is:

**`.github/workflows/deploy-rayhaan-notice-board.yml`** (repo root, alongside teammates' own `deploy-*.yml` files)

It triggers only on pushes to `master` that touch this project's `paths:`-filtered folder, then: builds the Lambda zip, updates the Lambda function code, builds the frontend with `VITE_API_URL`, syncs it to S3, and invalidates the CloudFront cache. It requires these repository secrets (`Settings → Secrets and variables → Actions`): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `LAMBDA_FUNCTION_NAME`, `S3_BUCKET`, `VITE_API_URL`, `CLOUDFRONT_DISTRIBUTION_ID`.

A stale, non-functional `deploy.yml` also still exists under this project's own `.github/workflows/` folder from an earlier attempt — it's inert (GitHub never reads it from that location) and can be ignored or removed.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notices` | Return all notices |
| POST | `/notices` | Create a notice `{ title, content, bg_color, text_color }` |
| PUT | `/notices/{id}` | Partially update a notice (position, colors, title, content) |
| DELETE | `/notices/{id}` | Delete a notice by ID |

Max 15 notices on the board at once (enforced in `backend/lambda_function.py`).

---

## Repo layout

```
02-notice-board/
├── frontend/                  # React + Vite corkboard UI
│   ├── src/app.jsx            # main app (lowercase filename — imports match it)
│   └── src/components/        # NoticeCard.jsx, NoticeModal.jsx
├── backend/
│   ├── lambda_function.py     # Lambda handler (pymongo)
│   ├── local_server.py        # local dev server, no AWS required
│   └── requirements.txt
├── build.py                   # packages backend/lambda.zip for the Lambda runtime
├── terraform/
│   ├── main.tf                 # Tier 1: security groups, Mongo EC2, S3, Lambda, API Gateway
│   ├── cloudfront.tf            # Tier 3: CloudFront + OAC + private bucket policy
│   ├── variables.tf
│   ├── outputs.tf
│   └── scripts/mongo-userdata.sh
└── .gitignore                  # excludes venv/, node_modules/, dist/, *.zip, *.pem, tfstate, tfvars
```

(The GitHub Actions workflow itself lives at the repo root — see [CI/CD](#cicd) above, not in this folder.)

---

## Local development

```bash
python3 -m venv venv
venv\Scripts\Activate.ps1        # PowerShell; use source venv/bin/activate on Mac/Linux
pip install -r backend/requirements.txt
python backend/local_server.py   # local API, no AWS needed

cd frontend
npm install
npm run dev
```

---

## Cleaning up (avoid ongoing AWS charges)

```powershell
cd terraform
terraform destroy
```

This tears down the Lambda, API Gateway, CloudFront distribution, S3 bucket, and — importantly — the EC2 instance running MongoDB, which is the main thing billed by the hour if left running.
