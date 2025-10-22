#!/bin/bash

echo "🔄 Force Fresh Update - Bypass All Caches"
echo "========================================"

echo "📊 1. Generating fresh recommendations from Lambda..."
aws lambda invoke --function-name plex-analyzer --payload '{}' fresh-response.json

if [ $? -eq 0 ]; then
    echo "✅ Lambda function executed successfully"
    
    echo "📝 2. Extracting fresh data..."
    jq -r '.body' fresh-response.json > fresh-recommendations.json
    
    echo "☁️ 3. Uploading to website S3 bucket..."
    aws s3 cp fresh-recommendations.json s3://plex.robertconsulting.net/recommendations.json --content-type application/json
    
    if [ $? -eq 0 ]; then
        echo "✅ Fresh recommendations uploaded to S3"
        
        echo "🗑️ 4. Invalidating CloudFront cache..."
        aws cloudfront create-invalidation --distribution-id E3T1Z34I8CU20F --paths "/recommendations.json" --output table
        
        echo "📊 5. Fresh data summary:"
        jq '.summary' fresh-recommendations.json
        
        echo ""
        echo "🎯 6. Next steps:"
        echo "   - Wait 2-3 minutes for CloudFront invalidation to complete"
        echo "   - Clear your browser cache (Ctrl+F5 or Cmd+Shift+R)"
        echo "   - Try incognito/private browsing mode"
        echo "   - Visit: https://plex.robertconsulting.net"
        
        # Clean up
        rm fresh-response.json fresh-recommendations.json
        
    else
        echo "❌ Failed to upload to S3"
        exit 1
    fi
else
    echo "❌ Lambda function failed"
    exit 1
fi

echo ""
echo "⏰ CloudFront invalidation typically takes 2-3 minutes to complete globally."
echo "🌍 The website should show the updated data once the cache is cleared."
