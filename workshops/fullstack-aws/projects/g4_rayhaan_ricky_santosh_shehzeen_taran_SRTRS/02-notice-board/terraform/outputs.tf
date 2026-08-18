output "s3_bucket_name" {
  description = "S3 bucket holding the built frontend"
  value       = aws_s3_bucket.frontend.id
}

output "s3_website_endpoint" {
  description = "Tier 1/2 public S3 website URL (http://...). Stops being the primary URL once Tier 3 CloudFront is added."
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "api_base_url" {
  description = "Base URL for the API Gateway HTTP API - use as VITE_API_URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "lambda_function_name" {
  description = "Lambda function name - used by the GitHub Actions workflow (LAMBDA_FUNCTION_NAME secret)"
  value       = aws_lambda_function.api.function_name
}

output "mongo_public_ip" {
  description = "Public IP of the MongoDB EC2 instance, for SSH/admin access"
  value       = aws_instance.mongo.public_ip
}

output "mongo_private_ip" {
  description = "Private IP the Lambda function connects to (MONGO_HOST)"
  value       = aws_instance.mongo.private_ip
}