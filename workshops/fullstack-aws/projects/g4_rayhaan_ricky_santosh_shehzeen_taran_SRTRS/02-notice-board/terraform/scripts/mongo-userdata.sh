#!/bin/bash
# Installs MongoDB Community 7.0 on Amazon Linux 2023 and binds it to all
# interfaces (access is restricted at the security-group level to the
# Lambda security group only, so this is safe within this exercise).
set -euxo pipefail

cat <<'REPO' > /etc/yum.repos.d/mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
REPO

dnf install -y mongodb-org

sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf

systemctl enable mongod
systemctl start mongod