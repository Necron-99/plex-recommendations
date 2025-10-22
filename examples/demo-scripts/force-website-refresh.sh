#!/bin/bash

# Force Complete Website Refresh
# This script forces a complete refresh of the website with new recommendations

set -e

echo "🔄 Forcing Complete Website Refresh"
echo "=================================="

# Configuration
S3_BUCKET="plex-recommendations-c7c49ce4"
CLOUDFRONT_ID="E3T1Z34I8CU20F"
FUNCTION_NAME="plex-analyzer"
REGION="us-east-1"

# Generate fresh recommendations
echo "🎬 Generating fresh recommendations..."
aws lambda invoke --function-name $FUNCTION_NAME --region $REGION --payload '{}' /tmp/lambda-response.json
cat /tmp/lambda-response.json | jq -r '.body' | jq '.' > website/recommendations.json

echo "✅ Fresh recommendations generated"

# Upload files with no-cache headers
echo "☁️ Uploading files to S3 with no-cache headers..."
aws s3 cp website/index.html s3://$S3_BUCKET/website/index.html --cache-control "no-cache, no-store, must-revalidate"
aws s3 cp website/recommendations.json s3://$S3_BUCKET/website/recommendations.json --cache-control "no-cache, no-store, must-revalidate"

echo "✅ Files uploaded with no-cache headers"

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*" --output table

echo "✅ CloudFront cache invalidated"

# Display new timestamp
NEW_TIMESTAMP=$(cat website/recommendations.json | jq -r '.generatedAt')
echo ""
echo "🎉 Website Refresh Complete!"
echo "=========================="
echo "📅 New timestamp: $NEW_TIMESTAMP"
echo "🌐 Website: https://plex.robertconsulting.net"
echo ""
echo "⏳ Wait 2-3 minutes for CloudFront invalidation to complete"
echo "🔄 Then clear your browser cache (Ctrl+F5 or Cmd+Shift+R)"

# Clean up
rm -f /tmp/lambda-response.json
