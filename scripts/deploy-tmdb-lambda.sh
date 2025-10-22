#!/bin/bash

# Deploy TMDB-Enhanced Lambda Function
# This script deploys the Lambda function with real TMDB API integration

set -e

echo "🚀 Deploying TMDB-Enhanced Lambda Function"
echo "=========================================="

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
zip -r function.zip enhanced-with-tmdb-api.js package.json 2>/dev/null || {
    echo "⚠️  Creating minimal package..."
    zip -r function.zip enhanced-with-tmdb-api.js
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
    --handler enhanced-with-tmdb-api.handler \
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
        "TMDB_INTEGRATION": "enabled",
        "COMPREHENSIVE_DB_ENABLED": "true"
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
echo "🧪 Testing the TMDB-enhanced Lambda function..."
TEST_RESPONSE=$(aws lambda invoke --function-name $FUNCTION_NAME --region $REGION --payload '{}' /tmp/lambda-response.json)

if [ $? -eq 0 ]; then
    echo "✅ TMDB-enhanced Lambda function test successful"
    
    # Check if TMDB integration is working
    if grep -q "tmdbIntegration" /tmp/lambda-response.json; then
        echo "📊 TMDB integration detected in response"
    else
        echo "⚠️  TMDB integration may not be working properly"
    fi
else
    echo "❌ Lambda function test failed"
    exit 1
fi

# Clean up
rm -f function.zip /tmp/env-vars.json /tmp/lambda-response.json

echo ""
echo "🎉 TMDB-Enhanced Lambda Function Deployment Complete!"
echo "===================================================="
echo "📊 Features enabled:"
echo "   - Real TMDB API integration"
echo "   - 755+ movies from TMDB database"
echo "   - English language filtering"
echo "   - Available format filtering"
echo "   - Enhanced ML recommendations"
echo "   - Genre and decade-based matching"
echo "   - Director and rating preferences"
echo ""
echo "🌐 Next steps:"
echo "   1. Test the function with your Plex data"
echo "   2. Update website to use new TMDB recommendations"
echo "   3. Monitor performance and costs"
echo "   4. Expand movie database as needed"
