#!/bin/bash

# Update Comprehensive Movie Recommendations
# This script generates fresh recommendations using the comprehensive movie database

set -e

echo "🎬 Updating Comprehensive Movie Recommendations"
echo "=============================================="

# Configuration
FUNCTION_NAME="plex-analyzer"
REGION="us-east-1"
S3_BUCKET="plex-recommendations-c7c49ce4"
WEBSITE_DIR="website"

# Get Function URL
FUNCTION_URL=$(aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION --query 'FunctionUrl' --output text 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Function URL not found. Creating one..."
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
        --region $REGION
    
    FUNCTION_URL=$(aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION --query 'FunctionUrl' --output text)
fi

echo "🌐 Function URL: $FUNCTION_URL"

# Generate fresh recommendations
echo "🔄 Generating fresh recommendations..."
RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{}' \
    --max-time 60)

if [ $? -ne 0 ]; then
    echo "❌ Failed to get recommendations from Lambda function"
    exit 1
fi

# Parse the response
echo "$RESPONSE" | jq -r '.body' > /tmp/response-body.json
RECOMMENDATIONS=$(cat /tmp/response-body.json)

# Save recommendations to website directory
echo "💾 Saving recommendations to website..."
echo "$RECOMMENDATIONS" > "$WEBSITE_DIR/recommendations.json"

# Upload to S3
echo "☁️ Uploading to S3..."
aws s3 cp "$WEBSITE_DIR/recommendations.json" "s3://$S3_BUCKET/website/recommendations.json"

# Get CloudFront distribution ID
CLOUDFRONT_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='Plex Recommendations Website'].Id" --output text)

if [ ! -z "$CLOUDFRONT_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_ID \
        --paths "/recommendations.json" "/index.html" \
        --output table
else
    echo "⚠️ CloudFront distribution not found"
fi

# Display summary
echo ""
echo "🎉 Comprehensive Recommendations Updated!"
echo "========================================"
echo "📊 Summary:"
echo "$RECOMMENDATIONS" | jq -r '.summary | "   - Total movies analyzed: \(.totalMovies)", "   - Average rating: \(.averageRating)", "   - Top genre: \(.topGenres[0].genre // "N/A")", "   - Total recommendations: \(.totalRecommendations)"'

echo ""
echo "🎬 Comprehensive Database:"
echo "$RECOMMENDATIONS" | jq -r '.comprehensiveDatabase | "   - Movies in database: \(.totalMoviesInDatabase)", "   - English movies: \(.englishMovies)", "   - Available movies: \(.availableMovies)", "   - Recommendations generated: \(.recommendationsGenerated)"'

echo ""
echo "🤖 ML Enhancements:"
echo "$RECOMMENDATIONS" | jq -r '.mlEnhancements | "   - Content-based: \(.contentBasedRecommendations)", "   - Collaborative: \(.collaborativeRecommendations)", "   - Hybrid: \(.hybridRecommendations)", "   - Total ML recommendations: \(.totalMLRecommendations)"'

echo ""
echo "🌐 Website updated:"
echo "   - Local: $WEBSITE_DIR/recommendations.json"
echo "   - S3: s3://$S3_BUCKET/website/recommendations.json"
echo "   - CloudFront: Invalidated"

# Clean up
rm -f /tmp/response-body.json

echo ""
echo "🚀 Next Steps:"
echo "   1. Visit https://plex.robertconsulting.net to see new recommendations"
echo "   2. Recommendations now include movies from comprehensive database"
echo "   3. All movies filtered for English language and availability"
echo "   4. Enhanced ML recommendations with detailed reasons"
