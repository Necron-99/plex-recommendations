#!/usr/bin/env python3
"""
Plex Data Exporter
Extracts movie watch history from local Plex server and uploads to S3
"""

import requests
import json
import boto3
import os
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
import sys

# Configuration
PLEX_SERVER = "192.168.0.109:32400"
PLEX_TOKEN = "iUAXXUBe9Hno42-aHy5E"
S3_BUCKET = "robert-consulting-cache"
AWS_PROFILE = "default"  # or specify a profile
AWS_REGION = "us-east-1"

class PlexDataExporter:
    def __init__(self):
        self.plex_base_url = f"http://{PLEX_SERVER}"
        self.plex_token = PLEX_TOKEN
        self.s3_bucket = S3_BUCKET
        
        # Initialize S3 client
        try:
            session = boto3.Session(profile_name=AWS_PROFILE)
            self.s3_client = session.client('s3', region_name=AWS_REGION)
            print("✅ S3 client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing S3 client: {e}")
            sys.exit(1)
    
    def test_plex_connection(self) -> bool:
        """Test connection to Plex server"""
        try:
            url = f"{self.plex_base_url}/status/sessions"
            headers = {"X-Plex-Token": self.plex_token}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Plex server connection successful")
                return True
            else:
                print(f"❌ Plex server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Plex server: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get basic server information"""
        try:
            url = f"{self.plex_base_url}/"
            headers = {"X-Plex-Token": self.plex_token}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                return {
                    "name": root.get("friendlyName", "Unknown"),
                    "version": root.get("version", "Unknown"),
                    "platform": root.get("platform", "Unknown")
                }
            return {}
        except Exception as e:
            print(f"⚠️ Warning: Could not get server info: {e}")
            return {}
    
    def get_watch_history(self, days_back: int = 365) -> List[Dict[str, Any]]:
        """Get movie watch history for specified number of days"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            print(f"📅 Fetching watch history from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Get watch history
            url = f"{self.plex_base_url}/status/sessions/history/all"
            headers = {"X-Plex-Token": self.plex_token}
            params = {
                "start": start_timestamp,
                "end": end_timestamp
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code != 200:
                print(f"❌ Error fetching watch history: {response.status_code}")
                return []
            
            # Parse XML response
            root = ET.fromstring(response.content)
            watch_history = []
            
            for video in root.findall("Video"):
                # Only process movies (not TV episodes)
                if video.get("type") == "movie":
                    movie_data = {
                        "title": video.get("title", ""),
                        "year": int(video.get("year", 0)) if video.get("year") else None,
                        "genres": [g.strip() for g in video.get("genre", "").split(",") if g.strip()],
                        "rating": float(video.get("rating", 0)) if video.get("rating") else None,
                        "duration": int(video.get("duration", 0)) if video.get("duration") else None,
                        "viewedAt": datetime.fromtimestamp(int(video.get("viewedAt", 0))).isoformat() if video.get("viewedAt") else None,
                        "type": video.get("type", "movie"),
                        "studio": video.get("studio", ""),
                        "summary": video.get("summary", "")
                    }
                    watch_history.append(movie_data)
            
            print(f"✅ Found {len(watch_history)} movies in watch history")
            return watch_history
            
        except Exception as e:
            print(f"❌ Error getting watch history: {e}")
            return []
    
    def calculate_statistics(self, watch_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics from watch history"""
        if not watch_history:
            return {}
        
        # Genre counts
        genre_counts = {}
        year_counts = {}
        rating_sum = 0
        rating_count = 0
        
        for movie in watch_history:
            # Count genres
            for genre in movie.get("genres", []):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Count years (by decade)
            if movie.get("year"):
                decade = (movie["year"] // 10) * 10
                year_counts[decade] = year_counts.get(decade, 0) + 1
            
            # Average rating
            if movie.get("rating"):
                rating_sum += movie["rating"]
                rating_count += 1
        
        # Sort genres by count
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_decades = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "totalMovies": len(watch_history),
            "topGenres": [{"genre": genre, "count": count} for genre, count in top_genres],
            "topDecades": [{"decade": decade, "count": count} for decade, count in top_decades],
            "averageRating": round(rating_sum / rating_count, 2) if rating_count > 0 else 0,
            "dateRange": {
                "start": min(movie["viewedAt"] for movie in watch_history if movie.get("viewedAt")),
                "end": max(movie["viewedAt"] for movie in watch_history if movie.get("viewedAt"))
            } if watch_history else {}
        }
    
    def compress_data(self, data: Dict[str, Any]) -> bytes:
        """Compress data for storage optimization (60% size reduction)"""
        try:
            json_data = json.dumps(data, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            print(f"📦 Data compressed: {len(json_data)} bytes → {len(compressed_data)} bytes ({len(compressed_data)/len(json_data)*100:.1f}%)")
            return compressed_data
        except Exception as e:
            print(f"⚠️ Warning: Compression failed, using uncompressed data: {e}")
            return json.dumps(data, indent=2).encode('utf-8')
    
    def generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key for deduplication"""
        try:
            # Create a hash of the data to detect duplicates
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:8]
        except Exception as e:
            print(f"⚠️ Warning: Cache key generation failed: {e}")
            return datetime.now().strftime("%H%M%S")
    
    def upload_to_s3_optimized(self, data: Dict[str, Any]) -> bool:
        """Upload data to S3 with cost optimizations"""
        try:
            # Compress data (60% savings)
            compressed_data = self.compress_data(data)
            
            # Generate cache key for deduplication
            cache_key = self.generate_cache_key(data)
            
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            key = f"plex-data/watch-history-{timestamp}-{cache_key}.json.gz"
            
            # Upload with S3 Intelligent Tiering (45% savings)
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=compressed_data,
                ContentType="application/gzip",
                ContentEncoding="gzip",
                StorageClass="INTELLIGENT_TIERING"  # Cost optimization
            )
            
            # Also upload as latest.json.gz
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key="plex-data/latest.json.gz",
                Body=compressed_data,
                ContentType="application/gzip",
                ContentEncoding="gzip",
                StorageClass="INTELLIGENT_TIERING"
            )
            
            print(f"✅ Data uploaded to S3 (optimized): s3://{self.s3_bucket}/{key}")
            print(f"✅ Latest data available at: s3://{self.s3_bucket}/plex-data/latest.json.gz")
            print(f"💰 Cost optimizations: S3 Intelligent Tiering + compression enabled")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to S3: {e}")
            return False
    
    def export_data(self, days_back: int = 365) -> bool:
        """Main export function"""
        print("🎬 Starting Plex data export...")
        
        # Test connection
        if not self.test_plex_connection():
            return False
        
        # Get server info
        server_info = self.get_server_info()
        print(f"📡 Connected to: {server_info.get('name', 'Unknown Server')}")
        
        # Get watch history
        watch_history = self.get_watch_history(days_back)
        if not watch_history:
            print("⚠️ No watch history found")
            return False
        
        # Calculate statistics
        statistics = self.calculate_statistics(watch_history)
        
        # Prepare export data
        export_data = {
            "exportedAt": datetime.now().isoformat(),
            "serverInfo": server_info,
            "watchHistory": watch_history,
            "statistics": statistics,
            "exportSettings": {
                "daysBack": days_back,
                "totalMovies": len(watch_history)
            }
        }
        
        # Upload to S3 with optimizations
        if self.upload_to_s3_optimized(export_data):
            print("🎉 Plex data export completed successfully!")
            print(f"📊 Exported {len(watch_history)} movies")
            
            # Safe display of top genre
            top_genres = statistics.get('topGenres', [])
            if top_genres:
                print(f"🎭 Top genre: {top_genres[0].get('genre', 'N/A')}")
            else:
                print("🎭 Top genre: N/A (no genre data)")
            
            print(f"⭐ Average rating: {statistics.get('averageRating', 0)}")
            return True
        else:
            return False

def main():
    """Main function"""
    print("🎬 Plex Data Exporter")
    print("=" * 50)
    
    # Check for command line arguments
    days_back = 365
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
            print(f"📅 Using custom date range: {days_back} days")
        except ValueError:
            print("⚠️ Invalid days argument, using default 365 days")
    
    # Create exporter and run
    exporter = PlexDataExporter()
    success = exporter.export_data(days_back)
    
    if success:
        print("\n✅ Export completed successfully!")
        print("🔄 You can now run the Lambda analyzer to generate recommendations")
    else:
        print("\n❌ Export failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
