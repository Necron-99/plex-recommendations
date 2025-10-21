#!/bin/bash

# Create IAM Role for Plex Recommendations Lambda Function
# This script creates the necessary IAM role and policies for the Lambda function

set -e

echo "🔐 Creating IAM Role for Plex Recommendations Lambda"
echo "=================================================="

# Configuration
ROLE_NAME="PlexRecommendationsLambdaRole"
POLICY_NAME="PlexRecommendationsLambdaPolicy"
S3_BUCKET="your-s3-bucket-name"  # Replace with your actual bucket name

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $ACCOUNT_ID"

# Create trust policy for Lambda
echo "🔑 Creating trust policy..."
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
echo "👤 Creating IAM role: $ROLE_NAME"
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "⚠️  Role $ROLE_NAME already exists"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://trust-policy.json \
        --description "Role for Plex Recommendations Lambda function"
    
    echo "✅ IAM role created: $ROLE_NAME"
fi

# Create custom policy for S3 access
echo "📜 Creating custom policy for S3 access..."
cat > lambda-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET",
        "arn:aws:s3:::$S3_BUCKET/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

# Attach custom policy
echo "📋 Attaching custom policy to role..."
if aws iam get-policy --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME" > /dev/null 2>&1; then
    echo "⚠️  Policy $POLICY_NAME already exists, updating..."
    aws iam create-policy-version \
        --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME" \
        --policy-document file://lambda-policy.json \
        --set-as-default
else
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://lambda-policy.json \
        --description "Policy for Plex Recommendations Lambda function"
    
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"
fi

# Attach AWS managed policy for basic Lambda execution
echo "🔗 Attaching AWS managed policy for Lambda execution..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

echo "✅ Policies attached to role"

# Wait for role to be ready
echo "⏳ Waiting for role to be ready..."
sleep 10

# Get role ARN
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

echo ""
echo "🎉 IAM Role Setup Complete!"
echo "=================================================="
echo "📋 Role Details:"
echo "   Role Name: $ROLE_NAME"
echo "   Role ARN: $ROLE_ARN"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your deployment script with this role ARN:"
echo "      LAMBDA_ROLE_ARN=\"$ROLE_ARN\""
echo ""
echo "   2. Update your S3 bucket name in the deployment script:"
echo "      S3_BUCKET=\"$S3_BUCKET\""
echo ""
echo "   3. Deploy your Lambda function:"
echo "      ./scripts/deploy-enhanced-lambda.sh"
echo ""
echo "📊 Permissions Granted:"
echo "   ✅ S3 access to bucket: $S3_BUCKET"
echo "   ✅ CloudWatch Logs for monitoring"
echo "   ✅ Basic Lambda execution"
echo ""
echo "💰 Cost Impact:"
echo "   ✅ No additional cost for IAM role"
echo "   ✅ Minimal permissions (principle of least privilege)"
echo ""

# Clean up temporary files
rm -f trust-policy.json lambda-policy.json

echo "🧹 Temporary files cleaned up"
echo "✅ Setup complete!"
