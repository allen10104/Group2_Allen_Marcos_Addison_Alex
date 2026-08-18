variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "student_name" {
  description = "Your name, used to prefix every resource (assignment requirement)"
  type        = string
  default     = "santosh-nukala"
}

variable "mongodb_uri" {
  description = "MongoDB Atlas connection string"
  type        = string
  # sensitive = true keeps the value out of `terraform plan` output and the CLI log.
  # It does NOT encrypt state - terraform.tfstate still holds it in plaintext, which is
  # exactly why .gitignore excludes *.tfstate. In production this state would live in
  # an S3 backend with encryption and a DynamoDB lock table.
  sensitive = true
}

variable "mongodb_db" {
  type    = string
  default = "noticeboard"
}

variable "jwt_secret" {
  description = "HS256 signing key for JWTs"
  type        = string
  sensitive   = true
}

variable "lambda_role_arn" {
  description = "Pre-provisioned Lambda execution role supplied by the workshop"
  type        = string
  default     = "arn:aws:iam::279249498881:role/quicklabs-fullstack-shared-lambda-exec"
}
