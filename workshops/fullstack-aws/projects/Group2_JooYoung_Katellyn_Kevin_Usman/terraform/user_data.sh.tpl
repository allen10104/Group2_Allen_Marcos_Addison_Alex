#!/bin/bash
# Rendered by Terraform (templatefile) and run once as EC2 user_data on first
# boot. Bootstraps Postgres, clones the app, installs it, and starts it as a
# systemd service. ${...} placeholders below are filled in by Terraform.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# ── Postgres ──────────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y postgresql postgresql-contrib python3-venv python3-pip git

sudo -u postgres psql <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${postgres_user}') THEN
    CREATE ROLE ${postgres_user} LOGIN PASSWORD '${postgres_password}';
  ELSE
    ALTER ROLE ${postgres_user} WITH PASSWORD '${postgres_password}';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${postgres_db} OWNER ${postgres_user}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${postgres_db}')\gexec
SQL

# Postgres only needs to accept connections from this box (the API runs
# here too) — default localhost-only listen_addresses/pg_hba is fine, no
# need to open it to the network at all.
systemctl enable postgresql
systemctl restart postgresql

# ── App code ──────────────────────────────────────────────────────────────
git clone --branch "${git_branch}" --single-branch "${git_repo_url}" /opt/app
cd "/opt/app/${project_subdir}/backend"

python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

cat > .env <<ENV
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=${postgres_db}
PG_USER=${postgres_user}
PG_PASSWORD=${postgres_password}
S3_UPLOADS_BUCKET=${s3_uploads_bucket}
AWS_REGION=${aws_region}
CORS_ORIGINS=*
ENV

# ── systemd service ─────────────────────────────────────────────────────────
cat > /etc/systemd/system/noticeboard.service <<UNIT
[Unit]
Description=Notice Board API
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/app/${project_subdir}/backend
ExecStart=/opt/app/${project_subdir}/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable noticeboard
systemctl restart noticeboard

# ── Expiry cleanup cron (every 15 minutes) ──────────────────────────────────
CLEANUP_CMD="/opt/app/${project_subdir}/backend/venv/bin/python /opt/app/${project_subdir}/backend/cleanup_expired.py >> /var/log/noticeboard-cleanup.log 2>&1"
( crontab -l 2>/dev/null | grep -v cleanup_expired.py; echo "*/15 * * * * $CLEANUP_CMD" ) | crontab -
