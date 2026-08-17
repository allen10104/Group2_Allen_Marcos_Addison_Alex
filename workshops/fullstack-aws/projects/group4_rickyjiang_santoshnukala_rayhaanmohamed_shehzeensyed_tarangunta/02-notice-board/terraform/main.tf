terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Pin the MAJOR version. Provider majors introduce breaking changes and
      # discovering that mid-deploy is not the experience you want.
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  # Every resource name derives from this. The assignment requires the student prefix;
  # computing it once means it can never drift between resources.
  name = "student-${var.student_name}-notice-board"

  tags = {
    Project = "notice-board"
    Student = var.student_name
    Managed = "terraform"
  }
}

# ---------------------------------------------------------------------------
# S3 - static website hosting for the React bundle
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "frontend" {
  # S3 bucket names are GLOBALLY unique across every AWS account on earth.
  # The student prefix makes a collision essentially impossible.
  bucket = local.name
  tags   = local.tags
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    # index.html, not error.html: this is a single-page app. Any unknown path must be
    # served the app shell so React can handle it. Without this a refresh on a
    # sub-path returns a raw S3 404.
    key = "index.html"
  }
}

# By default S3 blocks all public access. Tier 1 explicitly wants a public website, so
# we lift the block. TIER 3 REVERSES ALL FOUR OF THESE and puts CloudFront in front.
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"            # anyone on the internet
      Action    = "s3:GetObject" # READ ONLY - never s3:PutObject
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })

  # Applying a public policy before the public access block is lifted fails with
  # AccessDenied. Terraform cannot infer this ordering itself.
  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# ---------------------------------------------------------------------------
# IAM - execution role
# ---------------------------------------------------------------------------
# The workshop account denies iam:CreateRole, so we consume a shared execution role
# provisioned by the instructors instead of creating our own. Terraform never manages
# or destroys it - we only reference its ARN.
#
# In an account where we could create it, this would be an aws_iam_role with a trust
# policy allowing lambda.amazonaws.com to assume it, plus an attachment of
# AWSLambdaBasicExecutionRole (create log group, create log stream, put log events -
# nothing more). See git history for that version.

# ---------------------------------------------------------------------------
# Lambda - the FastAPI backend
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "api" {
  function_name = "${local.name}-api"
  role          = var.lambda_role_arn

  filename = "${path.module}/../backend/lambda.zip"

  # Terraform only re-uploads when this hash changes. WITHOUT IT, editing Python and
  # re-running apply reports "no changes" and deploys nothing - then you spend twenty
  # minutes wondering why your fix had no effect.
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")

  # module.function - matches `handler = Mangum(app)` in backend/lambda_function.py
  handler = "lambda_function.handler"
  runtime = "python3.13"

  # Python needs far less than a JVM. 512 MB is comfortable; CPU scales with memory on
  # Lambda, so this also keeps the cold start quick.
  memory_size = 512
  # A cold start plus the first Atlas TLS handshake can take a few seconds. 30 matches
  # the API Gateway integration timeout, so anything higher is unreachable anyway.
  timeout = 30

  environment {
    variables = {
      REPOSITORY             = "mongo"
      MONGODB_URI            = var.mongodb_uri
      MONGODB_DB             = var.mongodb_db
      JWT_SECRET             = var.jwt_secret
      JWT_EXPIRATION_MINUTES = "60"

      # The S3 website endpoint, so the browser's cross-origin calls are permitted.
      # Tier 3 appends the CloudFront domain here - one line, no code change, because
      # config.py reads this at startup.
      CORS_ALLOWED_ORIGINS = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
    }
  }

  tags = local.tags
}

# ---------------------------------------------------------------------------
# API Gateway - HTTP API (v2)
# ---------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "api" {
  name          = "${local.name}-api"
  protocol_type = "HTTP"

  # NO cors_configuration BLOCK ON PURPOSE.
  # FastAPI's CORSMiddleware already emits CORS headers. If API Gateway adds its own,
  # the browser receives TWO Access-Control-Allow-Origin headers and rejects the
  # response with "contains multiple values" - which reads exactly like a CORS
  # misconfiguration and sends you debugging the wrong layer. One CORS owner only.

  tags = local.tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY" # pass the whole request through
  integration_uri  = aws_lambda_function.api.invoke_arn

  # 2.0 is the HTTP API event shape. Mangum detects and handles both, but pinning it
  # keeps the event format predictable in the logs.
  payload_format_version = "2.0"

  timeout_milliseconds = 30000 # must be <= the Lambda timeout
}

# Catch-all: every method, every path, straight to Lambda. FastAPI's own routing does
# the real work, so duplicating the route table in API Gateway would just be two
# places to keep in sync.
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# {proxy+} does NOT match the bare root path, so it needs its own route.
resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id = aws_apigatewayv2_api.api.id
  # "$default" is the special stage that serves from the API's root URL with no
  # /stage-name path segment. Any other name means every frontend URL needs the stage
  # prefix appended - an easy way to break VITE_API_URL.
  name        = "$default"
  auto_deploy = true
  tags        = local.tags

  # TIER 4 adds an access_log_settings block right here.
}

# Without this, API Gateway gets AccessDeniedException calling your function.
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"

  # Scopes the grant to THIS API only. Without source_arn, any API Gateway in any
  # account could invoke your function.
  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
