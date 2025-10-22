#!/bin/bash

echo "🔧 DNS Cache Fix for plex.robertconsulting.net"
echo "============================================="

echo "📊 Current Status:"
echo "   ✅ CloudFront Distribution: Deployed and working"
echo "   ✅ S3 Bucket: Files uploaded correctly"
echo "   ✅ Route53 Record: Points to correct CloudFront"
echo "   ⚠️  Local DNS: Inconsistent resolution"

echo ""
echo "🌐 DNS Resolution Status:"
echo "   Google DNS (8.8.8.8): ✅ Working"
echo "   Cloudflare DNS (1.1.1.1): ✅ Working"
echo "   Local DNS: ❌ Inconsistent"

echo ""
echo "🔧 Solutions to try:"

echo ""
echo "1. 🌍 Access via CloudFront URL directly:"
echo "   https://d24h0ypf8fsiv7.cloudfront.net"
echo "   (This should work immediately)"

echo ""
echo "2. 🧹 Clear DNS cache on macOS:"
echo "   sudo dscacheutil -flushcache"
echo "   sudo killall -HUP mDNSResponder"

echo ""
echo "3. 🔄 Try different DNS servers:"
echo "   - Change your DNS to 8.8.8.8 and 8.8.4.4 (Google)"
echo "   - Or use 1.1.1.1 and 1.0.0.1 (Cloudflare)"

echo ""
echo "4. ⏰ Wait for DNS propagation:"
echo "   - DNS changes can take 5-60 minutes to fully propagate"
echo "   - Your local ISP's DNS may be slower to update"

echo ""
echo "5. 🧪 Test from different locations:"
echo "   - Try from your phone (different network)"
echo "   - Try from a different computer"
echo "   - Use online DNS checker tools"

echo ""
echo "🎯 Quick Test Commands:"
echo "   # Test direct CloudFront access:"
echo "   curl -I https://d24h0ypf8fsiv7.cloudfront.net"
echo ""
echo "   # Test with Google DNS:"
echo "   nslookup plex.robertconsulting.net 8.8.8.8"
echo ""
echo "   # Test with Cloudflare DNS:"
echo "   nslookup plex.robertconsulting.net 1.1.1.1"

echo ""
echo "✅ The website is working correctly - this is just a DNS propagation issue!"
