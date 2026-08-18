#!/bin/bash
# setup-postgres-ec2.sh
#
# Run this ON the EC2 instance (over SSH) after you've launched it.
# Installs PostgreSQL, creates a dedicated app user + database for the
# Notice Board, and opens the instance up to remote connections so the
# (VPC-less) Lambda function can reach it over the public internet.
#
# Tested on Ubuntu 22.04/24.04. Adjust the package manager section if you
# launched Amazon Linux instead.
#
# Usage (from your machine):
#   scp scripts/setup-postgres-ec2.sh ubuntu@<EC2_PUBLIC_IP>:~
#   ssh ubuntu@<EC2_PUBLIC_IP>
#   chmod +x setup-postgres-ec2.sh
#   sudo ./setup-postgres-ec2.sh

set -euo pipefail

DB_NAME="noticeboard"
DB_USER="noticeboard_app"

if [ -z "${DB_PASSWORD:-}" ]; then
  echo "Set DB_PASSWORD before running, e.g.:"
  echo "  sudo DB_PASSWORD='some-strong-password' ./setup-postgres-ec2.sh"
  exit 1
fi

echo "==> Installing PostgreSQL..."
apt-get update -y
apt-get install -y postgresql postgresql-contrib

PG_VERSION=$(psql -V | grep -oP '\d+' | head -1)
PG_CONF_DIR="/etc/postgresql/${PG_VERSION}/main"

echo "==> Creating database and app user..."
sudo -u postgres psql <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec
SQL

echo "==> Allowing remote connections..."
sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" "${PG_CONF_DIR}/postgresql.conf"

# md5 auth for the app user from anywhere (Lambda has no fixed IP outside a
# VPC). Locking this down to a NAT gateway/EIP range is a good follow-up if
# you later attach Lambda to a VPC.
if ! grep -q "^host all all 0.0.0.0/0 md5" "${PG_CONF_DIR}/pg_hba.conf"; then
  echo "host all all 0.0.0.0/0 md5" >> "${PG_CONF_DIR}/pg_hba.conf"
fi

systemctl restart postgresql
systemctl enable postgresql

echo ""
echo "Done."
echo "  Host:     $(curl -s ifconfig.me 2>/dev/null || echo '<this instance public IP>')"
echo "  Port:     5432"
echo "  Database: ${DB_NAME}"
echo "  User:     ${DB_USER}"
echo ""
echo "Next: open port 5432 to inbound traffic on this instance's security group"
echo "(aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 5432 --cidr 0.0.0.0/0)"
echo "then put these values in terraform/terraform.tfvars."
