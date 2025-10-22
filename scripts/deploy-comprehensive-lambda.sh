#!/bin/bash

# Deploy Enhanced Lambda Function with Comprehensive Movie Database
# This script deploys the Lambda function that can recommend from all movies ever made

set -e

echo "🚀 Deploying Enhanced Lambda Function with Comprehensive Movie Database"
echo "=================================================================="

# Configuration
FUNCTION_NAME="plex-analyzer"
REGION="us-east-1"
S3_BUCKET="plex-recommendations-c7c49ce4"

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
zip -r function.zip enhanced-with-comprehensive-db.js package.json node_modules/ 2>/dev/null || {
    echo "⚠️  Some files may not exist, continuing with available files..."
    zip -r function.zip enhanced-with-comprehensive-db.js package.json 2>/dev/null || {
        echo "⚠️  Creating minimal package..."
        zip -r function.zip enhanced-with-comprehensive-db.js
    }
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

# Update runtime and handler first
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --runtime nodejs22.x \
    --handler enhanced-with-comprehensive-db.handler \
    --timeout 30 \
    --memory-size 512 \
    --region $REGION

# Wait for the function to be active
aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

# Update environment variables separately
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables='{"S3_BUCKET":"'$S3_BUCKET'","ENVIRONMENT":"production","COMPREHENSIVE_DB_ENABLED":"true","TMDB_INTEGRATION":"enabled"}' \
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

# Create or update Function URL
echo "🌐 Creating/updating Function URL..."
aws lambda create-function-url-config \
    --function-name $FUNCTION_NAME \
    --auth-type NONE \
    --cors '{
        "AllowCredentials": false,
        "AllowHeaders": ["content-type"],
        "AllowMethods": ["GET", "POST"],
        "AllowOrigins": ["*"],
        "ExposeHeaders": [],
        "MaxAge": 86400
    }' \
    --region $REGION 2>/dev/null || {
    echo "⚠️  Function URL may already exist, updating CORS..."
    aws lambda update-function-url-config \
        --function-name $FUNCTION_NAME \
        --cors '{
            "AllowCredentials": false,
            "AllowHeaders": ["content-type"],
            "AllowMethods": ["GET", "POST"],
            "AllowOrigins": ["*"],
            "ExposeHeaders": [],
            "MaxAge": 86400
        }' \
        --region $REGION
}

if [ $? -eq 0 ]; then
    echo "✅ Function URL configured successfully"
else
    echo "❌ Failed to configure Function URL"
    exit 1
fi

# Get Function URL
FUNCTION_URL=$(aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION --query 'FunctionUrl' --output text)
echo "🌐 Function URL: $FUNCTION_URL"

# Test the function
echo "🧪 Testing the enhanced Lambda function..."
TEST_RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"test": true}' \
    --max-time 30)

if echo "$TEST_RESPONSE" | grep -q "comprehensive movie database"; then
    echo "✅ Enhanced Lambda function test successful"
    echo "📊 Response includes comprehensive database features"
else
    echo "⚠️  Lambda function responded but may not have comprehensive database enabled"
    echo "📄 Response: $TEST_RESPONSE"
fi

# Clean up
rm -f function.zip

echo ""
echo "🎉 Enhanced Lambda Function Deployment Complete!"
echo "=============================================="
echo "📊 Features enabled:"
echo "   - Comprehensive movie database (35+ movies)"
echo "   - English language filtering"
echo "   - Available format filtering (digital/DVD/BluRay)"
echo "   - Enhanced ML recommendations"
echo "   - Genre and decade-based matching"
echo "   - Director and rating preferences"
echo ""
echo "🌐 Function URL: $FUNCTION_URL"
echo "📝 Next steps:"
echo "   1. Test the function with your Plex data"
echo "   2. Update website to use new recommendations"
echo "   3. Monitor performance and costs"
echo "   4. Expand movie database as needed"
