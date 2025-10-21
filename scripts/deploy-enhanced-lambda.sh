#!/bin/bash

# Deploy Enhanced Lambda Function with ML Capabilities
# This script deploys the enhanced Lambda function with lightweight ML recommendations

set -e

echo "🚀 Deploying Enhanced Plex Analyzer with ML Capabilities"
echo "=================================================="

# Configuration
FUNCTION_NAME="plex-analyzer"
LAMBDA_ROLE_ARN="arn:aws:iam::228480945348:role/PlexRecommendationsLambdaRole"
S3_BUCKET="plex-recommendations-c7c49ce4"
AWS_REGION="us-east-1"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Navigate to Lambda directory
cd "$(dirname "$0")/../lambda/plex-analyzer"

echo "📦 Preparing Lambda deployment package..."

# Create deployment package
rm -f plex-analyzer.zip
zip -r plex-analyzer.zip . -x "*.git*" "*.DS_Store*" "test*" "*.md"

echo "✅ Deployment package created: plex-analyzer.zip"

# Create environment variables JSON file
cat > env-vars.json << EOF
{
  "S3_BUCKET": "$S3_BUCKET",
  "AWS_REGION": "$AWS_REGION",
  "ML_ENABLED": "true"
}
EOF

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://plex-analyzer.zip \
        --region "$AWS_REGION"
    
    echo "✅ Lambda function code updated"
    
    # Update function configuration for ML capabilities
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --memory-size 512 \
        --timeout 60 \
        --region "$AWS_REGION"
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment 'Variables={"S3_BUCKET":"'$S3_BUCKET'","AWS_REGION":"'$AWS_REGION'","ML_ENABLED":"true"}' \
        --region "$AWS_REGION"
    
    echo "✅ Lambda function configuration updated for ML"
    
else
    echo "🆕 Creating new Lambda function..."
    
    # Create new function
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime nodejs18.x \
        --role "$LAMBDA_ROLE_ARN" \
        --handler enhanced-index.handler \
        --zip-file fileb://plex-analyzer.zip \
        --memory-size 512 \
        --timeout 60 \
        --region "$AWS_REGION"
    
    echo "✅ Lambda function created"
    
    # Add environment variables after creation
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment 'Variables={"S3_BUCKET":"'$S3_BUCKET'","AWS_REGION":"'$AWS_REGION'","ML_ENABLED":"true"}' \
        --region "$AWS_REGION"
    
    echo "✅ Environment variables added"
fi

# Get function URL for testing
echo "🔗 Getting function URL..."
FUNCTION_URL=$(aws lambda get-function-url-config --function-name "$FUNCTION_NAME" --region "$AWS_REGION" --query 'FunctionUrl' --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "🔗 Creating function URL..."
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name "$FUNCTION_NAME" \
        --auth-type NONE \
        --cors '{"AllowCredentials":false,"AllowHeaders":["content-type"],"AllowMethods":["GET","POST","OPTIONS"],"AllowOrigins":["*"],"ExposeHeaders":[],"MaxAge":86400}' \
        --region "$AWS_REGION" \
        --query 'FunctionUrl' \
        --output text)
fi

echo "✅ Function URL: $FUNCTION_URL"

# Clean up temporary files
rm -f env-vars.json

# Test the function
echo "🧪 Testing enhanced Lambda function..."
RESPONSE=$(curl -s "$FUNCTION_URL" || echo "Error: Failed to connect")

if echo "$RESPONSE" | grep -q "mlEnhancements"; then
    echo "✅ ML enhancements detected in response"
else
    echo "⚠️  ML enhancements not detected - function may need configuration"
fi

echo ""
echo "🎉 Enhanced Lambda deployment completed!"
echo "=================================================="
echo "📊 Function Details:"
echo "   Name: $FUNCTION_NAME"
echo "   URL: $FUNCTION_URL"
echo "   Memory: 512 MB"
echo "   Timeout: 60 seconds"
echo "   ML Enabled: Yes"
echo ""
echo "💰 Cost Estimate:"
echo "   Base Lambda: ~$0.20/month"
echo "   ML Processing: +$1-3/month"
echo "   Total: ~$1.20-3.20/month"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update website/index.html with the new function URL"
echo "   2. Test the ML recommendations in the web interface"
echo "   3. Monitor costs in AWS Cost Explorer"
echo ""
echo "📝 To update the website URL:"
echo "   Edit website/index.html and replace the fetch URL with:"
echo "   $FUNCTION_URL"
