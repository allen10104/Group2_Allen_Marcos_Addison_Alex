output "api_url" {
  description = "API Gateway base URL - this becomes VITE_API_URL"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "s3_website_url" {
  description = "Public S3 static website URL"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "s3_bucket_name" {
  description = "Bucket name - GitHub Secret S3_BUCKET"
  value       = aws_s3_bucket.frontend.bucket
}

output "lambda_function_name" {
  description = "Lambda name - GitHub Secret LAMBDA_FUNCTION_NAME"
  value       = aws_lambda_function.api.function_name
}



output "cloudfront_url" {
  description = "HTTPS URL for the app - this is the one you submit"
  value       = "https://${aws_cloudfront_distribution.app.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "Distribution ID - GitHub Secret CF_DISTRIBUTION_ID"
  value       = aws_cloudfront_distribution.app.id
}
