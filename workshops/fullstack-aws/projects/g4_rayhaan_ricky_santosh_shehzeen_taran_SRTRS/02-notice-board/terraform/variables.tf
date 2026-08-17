variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to every resource name, e.g. student-jane-doe"
  type        = string
}

variable "my_ip_cidr" {
  description = "Your IP in CIDR form (e.g. 203.0.113.5/32), used to allow SSH into the Mongo EC2 box. Get it from https://checkip.amazonaws.com"
  type        = string
}

variable "key_pair_name" {
  description = "Name of an EXISTING EC2 key pair (in this region) used to SSH into the Mongo instance"
  type        = string
}

variable "mongo_db_name" {
  description = "MongoDB database name used by the Lambda backend"
  type        = string
  default     = "noticeboard"
}

variable "mongo_instance_type" {
  description = "EC2 instance type for the self-managed MongoDB box"
  type        = string
  default     = "t3.micro"
}

variable "lambda_runtime" {
  description = "Lambda Python runtime. Keep in sync with LAMBDA_PYTHON_VERSION in build.py"
  type        = string
  default     = "python3.12"
}

variable "lambda_role_arn" {
  description = <<-EOT
    ARN of an EXISTING IAM role for the Lambda function to assume, e.g.
    "arn:aws:iam::123456789012:role/LabRole". Used instead of creating a new
    IAM role via Terraform, for restricted/sandbox AWS accounts (AWS Academy,
    Qwiklabs, bootcamp-provided accounts, etc.) where the IAM user isn't
    allowed to call iam:CreateRole. The role must already trust
    lambda.amazonaws.com and have (at minimum) the AWSLambdaBasicExecutionRole
    and AWSLambdaVPCAccessExecutionRole managed policies attached - lab-provided
    roles typically already have broad permissions that cover this.
  EOT
  type        = string
}