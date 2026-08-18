Here is the complete **Version 2** guide for deploying the **Notice Board** application using **Terraform** as your Infrastructure as Code (IaC) framework and connecting to PostgreSQL on EC2.

---

# Version 2: Terraform Infrastructure Deployment

All resources are created, updated, and destroyed declaratively through Terraform.

---

## 🛠️ Step-by-Step Implementation

### Step 1: Package Backend Dependencies

Run the packaging script locally in your project root to prepare the Lambda zip archive:

```bash
python build.py

```

*(This generates `backend/lambda.zip` containing `lambda_function.py` and its dependencies).*

---

### Step 2: Define Infrastructure in Terraform

Create a folder named `terraform/` at the root of your project and populate the following 3 files:

#### `terraform/variables.tf`

```hcl
variable "student_name" {
  type        = string
  description = "Your student name used as a prefix for resource naming"
  default     = "john-smith"
}

variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "pg_host" {
  type        = string
  description = "Public or Private IP of your PostgreSQL EC2 instance"
}

variable "pg_database" {
  type        = string
  description = "PostgreSQL Database Name"
  default     = "noticeboard"
}

variable "pg_user" {
  type        = string
  description = "PostgreSQL Username"
  default     = "postgres"
}

variable "pg_password" {
  type        = string
  description = "PostgreSQL Password"
  sensitive   = true
}

```

#### `terraform/main.tf`

```hcl
provider "aws" {
  region = var.aws_region
}

locals {
  name = "student-${var.student_name}-notice-board"
}

# ==========================================
# 1. FRONTEND: S3 BUCKET & WEBSITE
# ==========================================
resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.name}-frontend"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==========================================
# 2. BACKEND: IAM ROLE & LAMBDA FUNCTION
# ==========================================
resource "aws_iam_role" "lambda_exec" {
  name = "${local.name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "backend" {
  function_name    = "${local.name}-backend"
  filename         = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      PG_HOST     = var.pg_host
      PG_DATABASE = var.pg_database
      PG_USER     = var.pg_user
      PG_PASSWORD = var.pg_password
    }
  }
}

# ==========================================
# 3. API GATEWAY (HTTP API)
# ==========================================
resource "aws_apigatewayv2_api" "api" {
  name          = "${local.name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }
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
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "routes" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# ==========================================
# 4. CLOUDFRONT CDN (ORIGIN ACCESS CONTROL)
# ==========================================
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${local.name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend.id}"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "allow_cloudfront" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.s3_distribution.arn
        }
      }
    }]
  })
}

# ==========================================
# 5. OBSERVABILITY: LOGS, ALARMS & DASHBOARD
# ==========================================
resource "aws_cloudwatch_log_group" "lambda_log" {
  name              = "/aws/lambda/${aws_lambda_function.backend.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "apigw_access" {
  name              = "/aws/apigateway/${local.name}-access"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.backend.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "apigw_5xx" {
  alarm_name          = "${local.name}-apigw-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.api.id
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = local.name
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0, y = 0, width = 12, height = 6
        properties = {
          title   = "Lambda Metrics"
          region  = var.aws_region
          period  = 60
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.backend.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", ".", { stat = "p95" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12, y = 0, width = 12, height = 6
        properties = {
          title   = "API Gateway Metrics"
          region  = var.aws_region
          period  = 60
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.api.id],
            [".", "4xx", ".", "."],
            [".", "5xx", ".", "."],
            [".", "Latency", ".", ".", { stat = "p95" }]
          ]
        }
      }
    ]
  })
}

```

#### `terraform/outputs.tf`

```hcl
output "s3_bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "Name of the S3 Bucket hosting the frontend"
}

output "api_gateway_url" {
  value       = aws_apigatewayv2_api.api.api_endpoint
  description = "Base URL of API Gateway"
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.s3_distribution.domain_name
  description = "Public URL of CloudFront Distribution"
}

output "lambda_function_name" {
  value       = aws_lambda_function.backend.function_name
  description = "Name of the deployed Lambda function"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.s3_distribution.id
  description = "Distribution ID for CloudFront cache invalidation"
}

```

---

### Step 3: Initialize & Deploy Terraform

Run the deployment sequence from within the `terraform/` directory:

```bash
cd terraform

# 1. Initialize Terraform
terraform init

# 2. Review Execution Plan
terraform plan -var="pg_host=YOUR_EC2_PUBLIC_IP" -var="pg_password=YOUR_POSTGRES_PASSWORD"

# 3. Apply Configuration
terraform apply -var="pg_host=YOUR_EC2_PUBLIC_IP" -var="pg_password=YOUR_POSTGRES_PASSWORD"

```

Type `yes` when prompted. Copy the output values once execution finishes.

---

### Step 4: Build & Upload Frontend

Navigate back to the `frontend/` directory, inject your `api_gateway_url` output from Terraform, build the bundle, and push it to S3:

```bash
cd ../frontend

# Build React app with the API URL injected
VITE_API_URL=https://<API_GATEWAY_ID>.execute-api.us-east-1.amazonaws.com npm run build

# Upload compiled assets to the private S3 bucket
aws s3 sync dist/ s3://<S3_BUCKET_NAME_FROM_TERRAFORM>/ --delete

```

You can now visit your live app securely via HTTPS at `https://<CLOUDFRONT_DOMAIN_NAME>`.

---

### Step 5: Automate with GitHub Actions CI/CD

Create `.github/workflows/deploy.yml` in your repository:

```yaml
name: Deploy Notice Board (Terraform Stack)

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Build & Deploy Backend Code
        run: |
          pip install -r backend/requirements.txt -t backend/_build -q
          cp backend/lambda_function.py backend/_build/
          cd backend/_build && zip -r ../lambda.zip . && cd ../..
          aws lambda update-function-code \
            --function-name ${{ secrets.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://backend/lambda.zip

      - name: Build & Deploy Frontend Code
        run: |
          cd frontend
          npm ci
          VITE_API_URL=${{ secrets.VITE_API_URL }} npm run build
          aws s3 sync dist/ s3://${{ secrets.S3_BUCKET }}/ --delete

      - name: Invalidate CloudFront Cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
            --paths "/*"

```

Add these **Repository Secrets** under **Settings → Secrets and variables → Actions** in GitHub:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
* `LAMBDA_FUNCTION_NAME` *(from Terraform output)*
* `S3_BUCKET` *(from Terraform output)*
* `VITE_API_URL` *(from Terraform output)*
* `CF_DISTRIBUTION_ID` *(from Terraform output)*