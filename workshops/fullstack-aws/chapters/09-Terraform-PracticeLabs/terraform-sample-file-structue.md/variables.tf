variable "student_name" {
  description = "Your name or slug (e.g. alice). Used to name all resources."
  type        = string
}

variable "created_date" {
  description = "Creation date for the `date` tag, format dd-mmm-yyyy (e.g. 12-Jul-2026)."
  type        = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}
