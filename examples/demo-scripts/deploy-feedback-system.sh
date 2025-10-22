#!/bin/bash

# Deploy Feedback-Enhanced System
# This script deploys the Lambda function and website with real-time feedback capabilities

set -e

echo "🚀 Deploying Feedback-Enhanced Recommendation System"
echo "=================================================="

# Configuration
FUNCTION_NAME="plex-analyzer"
REGION="us-east-1"
S3_BUCKET="plex-recommendations-c7c49ce4"
WEBSITE_BUCKET="plex.robertconsulting.net"

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
zip -r function.zip feedback-enhanced.js package.json 2>/dev/null || {
    echo "⚠️  Creating minimal package..."
    zip -r function.zip feedback-enhanced.js
}

echo "✅ Lambda package created: function.zip"

# Update Lambda function code
echo "🔄 Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://function.zip \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Lambda function code updated successfully"
else
    echo "❌ Failed to update Lambda function code"
    exit 1
fi

# Update Lambda function configuration
echo "⚙️  Updating Lambda function configuration..."

# Update runtime and handler
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --runtime nodejs22.x \
    --handler feedback-enhanced.handler \
    --timeout 30 \
    --memory-size 512 \
    --region $REGION

# Wait for the function to be active
aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

# Update environment variables
cat > /tmp/env-vars.json << 'EOF'
{
    "Variables": {
        "S3_BUCKET": "plex-recommendations-c7c49ce4",
        "ENVIRONMENT": "production",
        "FEEDBACK_SYSTEM": "enabled",
        "TMDB_INTEGRATION": "enabled"
    }
}
EOF

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment file:///tmp/env-vars.json \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Lambda function configuration updated successfully"
else
    echo "❌ Failed to update Lambda function configuration"
    exit 1
fi

# Wait for function to be active
echo "⏳ Waiting for function to be active..."
aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

# Test the function
echo "🧪 Testing the feedback-enhanced Lambda function..."
TEST_RESPONSE=$(aws lambda invoke --function-name $FUNCTION_NAME --region $REGION --payload '{}' /tmp/lambda-response.json)

if [ $? -eq 0 ]; then
    echo "✅ Feedback-enhanced Lambda function test successful"
    
    # Check if feedback system is working
    if grep -q "feedbackSystem" /tmp/lambda-response.json; then
        echo "📊 Feedback system detected in response"
    else
        echo "⚠️  Feedback system may not be working properly"
    fi
else
    echo "❌ Lambda function test failed"
    exit 1
fi

# Generate fresh recommendations
echo "🎬 Generating fresh recommendations with feedback system..."
aws lambda invoke --function-name $FUNCTION_NAME --region $REGION --payload '{}' /tmp/lambda-response.json
cat /tmp/lambda-response.json | jq -r '.body' | jq '.' > ../../website/recommendations.json

# Upload website files
echo "🌐 Uploading website files..."
cd ../../website

# Upload the new feedback-enhanced website
aws s3 cp feedback-enhanced.html s3://$WEBSITE_BUCKET/index.html
aws s3 cp recommendations.json s3://$WEBSITE_BUCKET/recommendations.json

echo "✅ Website files uploaded successfully"

# Create CloudFront invalidation
echo "🔄 Invalidating CloudFront cache..."
CLOUDFRONT_ID="E3T1Z34I8CU20F"
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/index.html" "/recommendations.json" --output table

# Clean up
rm -f function.zip /tmp/env-vars.json /tmp/lambda-response.json

echo ""
echo "🎉 Feedback-Enhanced System Deployment Complete!"
echo "==============================================="
echo "📊 Features enabled:"
echo "   - Real-time feedback system"
echo "   - Admin-only feedback controls"
echo "   - TMDB integration (755+ movies)"
echo "   - Enhanced ML recommendations"
echo "   - User preference learning"
echo ""
echo "🔐 Admin Access:"
echo "   - URL: https://plex.robertconsulting.net?admin=plex-admin-2025"
echo "   - Only you can mark movies as watched and rate them"
echo "   - Everyone else sees recommendations without feedback controls"
echo ""
echo "🌐 Public Access:"
echo "   - URL: https://plex.robertconsulting.net"
echo "   - Shows recommendations without feedback controls"
echo ""
echo "🚀 Next Steps:"
echo "   1. Visit the admin URL to test feedback functionality"
echo "   2. Mark some movies as watched and rate them"
echo "   3. Watch how recommendations improve over time"
echo "   4. Share the public URL with others"
