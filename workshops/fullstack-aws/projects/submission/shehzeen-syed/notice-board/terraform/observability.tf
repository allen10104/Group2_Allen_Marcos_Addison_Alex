# Tier 4: CloudWatch logs, alarms, dashboard, saved Logs Insights queries.
# Only created when enable_observability = true.
# Apply with: terraform apply -var="enable_observability=true"
#
# IMPORTANT: if the Lambda has already been invoked (Tier 1-3 testing),
# AWS auto-created a /aws/lambda/<fn> log group with no retention limit.
# Import it before applying, or this will fail with "already exists":
#
#   terraform import aws_cloudwatch_log_group.lambda[0] /aws/lambda/<name_prefix>-notice-board-api

resource "aws_cloudwatch_log_group" "lambda" {
  count             = var.enable_observability ? 1 : 0
  name              = "/aws/lambda/${aws_lambda_function.backend.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "apigw_access" {
  count             = var.enable_observability ? 1 : 0
  name              = "/aws/apigateway/${var.name_prefix}-notice-board-access"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count               = var.enable_observability ? 1 : 0
  alarm_name          = "${var.name_prefix}-notice-board-lambda-errors"
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
  count               = var.enable_observability ? 1 : 0
  alarm_name          = "${var.name_prefix}-notice-board-apigw-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.this.id
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  count          = var.enable_observability ? 1 : 0
  dashboard_name = "${var.name_prefix}-notice-board"

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
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.backend.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.backend.function_name],
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.backend.function_name, { stat = "p95" }],
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
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.this.id],
            ["AWS/ApiGateway", "4xx", "ApiId", aws_apigatewayv2_api.this.id],
            ["AWS/ApiGateway", "5xx", "ApiId", aws_apigatewayv2_api.this.id],
            ["AWS/ApiGateway", "Latency", "ApiId", aws_apigatewayv2_api.this.id],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "CloudFront"
          # CloudFront metrics only exist in us-east-1, regardless of aws_region.
          region = "us-east-1"
          view   = "timeSeries"
          metrics = var.enable_cloudfront ? [
            ["AWS/CloudFront", "4xxErrorRate", "DistributionId", aws_cloudfront_distribution.frontend[0].id, "Region", "Global"],
            ["AWS/CloudFront", "5xxErrorRate", "DistributionId", aws_cloudfront_distribution.frontend[0].id, "Region", "Global"],
          ] : []
        }
      },
    ]
  })
}

resource "aws_cloudwatch_query_definition" "recent_5xx" {
  count           = var.enable_observability ? 1 : 0
  name            = "${var.name_prefix}-notice-board-5xx-recent"
  log_group_names = [aws_cloudwatch_log_group.apigw_access[0].name]

  query_string = <<-EOT
    fields @timestamp, status, httpMethod, routeKey, ip
    | filter status >= 500
    | sort @timestamp desc
    | limit 50
  EOT
}

resource "aws_cloudwatch_query_definition" "lambda_p95" {
  count           = var.enable_observability ? 1 : 0
  name            = "${var.name_prefix}-notice-board-lambda-p95"
  log_group_names = [aws_cloudwatch_log_group.lambda[0].name]

  query_string = <<-EOT
    filter @type = "REPORT"
    | stats pct(@duration, 95) as p95_duration by bin(5m)
  EOT
}
