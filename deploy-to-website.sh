#!/bin/bash

echo "🌐 Deploying Plex Recommendations to robert-consulting.net"
echo "========================================================"

# Configuration
WEBSITE_DIR="/private/tmp/plex-recommendations/website"
DEPLOY_DIR="plex-recommendations"

echo "📦 Preparing deployment package..."

# Create deployment directory
mkdir -p "$DEPLOY_DIR"

# Copy website files
cp -r "$WEBSITE_DIR"/* "$DEPLOY_DIR/"

# Create deployment-specific files
cat > "$DEPLOY_DIR/deploy-info.md" << EOF
# Plex Recommendations Deployment

## Files Included:
- index.html (main recommendations page)
- simple.html (simplified version)
- test.html (testing page)
- recommendations.json (current recommendations data)

## Deployment Options:

### Option 1: Subdomain (plex.robert-consulting.net)
\`\`\`bash
# Upload to subdomain directory
scp -r $DEPLOY_DIR/* user@robert-consulting.net:/var/www/plex/
\`\`\`

### Option 2: Path (robert-consulting.net/plex-recommendations/)
\`\`\`bash
# Upload to path directory
scp -r $DEPLOY_DIR/* user@robert-consulting.net:/var/www/html/plex-recommendations/
\`\`\`

### Option 3: Netlify (Free Static Hosting)
\`\`\`bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=$DEPLOY_DIR
\`\`\`

### Option 4: Vercel (Free Static Hosting)
\`\`\`bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod $DEPLOY_DIR
\`\`\`

## Configuration Needed:
1. Update Lambda function URL in index.html
2. Set up CORS for your domain
3. Configure SSL certificate
4. Set up automatic recommendation updates

## Next Steps:
1. Choose deployment option
2. Update Lambda function URL
3. Test the deployment
4. Set up automatic updates
EOF

# Create a simple deployment script
cat > "$DEPLOY_DIR/deploy.sh" << 'EOF'
#!/bin/bash

# Update recommendations before deployment
echo "🔄 Updating recommendations..."
cd "$(dirname "$0")/.."
./scripts/update-recommendations.sh

# Copy updated recommendations to deployment directory
cp website/recommendations.json plex-recommendations/

echo "✅ Deployment package ready!"
echo "📁 Files in: plex-recommendations/"
echo "🌐 Ready to deploy to your website"
EOF

chmod +x "$DEPLOY_DIR/deploy.sh"

echo "✅ Deployment package created in: $DEPLOY_DIR/"
echo ""
echo "🚀 Next steps:"
echo "1. Choose your deployment option (see deploy-info.md)"
echo "2. Run: ./$DEPLOY_DIR/deploy.sh (to update recommendations)"
echo "3. Deploy to your chosen hosting option"
echo ""
echo "📋 Available files:"
ls -la "$DEPLOY_DIR/"
