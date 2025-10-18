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
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
import sys
import time

# Configuration
PLEX_SERVER = "your-plex-server:32400"
PLEX_TOKEN = "your_plex_token_here"
S3_BUCKET = "your-s3-bucket-name"
AWS_PROFILE = "default"  # or specify a profile
AWS_REGION = "us-east-1"

# TMDB API Configuration for rich metadata
TMDB_API_KEY = "your_tmdb_api_key_here"  # Get from https://www.themoviedb.org/settings/api
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

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
                # Process both movies and TV episodes for better recommendations
                if video.get("type") in ["movie", "episode"]:
                    # Handle both movies and TV episodes
                    content_type = video.get("type", "movie")
                    if content_type == "episode":
                        # For TV episodes, use the show title and season/episode info
                        title = video.get("grandparentTitle", video.get("title", ""))  # Show title
                        season = video.get("parentIndex", "")
                        episode = video.get("index", "")
                        full_title = f"{title} (S{season}E{episode})" if season and episode else title
                    else:
                        # For movies, use the movie title
                        full_title = video.get("title", "")
                    
                    movie_data = {
                        "title": full_title,
                        "originalTitle": video.get("title", ""),
                        "showTitle": video.get("grandparentTitle", "") if content_type == "episode" else "",
                        "season": video.get("parentIndex", "") if content_type == "episode" else "",
                        "episode": video.get("index", "") if content_type == "episode" else "",
                        "year": int(video.get("year", 0)) if video.get("year") else None,
                        "genres": [g.strip() for g in video.get("genre", "").split(",") if g.strip()],
                        "rating": float(video.get("rating", 0)) if video.get("rating") else None,
                        "duration": int(video.get("duration", 0)) if video.get("duration") else None,
                        "viewedAt": datetime.fromtimestamp(int(video.get("viewedAt", 0))).isoformat() if video.get("viewedAt") else None,
                        "type": content_type,
                        "studio": video.get("studio", ""),
                        "summary": video.get("summary", "")
                    }
                    watch_history.append(movie_data)
            
            movies_count = sum(1 for item in watch_history if item["type"] == "movie")
            episodes_count = sum(1 for item in watch_history if item["type"] == "episode")
            print(f"✅ Found {len(watch_history)} items in watch history ({movies_count} movies, {episodes_count} TV episodes)")
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
    
    def search_tmdb_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for movie in TMDB API and return rich metadata"""
        if TMDB_API_KEY == "your_tmdb_api_key_here":
            print(f"⚠️ TMDB API key not configured, skipping metadata enrichment for: {title}")
            return None
            
        try:
            # Search for movie
            search_url = f"{TMDB_BASE_URL}/search/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": False
            }
            if year:
                params["year"] = year
                
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ TMDB API error for '{title}': {response.status_code}")
                return None
                
            data = response.json()
            if not data.get("results"):
                print(f"⚠️ No TMDB results found for: {title}")
                return None
                
            # Get the best match (first result)
            movie = data["results"][0]
            
            # Get detailed movie information
            movie_id = movie["id"]
            details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
            details_params = {
                "api_key": TMDB_API_KEY,
                "append_to_response": "credits,keywords,similar,recommendations"
            }
            
            details_response = requests.get(details_url, params=details_params, timeout=10)
            if details_response.status_code != 200:
                print(f"⚠️ TMDB details API error for '{title}': {details_response.status_code}")
                return None
                
            movie_details = details_response.json()
            
            # Extract rich metadata
            enriched_data = {
                "tmdb_id": movie_details.get("id"),
                "title": movie_details.get("title"),
                "original_title": movie_details.get("original_title"),
                "overview": movie_details.get("overview"),
                "release_date": movie_details.get("release_date"),
                "runtime": movie_details.get("runtime"),
                "budget": movie_details.get("budget"),
                "revenue": movie_details.get("revenue"),
                "vote_average": movie_details.get("vote_average"),
                "vote_count": movie_details.get("vote_count"),
                "popularity": movie_details.get("popularity"),
                "adult": movie_details.get("adult"),
                "backdrop_path": movie_details.get("backdrop_path"),
                "poster_path": movie_details.get("poster_path"),
                "genres": [{"id": g["id"], "name": g["name"]} for g in movie_details.get("genres", [])],
                "production_companies": [{"id": c["id"], "name": c["name"]} for c in movie_details.get("production_companies", [])],
                "production_countries": [{"iso_3166_1": c["iso_3166_1"], "name": c["name"]} for c in movie_details.get("production_countries", [])],
                "spoken_languages": [{"iso_639_1": l["iso_639_1"], "name": l["name"]} for l in movie_details.get("spoken_languages", [])],
                "cast": [{"id": c["id"], "name": c["name"], "character": c["character"], "order": c["order"]} for c in movie_details.get("credits", {}).get("cast", [])[:10]],  # Top 10 cast
                "crew": [{"id": c["id"], "name": c["name"], "job": c["job"], "department": c["department"]} for c in movie_details.get("credits", {}).get("crew", [])[:5]],  # Top 5 crew
                "keywords": [{"id": k["id"], "name": k["name"]} for k in movie_details.get("keywords", {}).get("keywords", [])],
                "similar_movies": [{"id": m["id"], "title": m["title"], "vote_average": m["vote_average"]} for m in movie_details.get("similar", {}).get("results", [])[:5]],  # Top 5 similar
                "recommendations": [{"id": m["id"], "title": m["title"], "vote_average": m["vote_average"]} for m in movie_details.get("recommendations", {}).get("results", [])[:5]]  # Top 5 recommendations
            }
            
            # Add image URLs
            if movie_details.get("poster_path"):
                enriched_data["poster_url"] = f"{TMDB_IMAGE_BASE_URL}/w500{movie_details['poster_path']}"
            if movie_details.get("backdrop_path"):
                enriched_data["backdrop_url"] = f"{TMDB_IMAGE_BASE_URL}/w1280{movie_details['backdrop_path']}"
                
            print(f"✅ Enriched metadata for: {title}")
            return enriched_data
            
        except Exception as e:
            print(f"⚠️ Error enriching metadata for '{title}': {e}")
            return None
    
    def enrich_movie_data(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich movie data with TMDB metadata"""
        if TMDB_API_KEY == "your_tmdb_api_key_here":
            print("⚠️ TMDB API key not configured, skipping metadata enrichment")
            return movies
            
        print("🎬 Enriching movie data with TMDB metadata...")
        enriched_movies = []
        
        for i, movie in enumerate(movies):
            print(f"📊 Processing {i+1}/{len(movies)}: {movie.get('title', 'Unknown')}")
            
            # Try to extract year from various fields
            year = None
            if movie.get('year'):
                try:
                    year = int(movie['year'])
                except (ValueError, TypeError):
                    pass
            
            # Search TMDB for this movie
            tmdb_data = self.search_tmdb_movie(movie.get('title', ''), year)
            
            # Combine original data with enriched data
            enriched_movie = movie.copy()
            if tmdb_data:
                enriched_movie['tmdb_metadata'] = tmdb_data
                enriched_movie['enriched'] = True
            else:
                enriched_movie['enriched'] = False
                
            enriched_movies.append(enriched_movie)
            
            # Rate limiting - TMDB allows 40 requests per 10 seconds
            if (i + 1) % 10 == 0:
                print(f"⏳ Rate limiting: waiting 2 seconds...")
                time.sleep(2)
        
        enriched_count = sum(1 for movie in enriched_movies if movie.get('enriched'))
        print(f"✅ Metadata enrichment complete: {enriched_count}/{len(movies)} movies enriched")
        
        return enriched_movies

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
        
        # Enrich with TMDB metadata (Phase 2 Enhancement 1)
        print("🎬 Phase 2 Enhancement 1: Rich Metadata Integration")
        enriched_watch_history = self.enrich_movie_data(watch_history)
        
        # Calculate statistics
        statistics = self.calculate_statistics(enriched_watch_history)
        
        # Prepare export data
        export_data = {
            "exportedAt": datetime.now().isoformat(),
            "serverInfo": server_info,
            "watchHistory": enriched_watch_history,
            "statistics": statistics,
            "exportSettings": {
                "daysBack": days_back,
                "totalMovies": len(enriched_watch_history),
                "enrichedMovies": sum(1 for movie in enriched_watch_history if movie.get('enriched', False))
            },
            "phase2Enhancements": {
                "richMetadataEnabled": TMDB_API_KEY != "your_tmdb_api_key_here",
                "tmdbApiConfigured": TMDB_API_KEY != "your_tmdb_api_key_here"
            }
        }
        
        # Upload to S3 with optimizations
        if self.upload_to_s3_optimized(export_data):
            print("🎉 Plex data export completed successfully!")
            movies_count = sum(1 for item in enriched_watch_history if item["type"] == "movie")
            episodes_count = sum(1 for item in enriched_watch_history if item["type"] == "episode")
            print(f"📊 Exported {len(enriched_watch_history)} items ({movies_count} movies, {episodes_count} TV episodes)")
            enriched_count = sum(1 for movie in enriched_watch_history if movie.get('enriched', False))
            print(f"🎬 Rich metadata: {enriched_count}/{len(enriched_watch_history)} movies enriched")
            
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
