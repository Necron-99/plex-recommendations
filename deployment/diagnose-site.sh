#!/bin/bash

echo "🔍 Diagnosing plex.robertconsulting.net"
echo "====================================="

echo "📊 1. DNS Resolution Tests:"
echo "   Local DNS:"
nslookup plex.robertconsulting.net 2>/dev/null | grep -A 4 "Non-authoritative answer" || echo "   ❌ Local DNS failed"

echo "   Google DNS (8.8.8.8):"
nslookup plex.robertconsulting.net 8.8.8.8 2>/dev/null | grep -A 4 "Non-authoritative answer" || echo "   ❌ Google DNS failed"

echo "   Cloudflare DNS (1.1.1.1):"
nslookup plex.robertconsulting.net 1.1.1.1 2>/dev/null | grep -A 4 "Non-authoritative answer" || echo "   ❌ Cloudflare DNS failed"

echo ""
echo "🌐 2. CloudFront Distribution Status:"
aws cloudfront get-distribution --id E3T1Z34I8CU20F --query 'Distribution.{Status:Status,DomainName:DomainName,Enabled:DistributionConfig.Enabled}' --output table

echo ""
echo "📁 3. S3 Bucket Contents:"
aws s3 ls s3://plex.robertconsulting.net/ --recursive

echo ""
echo "🔗 4. Route53 DNS Record:"
aws route53 list-resource-record-sets --hosted-zone-id Z0232243368137F38UDI1 --query "ResourceRecordSets[?Name == 'plex.robertconsulting.net.' && Type == 'A']" --output json

echo ""
echo "🌍 5. Direct CloudFront Test:"
echo "   Testing: https://d24h0ypf8fsiv7.cloudfront.net"
curl -I https://d24h0ypf8fsiv7.cloudfront.net 2>/dev/null | head -5 || echo "   ❌ CloudFront direct access failed"

echo ""
echo "📋 6. Recommendations:"
echo "   - If DNS is inconsistent, wait 5-10 minutes for propagation"
echo "   - Try accessing via CloudFront URL directly: https://d24h0ypf8fsiv7.cloudfront.net"
echo "   - Clear your browser DNS cache"
echo "   - Try from a different network/device"
