#!/bin/bash

echo "🔄 Updating Plex recommendations..."
echo "=================================="

# Call Lambda function and save response
echo "📡 Calling Lambda function..."
aws lambda invoke --function-name plex-analyzer --payload '{}' temp-response.json

if [ $? -eq 0 ]; then
    echo "✅ Lambda function called successfully"
    
    # Extract the body content and save to website
    echo "💾 Saving recommendations to website..."
    cat temp-response.json | jq -r '.body' > website/recommendations.json
    
    if [ $? -eq 0 ]; then
        echo "✅ Recommendations updated successfully!"
        echo "🌐 Open website/index.html and click 'Update Recommendations' to see the latest data"
        
        # Show summary
        echo ""
        echo "📊 Latest recommendations summary:"
        cat website/recommendations.json | jq '.summary'
        
        # Clean up
        rm temp-response.json
    else
        echo "❌ Failed to save recommendations"
        exit 1
    fi
else
    echo "❌ Failed to call Lambda function"
    exit 1
fi
