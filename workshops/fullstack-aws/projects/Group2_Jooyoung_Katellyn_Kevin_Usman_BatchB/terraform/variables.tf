variable "student_name" {
  description = "Your name in lowercase with no spaces (e.g. jooyoung). Used to identify your resources."

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.student_name))
    error_message = "student_name must be lowercase letters, numbers, and hyphens only (e.g. jooyoung)."
  }
}

variable "project_name" {
  description = "Project name — combined with student_name to form resource names"
  default     = "notice-board"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "database_url" {
  description = "Postgres connection URI (Supabase or any Postgres). Keep ?sslmode=require for Supabase."
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "Secret used to sign JWT access tokens. Use a long random string in any shared environment."
  type        = string
  sensitive   = true
}

variable "jwt_expire_minutes" {
  description = "JWT lifetime in minutes"
  type        = string
  default     = "60"
}

variable "created_date" {
  description = "Creation date for the `date` tag, format dd-mmm-yyyy (e.g. 17-Aug-2026)."
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the shared Lambda execution role your instructor pre-created for the cohort. You don't create your own IAM role."
  type        = string
}

variable "lambda_timeout_s" {
  description = "Lambda timeout in seconds (FastAPI cold start + Supabase)."
  type        = number
  default     = 30
}

variable "lambda_memory_mb" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention"
  type        = number
  default     = 14
}
