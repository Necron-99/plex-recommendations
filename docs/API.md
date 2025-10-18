# Plex Recommendations API Documentation

## Overview

The Plex Recommendations system consists of several components that work together to analyze your Plex watch history and generate personalized movie recommendations.

## Architecture

```
Local Plex Server → Python Exporter → S3 Storage → AWS Lambda → Recommendations Website
```

## Components

### 1. Plex Data Exporter (`scripts/plex-data-exporter.py`)

**Purpose**: Extracts movie watch history from your local Plex server and uploads it to S3.

**Configuration**:
```python
PLEX_SERVER = "192.168.0.109:32400"  # Your Plex server
PLEX_TOKEN = "your-plex-token"        # Your Plex token
S3_BUCKET = "robert-consulting-cache" # S3 bucket for storage
```

**Usage**:
```bash
# Export last 365 days (default)
python plex-data-exporter.py

# Export last 30 days
python plex-data-exporter.py 30
```

**Output**: JSON file uploaded to S3 with structure:
```json
{
  "exportedAt": "2025-10-18T16:32:26.000Z",
  "serverInfo": {
    "name": "faramir.necron99.org",
    "version": "1.32.5.7516",
    "platform": "Linux"
  },
  "watchHistory": [
    {
      "title": "Movie Title",
      "year": 2020,
      "genres": ["Action", "Drama"],
      "rating": 8.5,
      "duration": 120,
      "viewedAt": "2025-10-18T14:30:00.000Z",
      "type": "movie",
      "studio": "Studio Name",
      "summary": "Movie summary..."
    }
  ],
  "statistics": {
    "totalMovies": 8,
    "topGenres": [
      {"genre": "Action", "count": 3},
      {"genre": "Drama", "count": 2}
    ],
    "topDecades": [
      {"decade": 2020, "count": 4},
      {"decade": 2010, "count": 3}
    ],
    "averageRating": 7.8,
    "dateRange": {
      "start": "2024-10-18T00:00:00.000Z",
      "end": "2025-10-18T23:59:59.000Z"
    }
  }
}
```

### 2. AWS Lambda Analyzer (`lambda/plex-analyzer/index.js`)

**Purpose**: Processes Plex data from S3 and generates movie recommendations.

**Function Name**: `robert-consulting-plex-analyzer`

**Input**: Reads from S3 key `plex-data/latest.json`

**Output**: Saves analysis to S3 with structure:
```json
{
  "generatedAt": "2025-10-18T16:32:38.232Z",
  "sourceData": {
    "exportedAt": "2025-10-18T16:32:26.000Z",
    "totalMovies": 8,
    "dateRange": {
      "start": "2024-10-18T00:00:00.000Z",
      "end": "2025-10-18T23:59:59.000Z"
    }
  },
  "analysis": {
    "totalMovies": 8,
    "genreDistribution": {
      "Action": 3,
      "Drama": 2,
      "Comedy": 1
    },
    "decadeDistribution": {
      "2020": 4,
      "2010": 3,
      "2000": 1
    },
    "ratingDistribution": {
      "8": 3,
      "7": 2,
      "9": 1
    },
    "viewingFrequency": {
      "2025-10": 2,
      "2025-09": 3,
      "2025-08": 1
    },
    "averageRating": 7.8,
    "totalWatchTime": 960
  },
  "recommendations": {
    "genreBased": [
      {
        "type": "genre",
        "suggestion": "More Action movies",
        "reason": "You've watched 3 Action movies",
        "confidence": 0.75,
        "genre": "Action",
        "count": 3
      }
    ],
    "decadeBased": [
      {
        "type": "decade",
        "suggestion": "Movies from the 2020s",
        "reason": "You enjoy 2020s cinema (4 movies)",
        "confidence": 0.8,
        "decade": 2020,
        "count": 4
      }
    ],
    "ratingBased": [
      {
        "type": "rating",
        "suggestion": "Movies rated 8+ stars",
        "reason": "Your average rating is 7.8, suggesting you prefer quality films",
        "confidence": 0.7,
        "threshold": 8,
        "averageRating": 7.8
      }
    ],
    "general": [
      {
        "type": "general",
        "suggestion": "Explore similar movies to your favorites",
        "reason": "Based on your viewing patterns",
        "confidence": 0.6
      }
    ]
  },
  "summary": {
    "totalMovies": 8,
    "topGenres": [
      {"genre": "Action", "count": 3},
      {"genre": "Drama", "count": 2}
    ],
    "topDecades": [
      {"decade": 2020, "count": 4},
      {"decade": 2010, "count": 3}
    ],
    "averageRating": 7.8,
    "totalRecommendations": 7
  }
}
```

### 3. Website (`website/index.html`)

**Purpose**: Displays recommendations in a user-friendly interface.

**Features**:
- Real-time statistics display
- Recommendation sections by type
- Manual refresh capability
- Raw data viewer for debugging

**API Endpoint**: `https://lbfggdldp3.execute-api.us-east-1.amazonaws.com/prod/plex-analyzer`

## Data Flow

1. **Data Collection**: Python script connects to Plex server and exports watch history
2. **Storage**: Data is uploaded to S3 bucket `robert-consulting-cache`
3. **Processing**: Lambda function reads data from S3 and generates recommendations
4. **Display**: Website fetches analysis results and displays them to user

## S3 Bucket Structure

```
robert-consulting-cache/
├── plex-data/
│   ├── watch-history-2025-10-18-12-00-00.json
│   ├── watch-history-2025-10-19-14-30-00.json
│   └── latest.json (symlink to most recent)
└── plex-recommendations/
    ├── analysis-2025-10-18-12-05-00.json
    └── latest-analysis.json (symlink to most recent)
```

## Error Handling

### Common Issues

1. **Plex Connection Failed**
   - Check server IP and port
   - Verify Plex token is valid
   - Ensure server is running

2. **S3 Upload Failed**
   - Check AWS credentials
   - Verify S3 bucket permissions
   - Ensure bucket exists

3. **Lambda Function Error**
   - Check CloudWatch logs
   - Verify IAM permissions
   - Ensure S3 data exists

### Logging

- **Python Script**: Console output with emoji indicators
- **Lambda Function**: CloudWatch logs with structured logging
- **Website**: Browser console for debugging

## Security

- **Plex Token**: Stored in script (consider using environment variables)
- **AWS Credentials**: Managed by AWS CLI configuration
- **S3 Access**: IAM role-based permissions
- **Lambda Execution**: VPC and IAM role restrictions

## Performance

- **Data Export**: ~1-2 seconds for typical watch history
- **Lambda Processing**: ~500ms for analysis
- **Website Loading**: ~1-2 seconds for recommendations
- **Storage**: Minimal S3 costs (<$1/year)

## Future Enhancements

- **Real-time Updates**: Webhook integration with Plex
- **Machine Learning**: Advanced recommendation algorithms
- **Multi-user Support**: Multiple Plex users
- **Mobile App**: Native iOS/Android applications
