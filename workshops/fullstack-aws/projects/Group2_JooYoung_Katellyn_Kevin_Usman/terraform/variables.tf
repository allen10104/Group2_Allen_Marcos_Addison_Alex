variable "student_name" {
  description = "Your name in lowercase with no spaces (e.g. kevin-lam). Used to identify your resources."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.student_name))
    error_message = "student_name must be lowercase letters, numbers, and hyphens only (e.g. kevin-lam)."
  }
}

variable "project_name" {
  description = "Project name — combined with student_name to form resource names"
  type        = string
  default     = "notice-board"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

# ─────────────────────────────────────────────
# Postgres — runs on the same EC2 instance as the API (localhost)
# ─────────────────────────────────────────────

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "noticeboard"
}

variable "postgres_user" {
  description = "PostgreSQL username the API connects as"
  type        = string
  default     = "noticeboard_app"
}

variable "postgres_password" {
  description = "PostgreSQL password the API connects with"
  type        = string
  sensitive   = true
}

# ─────────────────────────────────────────────
# EC2 — hosts Postgres + the FastAPI backend
# ─────────────────────────────────────────────

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "git_repo_url" {
  description = "HTTPS URL of the (public) repo the EC2 instance clones on boot"
  type        = string
  default     = "https://github.com/LumpyTacos/workshops.git"
}

variable "git_branch" {
  description = "Branch to clone/deploy"
  type        = string
  default     = "master"
}

variable "project_subdir" {
  description = "Path within the repo to this project (contains backend/, frontend/, etc.)"
  type        = string
  default     = "workshops/fullstack-aws/projects/Group2_JooYoung_Katellyn_Kevin_Usman"
}

variable "created_date" {
  description = "Creation date for the `date` tag, format dd-mmm-yyyy (e.g. 14-Aug-2026)."
  type        = string
}
