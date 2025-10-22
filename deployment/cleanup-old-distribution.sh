#!/bin/bash

echo "🧹 Cleaning up old CloudFront distribution"
echo "========================================="

OLD_DISTRIBUTION_ID="E2URC630VG54YR"
NEW_DISTRIBUTION_ID="E3T1Z34I8CU20F"

echo "📊 Current CloudFront distributions:"
aws cloudfront list-distributions --query "DistributionList.Items[?contains(Comment, 'Plex Recommendations')].{ID:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}" --output table

echo ""
echo "🔄 Checking status of old distribution (E2URC630VG54YR)..."

# Check if old distribution is disabled
STATUS=$(aws cloudfront get-distribution --id $OLD_DISTRIBUTION_ID --query 'Distribution.Status' --output text)
ENABLED=$(aws cloudfront get-distribution --id $OLD_DISTRIBUTION_ID --query 'DistributionConfig.Enabled' --output text)

echo "   Status: $STATUS"
echo "   Enabled: $ENABLED"

if [ "$STATUS" = "Deployed" ] && [ "$ENABLED" = "False" ]; then
    echo "✅ Old distribution is disabled and ready for deletion"
    
    # Get current ETag
    ETAG=$(aws cloudfront get-distribution --id $OLD_DISTRIBUTION_ID --query 'ETag' --output text)
    echo "   ETag: $ETAG"
    
    echo "🗑️  Deleting old distribution..."
    aws cloudfront delete-distribution --id $OLD_DISTRIBUTION_ID --if-match $ETAG
    
    if [ $? -eq 0 ]; then
        echo "✅ Old distribution deleted successfully!"
        echo ""
        echo "🎯 You now have only one CloudFront distribution:"
        echo "   ID: $NEW_DISTRIBUTION_ID"
        echo "   Domain: d24h0ypf8fsiv7.cloudfront.net"
        echo "   URL: https://plex.robertconsulting.net"
    else
        echo "❌ Failed to delete old distribution"
    fi
else
    echo "⏳ Old distribution is still being disabled. Please wait and run this script again in a few minutes."
    echo "   CloudFront changes can take 10-15 minutes to propagate."
fi

echo ""
echo "📋 To monitor progress:"
echo "   aws cloudfront get-distribution --id $OLD_DISTRIBUTION_ID --query 'Distribution.Status' --output text"
