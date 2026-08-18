# TODO(step 5): output "s3_website_url"   — the S3 static website endpoint (open this in your browser)
# TODO(step 5): output "api_url"          — API Gateway invoke URL (set as VITE_API_URL when building the frontend)
# TODO(step 5): output "s3_bucket"        — bucket name (used to `aws s3 sync`)
# TODO(step 5): output "lambda_function_name" — used later in Tier 2's GitHub Actions workflow

output "cloudfront_url" {
  description = "Frontend URL — open this in your browser"
  value       = "https://${aws_cloudfront_distribution.cdn.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID — used to invalidate cache after a frontend deploy"
  value       = aws_cloudfront_distribution.cdn.id
}

output "api_url" {
  description = "API Gateway URL — set as VITE_API_URL when building the frontend"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "s3_bucket" {
  description = "S3 bucket name — used for `aws s3 sync`"
  value       = aws_s3_bucket.frontend.bucket
}

output "lambda_function_name" {
  description = "Lambda function name — used later in Tier 2's GitHub Actions workflow"
  value       = aws_lambda_function.api.function_name
}