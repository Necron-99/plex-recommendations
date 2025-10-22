#!/bin/bash

echo "🔍 Plex Recommendations Site Status Check"
echo "========================================"

DOMAIN="plex.robertconsulting.net"
DISTRIBUTION_ID="E3T1Z34I8CU20F"

echo "🌐 1. DNS Resolution:"
nslookup $DOMAIN 8.8.8.8 2>/dev/null | grep -A 4 "Non-authoritative answer" || echo "   ❌ DNS resolution failed"

echo ""
echo "☁️  2. CloudFront Distribution:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.{Status:Status,DomainName:DomainName,Enabled:DistributionConfig.Enabled}' --output table

echo ""
echo "🔒 3. SSL Certificate:"
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DistributionConfig.ViewerCertificate.{CertificateSource:CertificateSource,SSLSupportMethod:SSLSupportMethod,MinimumProtocolVersion:MinimumProtocolVersion}' --output json

echo ""
echo "📁 4. S3 Bucket Contents:"
aws s3 ls s3://plex.robertconsulting.net/ --recursive

echo ""
echo "🌍 5. Website Accessibility:"
echo "   Testing: https://$DOMAIN"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ Website is accessible (HTTP $HTTP_STATUS)"
else
    echo "   ❌ Website returned HTTP $HTTP_STATUS"
fi

echo ""
echo "📊 6. Recommendations Data:"
echo "   Testing: https://$DOMAIN/recommendations.json"
JSON_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/recommendations.json)
if [ "$JSON_STATUS" = "200" ]; then
    echo "   ✅ Recommendations data is accessible (HTTP $JSON_STATUS)"
    echo "   📈 Data summary:"
    curl -s https://$DOMAIN/recommendations.json | jq '.summary' 2>/dev/null || echo "   ⚠️  JSON parsing failed"
else
    echo "   ❌ Recommendations data returned HTTP $JSON_STATUS"
fi

echo ""
echo "🎯 7. Overall Status:"
if [ "$HTTP_STATUS" = "200" ] && [ "$JSON_STATUS" = "200" ]; then
    echo "   ✅ Site is fully functional!"
    echo "   🌍 Access: https://$DOMAIN"
    echo "   📊 Data: https://$DOMAIN/recommendations.json"
else
    echo "   ⚠️  Site has issues that need attention"
    if [ "$HTTP_STATUS" != "200" ]; then
        echo "   - Website accessibility issue (HTTP $HTTP_STATUS)"
    fi
    if [ "$JSON_STATUS" != "200" ]; then
        echo "   - Recommendations data issue (HTTP $JSON_STATUS)"
        echo "   💡 Try running: ./update-recommendations.sh"
    fi
fi

echo ""
echo "🔧 Available Commands:"
echo "   ./update-recommendations.sh  - Update recommendations data"
echo "   ./monitor-ssl-deployment.sh  - Check SSL certificate status"
echo "   ./cleanup-old-distribution.sh - Clean up old CloudFront distributions"
