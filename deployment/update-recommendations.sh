#!/bin/bash

echo "🔄 Updating Plex Recommendations"
echo "==============================="

echo "📊 Invoking Lambda function to generate fresh recommendations..."
aws lambda invoke --function-name plex-analyzer --payload '{}' response.json

if [ $? -eq 0 ]; then
    echo "✅ Lambda function executed successfully"
    
    echo "📝 Extracting recommendations data..."
    jq -r '.body' response.json > recommendations.json
    
    echo "☁️  Uploading to S3..."
    aws s3 cp recommendations.json s3://plex.robertconsulting.net/recommendations.json --content-type application/json
    
    if [ $? -eq 0 ]; then
        echo "✅ Recommendations updated successfully!"
        echo "🌍 Website: https://plex.robertconsulting.net"
        echo "📊 Data: https://plex.robertconsulting.net/recommendations.json"
        
        # Show summary
        echo ""
        echo "📈 Current Recommendations Summary:"
        jq '.summary' recommendations.json
        
        # Clean up
        rm response.json recommendations.json
    else
        echo "❌ Failed to upload to S3"
        exit 1
    fi
else
    echo "❌ Lambda function failed"
    exit 1
fi

echo ""
echo "🎯 Next Steps:"
echo "   - Refresh your browser to see updated recommendations"
echo "   - Run this script periodically to keep recommendations fresh"
echo "   - Consider setting up a cron job for automatic updates"