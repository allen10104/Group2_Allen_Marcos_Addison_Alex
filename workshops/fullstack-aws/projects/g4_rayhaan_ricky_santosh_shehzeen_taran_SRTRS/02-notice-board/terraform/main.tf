terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Networking (reuses the account's default VPC/subnets to keep this exercise
# simple - swap these data sources for your own VPC if you already have one
# from the Lambda/Postgres/EC2 lab)
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# ---------------------------------------------------------------------------
# Security groups
#
# NOTE: the Lambda is intentionally NOT attached to the VPC (no vpc_config,
# no aws_security_group "lambda"). Attaching a Lambda to a VPC requires the
# execution role to have ec2:CreateNetworkInterface/DescribeNetworkInterfaces/
# DeleteNetworkInterface (normally via the AWSLambdaVPCAccessExecutionRole
# managed policy). The shared lab role for this account doesn't have that
# permission and we can't attach policies to it ourselves, so instead the
# Lambda runs outside the VPC and reaches MongoDB over its public IP. Because
# Lambda functions outside a VPC don't have a fixed outbound IP/CIDR, the
# Mongo security group has to allow port 27017 from anywhere rather than
# scoping it to a specific security group - an acceptable trade-off for this
# exercise, but note it's less restrictive than the VPC-attached design.
# ---------------------------------------------------------------------------

resource "aws_security_group" "mongo_ec2" {
  name        = "${var.name_prefix}-mongo-sg"
  description = "Security group for the self-managed MongoDB EC2 instance"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from your IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description = "MongoDB from anywhere - Lambda is not VPC-attached and has no fixed IP, see note above"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-mongo-sg"
  }
}

# ---------------------------------------------------------------------------
# MongoDB on EC2 (self-managed, mirrors the "PostgreSQL on EC2" lab pattern)
# ---------------------------------------------------------------------------

resource "aws_instance" "mongo" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.mongo_instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.mongo_ec2.id]
  key_name                    = var.key_pair_name
  associate_public_ip_address = true
  user_data                   = file("${path.module}/scripts/mongo-userdata.sh")

  tags = {
    Name = "${var.name_prefix}-mongo"
  }
}

# ---------------------------------------------------------------------------
# S3 bucket - Tier 1: public static website hosting
# (Tier 3 replaces the public policy + access block with a CloudFront-only
#  policy - see the Tier 3 section appended further down this file)
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.name_prefix}-notice-board"

  tags = {
    Name = "${var.name_prefix}-notice-board"
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  # SPA fallback: unknown paths (client-side routes) still get index.html
  error_document {
    key = "index.html"
  }
}

# Tier 3: the public access block + public-read bucket policy that used to
# live here have been replaced by the CloudFront-only versions in
# cloudfront.tf (aws_s3_bucket_public_access_block.frontend_private and
# aws_s3_bucket_policy.frontend_cloudfront_only) - the bucket is now fully
# private, reachable only through CloudFront via Origin Access Control.

# ---------------------------------------------------------------------------
# IAM role for Lambda
#
# NOTE: this originally created its own aws_iam_role + policy attachments.
# On restricted/sandbox AWS accounts (AWS Academy, Qwiklabs, bootcamp-issued
# accounts, etc.) the provided IAM user typically can't call iam:CreateRole
# (or even iam:ListRoles/iam:GetRole) at all - only a pre-existing lab role
# may be used. So instead of managing a role here, we just reference an
# existing one by ARN via var.lambda_role_arn - no IAM API calls happen
# through Terraform at all this way.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "api" {
  function_name    = "${var.name_prefix}-notice-board-api"
  filename         = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")
  handler          = "lambda_function.handler"
  runtime          = var.lambda_runtime
  role             = var.lambda_role_arn
  timeout          = 10
  memory_size      = 256

  # Not VPC-attached - see the note above aws_security_group.mongo_ec2.
  environment {
    variables = {
      MONGO_HOST = aws_instance.mongo.public_ip
      MONGO_PORT = "27017"
      MONGO_DB   = var.mongo_db_name
    }
  }
}

# ---------------------------------------------------------------------------
# API Gateway (HTTP API)
# ---------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.name_prefix}-notice-board-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_notices" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /notices"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "post_notices" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /notices"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "delete_notice" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "DELETE /notices/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "put_notice" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "PUT /notices/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}