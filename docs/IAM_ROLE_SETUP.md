# 🔐 IAM Role Setup Guide

## 🎯 **Overview**

Your Lambda function needs an IAM role to access AWS services (S3, CloudWatch Logs). This guide shows you exactly what role to create and how to set it up.

## 🚀 **Quick Setup (Recommended)**

### **Option 1: Automated Setup**
```bash
# Run the automated setup script
cd /private/tmp/plex-recommendations
./scripts/create-lambda-role.sh
```

This script will:
- ✅ Create the IAM role
- ✅ Set up the necessary policies
- ✅ Give you the exact role ARN to use

## 🛠️ **Manual Setup (Alternative)**

### **Step 1: Create IAM Role**

1. **Go to AWS Console** → IAM → Roles → Create Role
2. **Select**: AWS Service → Lambda
3. **Role Name**: `PlexRecommendationsLambdaRole`
4. **Description**: `Role for Plex Recommendations Lambda function`

### **Step 2: Attach Policies**

#### **Required Policies:**
1. **AWS Managed Policy**: `AWSLambdaBasicExecutionRole`
   - Allows Lambda to write to CloudWatch Logs
   - **Cost**: FREE

2. **Custom Policy**: Create a new policy with this JSON:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_S3_BUCKET_NAME",
        "arn:aws:s3:::YOUR_S3_BUCKET_NAME/*"
      ]
    }
  ]
}
```

**Replace `YOUR_S3_BUCKET_NAME` with your actual S3 bucket name**

### **Step 3: Get Role ARN**

After creating the role, copy the **Role ARN** which looks like:
```
arn:aws:iam::123456789012:role/PlexRecommendationsLambdaRole
```

## 📋 **Role Requirements**

### **Minimum Permissions Needed**

| Service | Permission | Purpose | Cost |
|---------|------------|---------|------|
| **S3** | `s3:GetObject` | Read Plex data | FREE |
| **S3** | `s3:PutObject` | Save analysis results | FREE |
| **S3** | `s3:ListBucket` | List S3 objects | FREE |
| **CloudWatch** | `logs:CreateLogGroup` | Create log groups | FREE |
| **CloudWatch** | `logs:CreateLogStream` | Create log streams | FREE |
| **CloudWatch** | `logs:PutLogEvents` | Write logs | FREE |

### **Security Best Practices**
- ✅ **Principle of Least Privilege**: Only the permissions needed
- ✅ **Resource-Specific**: Limited to your specific S3 bucket
- ✅ **No Admin Access**: No broad permissions
- ✅ **Cost-Effective**: All permissions are FREE

## 🔧 **Configuration**

### **Update Your Deployment Script**

After creating the role, update these files:

#### **1. Update `scripts/deploy-enhanced-lambda.sh`**
```bash
# Replace these values with your actual values:
LAMBDA_ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/PlexRecommendationsLambdaRole"
S3_BUCKET="your-actual-s3-bucket-name"
```

#### **2. Update `lambda/plex-analyzer/enhanced-index.js`**
```javascript
// Replace with your actual S3 bucket name:
const S3_BUCKET = 'your-actual-s3-bucket-name';
```

## 🧪 **Testing the Role**

### **Test 1: Verify Role Exists**
```bash
# Check if role exists
aws iam get-role --role-name PlexRecommendationsLambdaRole
```

### **Test 2: Check Permissions**
```bash
# List attached policies
aws iam list-attached-role-policies --role-name PlexRecommendationsLambdaRole
```

### **Test 3: Deploy Lambda**
```bash
# Deploy with the new role
./scripts/deploy-enhanced-lambda.sh
```

## 💰 **Cost Impact**

### **IAM Role Costs**
- **Role Creation**: FREE
- **Policy Attachments**: FREE
- **Role Usage**: FREE
- **Total IAM Cost**: $0.00/month

### **Lambda Execution Costs**
- **Basic Lambda**: ~$0.20/month
- **With ML Processing**: ~$1.20-3.20/month
- **S3 Storage**: ~$0.50/month
- **Total System Cost**: ~$1.70-3.70/month

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. "Role does not exist" Error**
```bash
# Solution: Create the role first
./scripts/create-lambda-role.sh
```

#### **2. "Access Denied" to S3**
```bash
# Solution: Check S3 bucket name in policy
# Make sure it matches your actual bucket name
```

#### **3. "Invalid role ARN" Error**
```bash
# Solution: Check the role ARN format
# Should be: arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME
```

### **Verification Commands**
```bash
# Check if role exists
aws iam get-role --role-name PlexRecommendationsLambdaRole

# Check attached policies
aws iam list-attached-role-policies --role-name PlexRecommendationsLambdaRole

# Check inline policies
aws iam list-role-policies --role-name PlexRecommendationsLambdaRole
```

## 📊 **Role Summary**

### **What This Role Does**
- ✅ **Reads Plex data** from your S3 bucket
- ✅ **Saves analysis results** to S3
- ✅ **Writes logs** to CloudWatch
- ✅ **Enables ML processing** in Lambda

### **What This Role Does NOT Do**
- ❌ **No admin access** to your AWS account
- ❌ **No access** to other S3 buckets
- ❌ **No access** to other AWS services
- ❌ **No cost** - completely FREE

## 🎯 **Next Steps**

1. **Create the role** using the automated script
2. **Update configuration** with your role ARN and S3 bucket
3. **Deploy Lambda function** with the new role
4. **Test the system** to ensure everything works

## 📞 **Need Help?**

### **If the automated script fails:**
1. Check AWS CLI configuration: `aws configure list`
2. Verify you have IAM permissions
3. Try the manual setup steps

### **If you get permission errors:**
1. Check the S3 bucket name in the policy
2. Verify the role ARN is correct
3. Ensure the role is attached to the Lambda function

---

**Your IAM role is the foundation for secure, cost-effective ML recommendations! 🔐🤖**
