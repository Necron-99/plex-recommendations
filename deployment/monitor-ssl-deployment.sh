#!/bin/bash

echo "🔒 SSL Certificate Deployment Monitor"
echo "===================================="

DISTRIBUTION_ID="E3T1Z34I8CU20F"
DOMAIN="plex.robertconsulting.net"

echo "📊 Current CloudFront Distribution Status:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.{Status:Status,DomainName:DomainName,LastModified:LastModifiedTime}' --output table

echo ""
echo "🔐 SSL Certificate Configuration:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.ViewerCertificate' --output json

echo ""
echo "🌐 Domain Aliases:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.Aliases' --output json

echo ""
echo "⏳ Deployment Status:"
STATUS=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.Status' --output text)
if [ "$STATUS" = "Deployed" ]; then
    echo "   ✅ Distribution is fully deployed!"
    echo "   🌍 Your site should be accessible at: https://$DOMAIN"
    echo ""
    echo "🧪 Testing SSL Certificate:"
    echo "   Testing: https://$DOMAIN"
    curl -I https://$DOMAIN 2>/dev/null | head -3 || echo "   ⚠️  Site not yet accessible (DNS propagation in progress)"
else
    echo "   🔄 Distribution is still deploying..."
    echo "   ⏰ CloudFront deployments typically take 10-15 minutes"
    echo "   📋 Run this script again in a few minutes to check progress"
fi

echo ""
echo "📋 What was changed:"
echo "   ✅ Added custom domain alias: $DOMAIN"
echo "   ✅ Configured wildcard SSL certificate: *.robertconsulting.net"
echo "   ✅ Set minimum TLS version to 1.2"
echo "   ✅ Enabled SNI-only SSL support"

echo ""
echo "🎯 Next Steps:"
echo "   1. Wait for CloudFront deployment to complete (10-15 minutes)"
echo "   2. Test SSL certificate: https://$DOMAIN"
echo "   3. Verify certificate shows as valid in browser"
echo "   4. Check that it matches your main site's certificate"
