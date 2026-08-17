terraform {
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      workshop   = "full-stack"
      autodelete = "true"
      date       = var.created_date
    }
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  # Pattern: student-<name>-notice-board-<random>
  name        = "student-${var.student_name}-${var.project_name}-${random_id.suffix.hex}"
  lambda_name = "student-${var.student_name}-${var.project_name}-api"
}

# ─────────────────────────────────────────────
# S3 — Frontend Hosting (private; CloudFront OAC only)
# ─────────────────────────────────────────────

resource "aws_s3_bucket" "frontend" {
  bucket        = local.name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  index_document { suffix = "index.html" }
  error_document { key = "index.html" }
}

# ─────────────────────────────────────────────
# CloudFront — CDN with OAC
# ─────────────────────────────────────────────

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${local.name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  comment             = local.name

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  # OAC returns 403 for missing keys; SPA routes like /login need index.html.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontOAC"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn
        }
      }
    }]
  })
}

# ─────────────────────────────────────────────
# CloudWatch log groups (create before Lambda)
# ─────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "apigw_access" {
  name              = "/aws/apigateway/${local.name}-access"
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "apigw_logging" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.apigw_access.arn}:*"]
  }
}

resource "aws_cloudwatch_log_resource_policy" "apigw" {
  policy_name     = "${local.name}-apigw-logs"
  policy_document = data.aws_iam_policy_document.apigw_logging.json
}

# ─────────────────────────────────────────────
# Lambda — FastAPI via Mangum
# ─────────────────────────────────────────────
# Run python build.py before terraform apply to generate backend/lambda.zip
#
# Uses the shared Lambda execution role your instructor pre-created for the
# cohort (no student-managed IAM). Pass its ARN with -var=lambda_role_arn=...

resource "aws_lambda_function" "api" {
  function_name    = local.lambda_name
  role             = var.lambda_role_arn
  runtime          = "python3.12"
  handler          = "lambda_function.handler"
  filename         = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")
  timeout          = var.lambda_timeout_s
  memory_size      = var.lambda_memory_mb

  environment {
    variables = {
      DATABASE_URL       = var.database_url
      JWT_SECRET         = var.jwt_secret
      JWT_EXPIRE_MINUTES = var.jwt_expire_minutes
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ─────────────────────────────────────────────
# API Gateway — HTTP API
# ─────────────────────────────────────────────

resource "aws_apigatewayv2_api" "api" {
  name          = local.lambda_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 86400
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw_access.arn
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      method             = "$context.httpMethod"
      route              = "$context.routeKey"
      status             = "$context.status"
      responseLength     = "$context.responseLength"
      integrationStatus  = "$context.integrationStatus"
      integrationLatency = "$context.integrationLatency"
    })
  }

  depends_on = [aws_cloudwatch_log_resource_policy.apigw]
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# ─────────────────────────────────────────────
# CloudWatch alarms
# ─────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0
  period              = 300
  statistic           = "Sum"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
  treat_missing_data = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "apigw_5xx" {
  alarm_name          = "${local.name}-apigw-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 0
  period              = 300
  statistic           = "Sum"
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  dimensions = {
    ApiId = aws_apigatewayv2_api.api.id
  }
  treat_missing_data = "notBreaching"
}

# ─────────────────────────────────────────────
# CloudWatch dashboard
# ─────────────────────────────────────────────

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = local.name
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Lambda"
          region = "us-east-1"
          period = 60
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.api.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", ".", { stat = "p95" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway"
          region = "us-east-1"
          period = 60
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.api.id],
            [".", "4xx", ".", "."],
            [".", "5xx", ".", "."],
            [".", "Latency", ".", ".", { stat = "p95" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          title  = "CloudFront"
          region = "us-east-1"
          period = 300
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.cdn.id, "Region", "Global"],
            [".", "4xxErrorRate", ".", ".", ".", "."],
            [".", "5xxErrorRate", ".", ".", ".", "."]
          ]
        }
      }
    ]
  })
}

# ─────────────────────────────────────────────
# Saved Logs Insights queries
# ─────────────────────────────────────────────

resource "aws_cloudwatch_query_definition" "apigw_5xx_recent" {
  name = "${local.name}-5xx-recent"

  log_group_names = [
    aws_cloudwatch_log_group.apigw_access.name
  ]

  query_string = <<-Q
    fields @timestamp, requestId, route, status, integrationStatus, integrationLatency
    | filter status >= 500
    | sort @timestamp desc
    | limit 20
  Q
}

resource "aws_cloudwatch_query_definition" "lambda_p95" {
  name = "${local.name}-lambda-p95"

  log_group_names = [
    aws_cloudwatch_log_group.lambda.name
  ]

  query_string = <<-Q
    filter @type = "REPORT"
    | stats pct(@duration, 95) by bin(5m)
  Q
}
