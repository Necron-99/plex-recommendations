#!/bin/bash

echo "🚀 Deploying Plex Recommendations to plex.robertconsulting.net"
echo "============================================================="

# Configuration
BUCKET_NAME="plex.robertconsulting.net"
ROUTE53_HOSTED_ZONE="Z0232243368137F38UDI1"
AWS_REGION="us-east-1"
LAMBDA_FUNCTION_NAME="plex-analyzer"

echo "📦 Configuration:"
echo "   Bucket: $BUCKET_NAME"
echo "   Route53 Zone: $ROUTE53_HOSTED_ZONE"
echo "   Region: $AWS_REGION"
echo "   Lambda: $LAMBDA_FUNCTION_NAME"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Step 1: Create S3 bucket
echo "🪣 Creating S3 bucket: $BUCKET_NAME"
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

if [ $? -eq 0 ]; then
    echo "✅ S3 bucket created successfully"
else
    echo "⚠️  Bucket may already exist, continuing..."
fi

# Step 2: Upload website files
echo "📤 Uploading website files..."
aws s3 sync website/ s3://$BUCKET_NAME --delete

if [ $? -eq 0 ]; then
    echo "✅ Website files uploaded successfully"
else
    echo "❌ Failed to upload website files"
    exit 1
fi

# Step 3: Enable static website hosting
echo "🌐 Enabling static website hosting..."
aws s3 website s3://$BUCKET_NAME \
    --index-document index.html \
    --error-document error.html

if [ $? -eq 0 ]; then
    echo "✅ Static website hosting enabled"
else
    echo "❌ Failed to enable static website hosting"
    exit 1
fi

# Step 4: Configure bucket for public access
echo "🔓 Configuring bucket for public access..."

# First, disable block public access settings
echo "   Disabling block public access settings..."
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

if [ $? -eq 0 ]; then
    echo "✅ Block public access settings disabled"
else
    echo "⚠️  Failed to disable block public access settings, continuing..."
fi

# Set bucket policy for public read access
echo "   Setting bucket policy for public access..."
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

if [ $? -eq 0 ]; then
    echo "✅ Bucket policy set for public access"
    rm bucket-policy.json
else
    echo "⚠️  Failed to set bucket policy, but CloudFront will still work"
    rm bucket-policy.json
fi

# Step 5: Create CloudFront distribution
echo "☁️ Creating CloudFront distribution..."
cat > cloudfront-config.json << EOF
{
    "CallerReference": "plex-recommendations-$(date +%s)",
    "Comment": "Plex Recommendations Distribution",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-$BUCKET_NAME",
                "DomainName": "$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-$BUCKET_NAME",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 3600,
        "MaxTTL": 86400
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}
EOF

DISTRIBUTION_ID=$(aws cloudfront create-distribution --distribution-config file://cloudfront-config.json --query 'Distribution.Id' --output text)

if [ $? -eq 0 ]; then
    echo "✅ CloudFront distribution created: $DISTRIBUTION_ID"
    rm cloudfront-config.json
else
    echo "❌ Failed to create CloudFront distribution"
    exit 1
fi

# Step 6: Create Route53 DNS record
echo "🌍 Creating Route53 DNS record..."
cat > route53-change.json << EOF
{
    "Comment": "Create plex subdomain",
    "Changes": [
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "plex.robertconsulting.net",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "d1234567890.cloudfront.net",
                    "EvaluateTargetHealth": false,
                    "HostedZoneId": "Z2FDTNDATAQYW2"
                }
            }
        }
    ]
}
EOF

# Get the actual CloudFront domain name
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DomainName' --output text)

# Update the Route53 change with the actual domain
sed -i.bak "s/d1234567890.cloudfront.net/$CLOUDFRONT_DOMAIN/g" route53-change.json

aws route53 change-resource-record-sets --hosted-zone-id $ROUTE53_HOSTED_ZONE --change-batch file://route53-change.json

if [ $? -eq 0 ]; then
    echo "✅ Route53 DNS record created"
    rm route53-change.json route53-change.json.bak
else
    echo "❌ Failed to create Route53 DNS record"
    exit 1
fi

# Step 7: Create update script
echo "📝 Creating update script..."
cat > update-recommendations.sh << 'EOF'
#!/bin/bash

echo "🔄 Updating Plex recommendations..."

# Call Lambda function and save response
aws lambda invoke --function-name plex-analyzer --payload '{}' temp-response.json

if [ $? -eq 0 ]; then
    # Extract the body content and save to S3
    cat temp-response.json | jq -r '.body' > recommendations.json
    aws s3 cp recommendations.json s3://plex.robertconsulting.net/ --content-type "application/json"
    
    if [ $? -eq 0 ]; then
        echo "✅ Recommendations updated successfully!"
        rm temp-response.json recommendations.json
    else
        echo "❌ Failed to upload to S3"
    fi
else
    echo "❌ Failed to call Lambda function"
fi
EOF

chmod +x update-recommendations.sh

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "✅ S3 bucket created: $BUCKET_NAME"
echo "✅ CloudFront distribution: $DISTRIBUTION_ID"
echo "✅ Route53 DNS record created"
echo "✅ Update script created: update-recommendations.sh"
echo ""
echo "🌐 Your site will be available at:"
echo "   https://plex.robertconsulting.net"
echo ""
echo "⏱️  DNS propagation may take 5-15 minutes"
echo ""
echo "🔄 To update recommendations:"
echo "   ./update-recommendations.sh"
echo ""
echo "📊 To set up automatic updates (weekly):"
echo "   crontab -e"
echo "   Add: 0 2 * * 0 /path/to/update-recommendations.sh"
