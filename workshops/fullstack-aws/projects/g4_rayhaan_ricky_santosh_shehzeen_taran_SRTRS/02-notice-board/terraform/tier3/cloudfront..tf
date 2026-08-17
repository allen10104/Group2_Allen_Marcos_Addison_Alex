# ---------------------------------------------------------------------------
# TIER 3 - CloudFront + Origin Access Control
#
# How to activate this file:
#   1. In ../main.tf, DELETE (or comment out) these two resources:
#        - resource "aws_s3_bucket_public_access_block" "frontend"
#        - resource "aws_s3_bucket_policy" "frontend_public_read"
#      They are replaced by the private/CloudFront-only versions below.
#   2. Move this file up a directory:  mv terraform/tier3/cloudfront.tf terraform/cloudfront.tf
#   3. terraform init (no new providers, but harmless) && terraform apply
#
# Why: an Origin Access Control only works against the S3 bucket's REST API
# endpoint (bucket_regional_domain_name), not the "static website hosting"
# endpoint - so once CloudFront is in front, the bucket goes fully private
# and CloudFront becomes the only path in. Hitting the old S3 website URL
# afterwards should now return 403/Access Denied - that's the Tier 3
# acceptance check "S3 bucket is no longer publicly accessible directly".
# ---------------------------------------------------------------------------

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.name_prefix}-notice-board-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  comment             = "${var.name_prefix} notice board"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-${aws_s3_bucket.frontend.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods          = ["GET", "HEAD"]
    target_origin_id        = "s3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy  = "redirect-to-https"
    compress                = true

    # Managed-CachingOptimized policy (AWS-provided, no need to define our own)
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  # SPA fallback: React Router / client-side routes should still load index.html
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
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.name_prefix}-notice-board-cdn"
  }
}

# Bucket becomes fully private - CloudFront (via OAC) is the only reader
resource "aws_s3_bucket_public_access_block" "frontend_private" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "frontend_cloudfront_only" {
  bucket     = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend_private]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipalReadOnly"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}

output "cloudfront_domain_name" {
  description = "HTTPS URL to open the app through CloudFront - this becomes your primary frontend URL"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "Used by the GitHub Actions cache-invalidation step (CLOUDFRONT_DISTRIBUTION_ID secret)"
  value       = aws_cloudfront_distribution.frontend.id
}