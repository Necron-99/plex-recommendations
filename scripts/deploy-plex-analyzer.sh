#!/bin/bash

# Deploy Plex Analyzer Lambda Function
# Creates and deploys the AWS Lambda function for Plex data analysis

echo "🚀 Deploying Plex Analyzer Lambda Function..."

# Navigate to the lambda directory
cd ../lambda/plex-analyzer

# Check if we're in the right directory
if [ ! -f "index.js" ]; then
    echo "❌ Error: index.js not found. Please run this script from the scripts/ directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create deployment package
echo "📦 Creating deployment package..."
zip -r plex-analyzer.zip index.js node_modules/ package.json

# Create the Lambda function
echo "🚀 Creating Plex analyzer Lambda function..."
aws lambda create-function \
    --function-name robert-consulting-plex-analyzer \
    --runtime nodejs20.x \
    --role arn:aws:iam::228480945348:role/robert-consulting-dashboard-api-role \
    --handler index.handler \
    --zip-file fileb://plex-analyzer.zip \
    --timeout 300 \
    --memory-size 512 \
    --region us-east-1 \
    --description "Analyzes Plex watch history and generates movie recommendations"

# Set environment variables
echo "🔧 Setting environment variables..."
aws lambda update-function-configuration \
    --function-name robert-consulting-plex-analyzer \
    --environment Variables='{"S3_BUCKET":"robert-consulting-cache","AWS_REGION":"us-east-1"}' \
    --region us-east-1

# Test the function
echo "🧪 Testing the Lambda function..."
aws lambda invoke \
    --function-name robert-consulting-plex-analyzer \
    --region us-east-1 \
    --payload '{}' \
    response.json

echo "📊 Function response:"
cat response.json | jq '.'

# Clean up
rm plex-analyzer.zip response.json

echo "✅ Plex analyzer Lambda function deployed successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Run the local data exporter: cd ../../scripts && ./run-exporter.sh"
echo "2. Test the analyzer: aws lambda invoke --function-name robert-consulting-plex-analyzer --payload '{}' response.json"
echo "3. Open the website: open ../../website/index.html"
