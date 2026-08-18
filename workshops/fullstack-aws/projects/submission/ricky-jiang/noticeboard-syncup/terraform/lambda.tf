# Lambda + API Gateway experiment - entirely additive to the working EC2
# deployment. To undo this whole phase: delete this file and run
# `terraform apply` - it cleanly destroys just these resources, since
# nothing else in main.tf references anything defined here.

resource "aws_lambda_function" "backend" {
  function_name = "${local.name}-backend"
  filename      = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")

  role    = var.lambda_exec_role_arn
  handler = "app.lambda_handler.handler"
  runtime = "python3.12"
  timeout = 15

  environment {
    variables = {
      MONGODB_URI                  = var.mongodb_uri
      MONGODB_DB_NAME               = "syncup"
      JWT_SECRET                    = var.lambda_jwt_secret
      JWT_ALGORITHM                 = "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES   = "30"
      REFRESH_TOKEN_EXPIRE_DAYS     = "7"
      CORS_ORIGINS                  = var.lambda_cors_origins
      SEED_MANAGER_EMAIL            = "admin@example.com"
      SEED_MANAGER_PASSWORD         = "change-me"
    }
  }

  tags = {
    Name = "${local.name}-backend-lambda"
  }
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "backend" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "backend_proxy" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "backend_root" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}
