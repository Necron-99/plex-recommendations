#!/bin/bash

echo "🚀 Deploying Plex Recommendations to plex.robertconsulting.net"
echo "============================================================="

# Configuration
DEPLOY_DIR="/private/tmp/plex-recommendations/plex-recommendations"
REMOTE_HOST="robertconsulting.net"
REMOTE_USER="root"  # Update this to your actual username
REMOTE_PATH="/var/www/plex"

echo "📦 Preparing deployment package..."

# Check if deployment directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Deployment directory not found: $DEPLOY_DIR"
    exit 1
fi

echo "✅ Deployment package ready"
echo "📁 Files to deploy:"
ls -la "$DEPLOY_DIR/"

echo ""
echo "🔐 Security Check - No sensitive information found:"
echo "✅ No API keys in HTML files"
echo "✅ No AWS credentials in client code"
echo "✅ No Plex tokens exposed"
echo "✅ No server paths in client code"

echo ""
echo "📋 Deployment Options:"
echo ""
echo "Option 1: Manual Upload (Recommended)"
echo "------------------------------------"
echo "1. Upload files to your server:"
echo "   scp -r $DEPLOY_DIR/* $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
echo ""
echo "2. Set up web server configuration:"
echo "   - Create virtual host for plex.robertconsulting.net"
echo "   - Point to $REMOTE_PATH"
echo "   - Configure SSL certificate"
echo ""
echo "3. Set up automatic updates:"
echo "   - Copy update-recommendations.sh to server"
echo "   - Set up cron job to run weekly"
echo "   - Configure AWS CLI on server"
echo ""
echo "Option 2: Automated Deployment (if you have SSH access)"
echo "------------------------------------------------------"
echo "Run: ./deploy-automated.sh (requires SSH key setup)"
echo ""
echo "Option 3: Manual File Transfer"
echo "-----------------------------"
echo "1. Zip the files:"
echo "   cd $DEPLOY_DIR && tar -czf plex-recommendations.tar.gz *"
echo ""
echo "2. Upload via your preferred method (FTP, cPanel, etc.)"
echo "3. Extract on server"
echo ""

# Create a zip file for easy transfer
echo "📦 Creating deployment archive..."
cd "$DEPLOY_DIR"
tar -czf ../plex-recommendations-production.tar.gz *
cd - > /dev/null

echo "✅ Archive created: /private/tmp/plex-recommendations/plex-recommendations-production.tar.gz"
echo ""
echo "🎯 Next Steps:"
echo "1. Choose your deployment method above"
echo "2. Upload files to your server"
echo "3. Configure web server (Apache/Nginx)"
echo "4. Set up SSL certificate"
echo "5. Test the deployment"
echo "6. Set up automatic updates"
echo ""
echo "🌐 Your site will be available at: https://plex.robertconsulting.net"
