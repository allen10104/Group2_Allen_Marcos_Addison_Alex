output "s3_bucket_name" {
  value = aws_s3_bucket.frontend.id
}

output "s3_website_url" {
  description = "Direct S3 website URL. HTTP only; used in Tier 1-2 before CloudFront exists."
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "api_url" {
  description = "API Gateway invoke URL. Set as VITE_API_URL when building the frontend."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "lambda_function_name" {
  value = aws_lambda_function.backend.function_name
}

output "cloudfront_domain_name" {
  description = "Set once enable_cloudfront = true. HTTPS URL for the app."
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.frontend[0].domain_name : null
}

output "cloudfront_distribution_id" {
  description = "Set once enable_cloudfront = true. Used by the GitHub Actions invalidation step."
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.frontend[0].id : null
}
