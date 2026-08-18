output "cloudfront_url" {
  description = "HTTPS URL for the frontend, served via CloudFront"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed for cache invalidation in CI)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "lambda_api_url" {
  description = "API Gateway URL for the Lambda-backed API (separate from the EC2 backend, not yet the live app's URL)"
  value       = aws_apigatewayv2_api.backend.api_endpoint
}

output "lambda_function_name" {
  description = "Lambda function name (needed for CI to update its code)"
  value       = aws_lambda_function.backend.function_name
}
