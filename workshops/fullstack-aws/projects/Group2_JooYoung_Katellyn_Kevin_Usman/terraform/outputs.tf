output "cloudfront_url" {
  description = "The one URL for everything: frontend, /api/*, and /uploads/*"
  value       = "https://${aws_cloudfront_distribution.cdn.domain_name}"
}

output "s3_bucket" {
  description = "Frontend S3 bucket name — used by deploy scripts / GitHub Actions"
  value       = aws_s3_bucket.frontend.bucket
}

output "uploads_bucket" {
  description = "Uploads S3 bucket name"
  value       = aws_s3_bucket.uploads.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID — used to invalidate the cache after each deploy"
  value       = aws_cloudfront_distribution.cdn.id
}

output "ec2_instance_id" {
  description = "EC2 instance ID — used to target `aws ssm send-command` for backend deploys"
  value       = aws_instance.app.id
}

output "ec2_public_dns" {
  description = "EC2 instance public DNS (useful for debugging directly, bypassing CloudFront)"
  value       = aws_instance.app.public_dns
}
