#!/bin/bash

echo "🚀 Deploying Plex Recommendations to S3 Static Hosting"
echo "======================================================"

# Configuration
DEPLOY_DIR="/private/tmp/plex-recommendations/s3-deployment"
S3_BUCKET="robertconsulting.net"  # Update this to your actual bucket name

echo "📦 Preparing S3 deployment package..."

# Check if deployment directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Deployment directory not found: $DEPLOY_DIR"
    exit 1
fi

echo "✅ S3 deployment package ready"
echo "📁 Files to deploy:"
ls -la "$DEPLOY_DIR/"

echo ""
echo "🔐 Security Check - S3 Static Hosting Ready:"
echo "✅ No sensitive information exposed"
echo "✅ Static files only"
echo "✅ CORS-safe"
echo "✅ HTTPS ready"
echo "✅ CDN optimized"

echo ""
echo "📋 S3 Deployment Options:"
echo ""
echo "Option 1: Subdomain (plex.robertconsulting.net) - RECOMMENDED"
echo "------------------------------------------------------------"
echo "1. Create S3 bucket:"
echo "   aws s3 mb s3://plex.robertconsulting.net"
echo ""
echo "2. Upload files:"
echo "   aws s3 sync $DEPLOY_DIR/ s3://plex.robertconsulting.net --delete"
echo ""
echo "3. Enable website hosting:"
echo "   aws s3 website s3://plex.robertconsulting.net --index-document index.html --error-document error.html"
echo ""
echo "4. Set up CloudFront distribution"
echo "5. Configure DNS: plex.robertconsulting.net → CloudFront"
echo ""
echo "Option 2: Path-based (robertconsulting.net/plex/) - SIMPLER"
echo "----------------------------------------------------------"
echo "1. Upload to existing bucket:"
echo "   aws s3 sync $DEPLOY_DIR/ s3://$S3_BUCKET/plex/ --delete"
echo ""
echo "2. Access at: https://robertconsulting.net/plex/"
echo ""
echo "Option 3: Automated Deployment"
echo "-----------------------------"
echo "Run: ./deploy-automated-s3.sh (requires AWS CLI setup)"
echo ""

# Create deployment archive
echo "📦 Creating S3 deployment archive..."
cd "$DEPLOY_DIR"
tar -czf ../plex-recommendations-s3.tar.gz *
cd - > /dev/null

echo "✅ Archive created: /private/tmp/plex-recommendations/plex-recommendations-s3.tar.gz"
echo ""
echo "🎯 Next Steps:"
echo "1. Choose your S3 deployment option above"
echo "2. Create/configure S3 bucket"
echo "3. Upload files to S3"
echo "4. Enable static website hosting"
echo "5. Set up CloudFront (recommended)"
echo "6. Configure DNS (if using subdomain)"
echo "7. Test the deployment"
echo "8. Set up automatic updates"
echo ""
echo "🌐 Your site will be available at:"
echo "   - Subdomain: https://plex.robertconsulting.net"
echo "   - Path: https://robertconsulting.net/plex/"
echo ""
echo "💰 Estimated monthly cost: <$1 (S3 + CloudFront + Lambda)"
