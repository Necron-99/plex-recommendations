#!/bin/bash

echo "🔧 Fixing S3 Bucket Permissions for plex.robertconsulting.net"
echo "============================================================"

BUCKET_NAME="plex.robertconsulting.net"

echo "📋 Manual steps to fix S3 permissions:"
echo ""
echo "1. Go to AWS S3 Console:"
echo "   https://s3.console.aws.amazon.com/s3/buckets/$BUCKET_NAME"
echo ""
echo "2. Click on the 'Permissions' tab"
echo ""
echo "3. Scroll down to 'Block public access (bucket settings)'"
echo "   Click 'Edit' and uncheck all 4 boxes:"
echo "   ☐ Block all public access"
echo "   ☐ Block public access to buckets and objects granted through new access control lists (ACLs)"
echo "   ☐ Block public access to buckets and objects granted through any access control lists (ACLs)"
echo "   ☐ Block public access to buckets and objects granted through new public bucket or access point policies"
echo "   ☐ Block public access to buckets and objects granted through any public bucket or access point policies"
echo ""
echo "4. Click 'Save changes' and type 'confirm'"
echo ""
echo "5. Scroll down to 'Bucket policy' and click 'Edit'"
echo "   Paste this policy:"
echo ""
cat << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::plex.robertconsulting.net/*"
        }
    ]
}
EOF
echo ""
echo "6. Click 'Save changes'"
echo ""
echo "7. Continue with the deployment script:"
echo "   ./deploy-subdomain.sh"
echo ""
echo "⚠️  Note: CloudFront will work even without public bucket policy,"
echo "   but direct S3 access won't work until these steps are completed."
