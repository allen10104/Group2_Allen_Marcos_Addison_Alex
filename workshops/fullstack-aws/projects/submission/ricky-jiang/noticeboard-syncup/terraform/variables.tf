variable "student_prefix" {
  description = "Prefix applied to every AWS resource name (assignment naming requirement)"
  type        = string
  default     = "student-ricky-jiang"
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type for the backend"
  type        = string
  default     = "t3.micro"
}

variable "ssh_public_key_path" {
  description = "Path to the local SSH public key used for EC2 access"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

# ---------- Lambda experiment (Phase: EC2->Lambda migration test) ----------
# These are additive - the EC2 deployment doesn't use any of these.

variable "lambda_exec_role_arn" {
  description = "Pre-existing shared Lambda execution role (this AWS account has no IAM permissions for students, so a shared role is used instead of creating one)"
  type        = string
  default     = "arn:aws:iam::279249498881:role/quicklabs-fullstack-shared-lambda-exec"
}

variable "mongodb_uri" {
  description = "MongoDB Atlas connection string for the Lambda function's environment"
  type        = string
  sensitive   = true
}

variable "lambda_jwt_secret" {
  description = "JWT signing secret for the Lambda environment (separate from the EC2 deployment's secret)"
  type        = string
  sensitive   = true
}

variable "lambda_cors_origins" {
  description = "Allowed CORS origins for the Lambda-backed API, comma-separated"
  type        = string
  default     = "http://localhost:5173,https://d29oqtt6m1oqoi.cloudfront.net"
}
