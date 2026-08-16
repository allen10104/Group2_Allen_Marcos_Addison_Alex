terraform {
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

# =====================================================================
# S3 — frontend hosting
# =====================================================================

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.name_prefix}-notice-board-frontend"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# Tier 1/2: bucket is public. Tier 3 (enable_cloudfront = true): bucket
# is locked down and only CloudFront (via OAC) may read it.
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = var.enable_cloudfront
  block_public_policy     = var.enable_cloudfront
  ignore_public_acls      = var.enable_cloudfront
  restrict_public_buckets = var.enable_cloudfront
}

data "aws_iam_policy_document" "public_read" {
  statement {
    sid    = "PublicReadGetObject"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
  }
}

data "aws_iam_policy_document" "cloudfront_oac_read" {
  count = var.enable_cloudfront ? 1 : 0

  statement {
    sid    = "AllowCloudFrontServicePrincipalReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend[0].arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket     = aws_s3_bucket.frontend.id
  policy     = var.enable_cloudfront ? data.aws_iam_policy_document.cloudfront_oac_read[0].json : data.aws_iam_policy_document.public_read.json
  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# =====================================================================
# Lambda — Python backend
# =====================================================================

resource "aws_iam_role" "lambda_exec" {
  name = "${var.name_prefix}-notice-board-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  count      = length(var.lambda_vpc_subnet_ids) > 0 ? 1 : 0
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_lambda_function" "backend" {
  function_name    = "${var.name_prefix}-notice-board-api"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.handler"
  runtime          = "python3.12"
  timeout          = 10
  filename         = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")

  environment {
    variables = {
      PG_HOST            = var.pg_host
      PG_PORT            = var.pg_port
      PG_DB              = var.pg_db
      PG_USER            = var.pg_user
      PG_PASSWORD        = var.pg_password
      JWT_SECRET         = var.jwt_secret
      JWT_EXPIRE_MINUTES = tostring(var.jwt_expire_minutes)
    }
  }

  dynamic "vpc_config" {
    for_each = length(var.lambda_vpc_subnet_ids) > 0 ? [1] : []
    content {
      subnet_ids         = var.lambda_vpc_subnet_ids
      security_group_ids = var.lambda_vpc_security_group_ids
    }
  }
}

# =====================================================================
# API Gateway — HTTP API
# =====================================================================

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.name_prefix}-notice-board-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

# FastAPI does its own internal routing (/auth/register, /auth/login,
# /notices, /notices/{id}, /docs, ...), so API Gateway just needs to
# proxy everything through to it.
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  # Tier 4 (enable_observability = true) turns on JSON access logging.
  dynamic "access_log_settings" {
    for_each = var.enable_observability ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.apigw_access[0].arn
      format = jsonencode({
        requestId                = "$context.requestId"
        ip                       = "$context.identity.sourceIp"
        requestTime               = "$context.requestTime"
        httpMethod                = "$context.httpMethod"
        routeKey                  = "$context.routeKey"
        status                    = "$context.status"
        protocol                  = "$context.protocol"
        responseLength             = "$context.responseLength"
        integrationErrorMessage   = "$context.integrationErrorMessage"
      })
    }
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
