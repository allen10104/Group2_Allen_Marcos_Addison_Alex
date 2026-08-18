This guide covers the manual deployment of **Version 1** (AWS S3 + Lambda + API Gateway + MongoDB Atlas) using the AWS CLI and AWS Management Console. Replace `YOUR_STUDENT_NAME` and `YOUR_ACCOUNT_ID` with your actual credentials.

---

### Tier 1: Manual Setup & Deployment

#### 1. Set Up MongoDB Atlas

1. Log into **MongoDB Atlas** and create a cluster.
2. Under **Database Access**, create a user with `Read and write to any database` permissions.
3. Under **Network Access**, click **Add IP Address** and select **Allow Access from Anywhere (`0.0.0.0/0`)**.
4. Click **Connect** → **Drivers** (Python) and copy your URI connection string. It will look like:
```text
mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/noticeboard?retryWrites=true&w=majority

```



#### 2. Package Backend Lambda Function

Run the following locally in your project root to prepare the deployment zip:

```bash
# Prepare python dependencies in a target build folder
pip install -r backend/requirements.txt -t backend/_build -q

# Copy the Lambda handler code into the build package
cp backend/lambda_function.py backend/_build/

# Zip the payload
cd backend/_build && zip -r ../lambda.zip . && cd ../..

```

#### 3. Create IAM Role & Deploy Lambda

```bash
# 1. Create Lambda Execution Role
aws iam create-role \
  --role-name student-YOUR_STUDENT_NAME-noticeboard-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 2. Attach basic execution policy for CloudWatch logs
aws iam attach-role-policy \
  --role-name student-YOUR_STUDENT_NAME-noticeboard-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 3. Create the Lambda Function
aws lambda create-function \
  --function-name student-YOUR_STUDENT_NAME-notice-board-backend \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/student-YOUR_STUDENT_NAME-noticeboard-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://backend/lambda.zip \
  --environment "Variables={MONGODB_URI='your-atlas-connection-string'}"

```

#### 4. Configure API Gateway (HTTP API)

```bash
# 1. Create HTTP API
aws apigatewayv2 create-api \
  --name student-YOUR_STUDENT_NAME-noticeboard-api \
  --protocol-type HTTP \
  --cors-configuration "AllowOrigins='*',AllowMethods='*',AllowHeaders='*'"

# 2. Create Target Integration pointing to Lambda
aws apigatewayv2 create-integration \
  --api-id YOUR_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:student-YOUR_STUDENT_NAME-notice-board-backend \
  --payload-format-version "2.0"

# 3. Create Catch-All Route
aws apigatewayv2 create-route \
  --api-id YOUR_API_ID \
  --route-key "ANY /{proxy+}" \
  --target "integrations/YOUR_INTEGRATION_ID"

# 4. Grant API Gateway permission to trigger Lambda
aws lambda add-permission \
  --function-name student-YOUR_STUDENT_NAME-notice-board-backend \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:YOUR_API_ID/*/*"

```

*(Your backend endpoint is now `https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com`)*

#### 5. Build and Deploy Static Frontend on S3

```bash
# 1. Create Bucket
aws s3 api create-bucket \
  --bucket student-YOUR_STUDENT_NAME-notice-board-frontend \
  --region us-east-1

# 2. Build Frontend with API Gateway URL
cd frontend
npm ci
VITE_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com npm run build

# 3. Upload built files to S3
aws s3 sync dist/ s3://student-YOUR_STUDENT_NAME-notice-board-frontend/ --delete

```

---

### Tier 2: GitHub Actions Automated CI/CD

Create `.github/workflows/deploy.yml` in your repository. Configure GitHub Secrets for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `LAMBDA_FUNCTION_NAME`, `VITE_API_URL`, and `S3_BUCKET`.

```yaml
name: Deploy Notice Board (Manual Stack)

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

      - name: Deploy Backend
        run: |
          pip install -r backend/requirements.txt -t backend/_build -q
          cp backend/lambda_function.py backend/_build/
          cd backend/_build && zip -r ../lambda.zip . && cd ../..
          aws lambda update-function-code \
            --function-name ${{ secrets.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://backend/lambda.zip

      - name: Deploy Frontend
        run: |
          cd frontend
          npm ci
          VITE_API_URL=${{ secrets.VITE_API_URL }} npm run build
          aws s3 sync dist/ s3://${{ secrets.S3_BUCKET }}/ --delete

```

---

### Tier 3: Add CloudFront CDN & Secure S3 Access

1. **Create Distribution via Console / CLI:**
* Go to **CloudFront Console** → **Create Distribution**.
* Set Origin Domain to your S3 bucket's regional domain name.
* Under **Origin Access**, select **Origin Access Control (OAC)** and create a new control setting.
* Save and copy the generated **S3 Bucket Policy** attached by CloudFront.


2. **Apply Policy to S3:**
Apply the policy directly in S3 Bucket Settings under **Bucket Policy** to make sure the bucket is strictly private to the public, accepting reads only via CloudFront.
3. **Add Cache Invalidation Step:**
Add a final step to `.github/workflows/deploy.yml` and store `CF_DISTRIBUTION_ID` in your repository secrets:
```yaml
      - name: Invalidate CloudFront Cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
            --paths "/*"

```



---

### Tier 4: Observability with CloudWatch

1. **Set Log Retention:**
Enforce the 14-day retention requirement on the auto-generated Lambda log group:
```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/student-YOUR_STUDENT_NAME-notice-board-backend \
  --retention-in-days 14

```


2. **Create CloudWatch Metric Alarms:**
```bash
# 1. Alarm for Lambda Exec Errors (>0)
aws cloudwatch put-metric-alarm \
  --alarm-name "student-YOUR_STUDENT_NAME-lambda-errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=student-YOUR_STUDENT_NAME-notice-board-backend

# 2. Alarm for API Gateway 5xx Errors (>0)
aws cloudwatch put-metric-alarm \
  --alarm-name "student-YOUR_STUDENT_NAME-apigw-5xx" \
  --metric-name 5xx \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=ApiId,Value=YOUR_API_ID

```