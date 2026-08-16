variable "name_prefix" {
  description = "Prefix for every AWS resource name, e.g. student-jane-doe"
  type        = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# ---------- Database (PostgreSQL on EC2, from the prior lab) ----------

variable "pg_host" {
  description = "Hostname or private IP of the PostgreSQL EC2 instance"
  type        = string
}

variable "pg_port" {
  type    = string
  default = "5432"
}

variable "pg_db" {
  type = string
}

variable "pg_user" {
  type = string
}

variable "pg_password" {
  type      = string
  sensitive = true
}

# ---------- Auth ----------

variable "jwt_secret" {
  description = "Secret used to sign/verify JWTs. Use a long random string (e.g. `openssl rand -hex 32`)."
  type        = string
  sensitive   = true
}

variable "jwt_expire_minutes" {
  type    = number
  default = 60
}

# ---------- Optional: put Lambda in a VPC to reach the EC2 DB privately ----------
# Leave both lists empty if your EC2 Postgres instance is reachable over the
# public internet (security group allowing the Lambda's egress). Fill them
# in if the DB is only reachable from inside your VPC.

variable "lambda_vpc_subnet_ids" {
  type    = list(string)
  default = []
}

variable "lambda_vpc_security_group_ids" {
  type    = list(string)
  default = []
}

# ---------- Tier toggles ----------
# Tier 1/2: leave both false.
# Tier 3:   set enable_cloudfront = true (also flips the S3 bucket to
#           CloudFront-only access and blocks public access).
# Tier 4:   set enable_observability = true (adds log groups, alarms,
#           dashboard, and saved Logs Insights queries).

variable "enable_cloudfront" {
  type    = bool
  default = false
}

variable "enable_observability" {
  type    = bool
  default = false
}
