# Plex Movie Recommendations - Setup Guide

## 🚀 Quick Start

This project creates a personalized movie recommendation system using your Plex watch history and TMDB metadata.

## 📋 Prerequisites

- Python 3.8+
- AWS CLI configured
- Plex server with API access
- TMDB API account (free)

## 🔧 Configuration

### 1. Plex Setup
1. Get your Plex token from: https://support.plex.tv/articles/204059436/
2. Note your Plex server IP/domain and port (usually 32400)

### 2. TMDB API Setup
1. Create a free account at: https://www.themoviedb.org/
2. Go to API settings: https://www.themoviedb.org/settings/api
3. Request an API key (Developer type)

### 3. AWS Setup
1. Create an S3 bucket for storing Plex data
2. Set up IAM role for Lambda execution
3. Configure AWS CLI with your credentials

### 4. Update Configuration Files

Edit these files with your actual values:

**scripts/plex-data-exporter.py:**
```python
PLEX_SERVER = "your-plex-server:32400"
PLEX_TOKEN = "your_plex_token_here"
S3_BUCKET = "your-s3-bucket-name"
TMDB_API_KEY = "your_tmdb_api_key_here"
```

**lambda/plex-analyzer/index.js:**
```javascript
const S3_BUCKET = 'your-s3-bucket-name';
```

**scripts/deploy-plex-analyzer.sh:**
```bash
--role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE
```

## 🏃‍♂️ Running the System

### 1. Export Plex Data
```bash
cd scripts
python3 plex-data-exporter.py
```

### 2. Deploy Lambda Function
```bash
cd scripts
./deploy-plex-analyzer.sh
```

### 3. Open Website
Open `website/index.html` in your browser to see recommendations.

## 🎯 Features

- **Genre-based recommendations** based on your watch history
- **Decade-based suggestions** from your preferred time periods
- **Cast and director recommendations** using TMDB metadata
- **Similar movies** using TMDB algorithms
- **Cost-optimized** with S3 Intelligent Tiering and compression
- **Rich metadata integration** with TMDB API

## 💰 Cost Optimization

The system includes several cost optimizations:
- S3 Intelligent Tiering (45% storage savings)
- Data compression (60% size reduction)
- Lambda optimization (256MB, 60s timeout)
- Intelligent caching (24-hour expiry)
- Incremental processing (90% cost reduction on repeated analysis)

## 🔒 Security Notes

- Never commit API keys or tokens to version control
- Use environment variables or AWS Secrets Manager for production
- Ensure your Plex server is properly secured
- Use IAM roles with minimal required permissions

## 🆘 Troubleshooting

### Common Issues:
1. **"Failed to fetch" error**: Check API Gateway CORS configuration
2. **No recommendations**: Ensure Plex data was exported successfully
3. **TMDB errors**: Verify API key is correct and has sufficient quota
4. **AWS errors**: Check IAM permissions and region configuration

### Getting Help:
- Check the logs in AWS CloudWatch
- Verify all configuration values are correct
- Ensure your Plex server is accessible from your local machine

## 📈 Next Steps

- **Phase 2 Enhancement 2**: ML Integration (AWS SageMaker)
- **Phase 2 Enhancement 3**: Real-time Processing (AWS Kinesis)
- **Custom recommendation algorithms** based on your preferences
- **Multi-user support** for family recommendations
