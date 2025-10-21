# Plex Recommendations - Subdomain Deployment

## Overview
This deployment creates a complete AWS infrastructure for hosting Plex recommendations at `plex.robertconsulting.net`.

## Architecture
- **S3 Bucket**: `plex.robertconsulting.net` (static website hosting)
- **CloudFront**: Global CDN for performance
- **Route53**: DNS management (Zone: Z0232243368137F38UDI1)
- **Lambda**: Backend processing for recommendations

## Files Included
- `website/index.html` - Main recommendations page
- `website/error.html` - 404 error page
- `deploy-subdomain.sh` - Complete deployment script
- `README.md` - This file

## Deployment Steps

### 1. Run the Deployment Script
```bash
cd deployment/
./deploy-subdomain.sh
```

This script will:
- Create S3 bucket: `plex.robertconsulting.net`
- Upload website files
- Enable static website hosting
- Set public read permissions
- Create CloudFront distribution
- Create Route53 DNS record
- Generate update script

### 2. Wait for DNS Propagation
DNS changes may take 5-15 minutes to propagate globally.

### 3. Test the Deployment
Visit: https://plex.robertconsulting.net

### 4. Set Up Automatic Updates
```bash
# Add to crontab for weekly updates
crontab -e
# Add this line:
0 2 * * 0 /path/to/update-recommendations.sh
```

## Security Features
- ✅ No sensitive data in client-side code
- ✅ Static files only
- ✅ HTTPS enforced via CloudFront
- ✅ Public read access only
- ✅ No server-side processing

## Cost Estimation
- **S3 Storage**: ~$0.023/GB/month
- **CloudFront**: ~$0.085/GB transfer
- **Route53**: $0.50/month per hosted zone
- **Lambda**: ~$0.20/month
- **Total**: <$2/month

## Maintenance
1. **Weekly Updates**: Run `update-recommendations.sh`
2. **Monitor Costs**: Check AWS billing dashboard
3. **SSL**: CloudFront handles automatically
4. **Performance**: CloudFront provides global CDN

## Troubleshooting
- **DNS Issues**: Check Route53 console
- **CloudFront**: Check distribution status
- **S3 Access**: Verify bucket policy
- **Lambda**: Check function logs

## Cleanup (if needed)
```bash
# Delete CloudFront distribution
aws cloudfront delete-distribution --id DISTRIBUTION_ID --if-match ETAG

# Delete S3 bucket
aws s3 rb s3://plex.robertconsulting.net --force

# Delete Route53 record
aws route53 change-resource-record-sets --hosted-zone-id Z0232243368137F38UDI1 --change-batch file://delete-record.json
```
