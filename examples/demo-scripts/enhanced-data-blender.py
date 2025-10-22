#!/usr/bin/env python3
"""
Enhanced Plex Data Blender - Comprehensive Data Integration
Combines current Plex data with historical backups from multiple servers
"""

import json
import os
import glob
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import hashlib
import requests

class EnhancedPlexDataBlender:
    def __init__(self):
        self.combined_data = {
            "watchHistory": [],
            "statistics": {},
            "sources": {
                "current_plex": 0,
                "azog_backup": 0,
                "bilbo_backup": 0,
                "deduplication_removed": 0,
                "total_unique_movies": 0
            },
            "blendedAt": datetime.now().isoformat()
        }
        
        # Configuration
        self.PLEX_SERVER = "192.168.0.109:32400"
        self.PLEX_TOKEN = "iUAXXUBe9Hno42-aHy5E"
        self.S3_BUCKET = "plex-recommendations-c7c49ce4"
        
    def get_current_plex_data(self) -> List[Dict[str, Any]]:
        """Get current watch history from live Plex server"""
        print("📡 Getting current Plex data from 192.168.0.109...")
        
        try:
            # Test connection
            url = f"http://{self.PLEX_SERVER}/status/sessions"
            headers = {"X-Plex-Token": self.PLEX_TOKEN}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Plex server returned status {response.status_code}")
                return []
            
            print("✅ Connected to current Plex server")
            
            # Get library sections
            url = f"http://{self.PLEX_SERVER}/library/sections"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print("❌ Could not get library sections")
                return []
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            all_movies = []
            
            for section in root.findall("Directory"):
                if section.get("type") == "1":  # Movie section
                    section_id = section.get("key")
                    section_title = section.get("title")
                    
                    print(f"📽️ Processing movie section: {section_title}")
                    
                    # Get all movies from this section
                    url = f"http://{self.PLEX_SERVER}/library/sections/{section_id}/all"
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        movies_root = ET.fromstring(response.content)
                        
                        for video in movies_root.findall("Video"):
                            if video.get("type") == "movie":
                                movie_data = {
                                    "title": video.get("title", ""),
                                    "year": video.get("year", ""),
                                    "rating": video.get("rating", "0"),
                                    "duration": video.get("duration", "0"),
                                    "summary": video.get("summary", ""),
                                    "studio": video.get("studio", ""),
                                    "contentRating": video.get("contentRating", ""),
                                    "viewCount": video.get("viewCount", "0"),
                                    "lastViewedAt": video.get("lastViewedAt", ""),
                                    "type": "movie",
                                    "source": "current_plex",
                                    "section": section_title
                                }
                                
                                # Convert timestamp if present
                                if movie_data["lastViewedAt"]:
                                    try:
                                        timestamp = int(movie_data["lastViewedAt"])
                                        movie_data["viewedAt"] = datetime.fromtimestamp(timestamp).isoformat()
                                    except:
                                        movie_data["viewedAt"] = movie_data["lastViewedAt"]
                                
                                all_movies.append(movie_data)
            
            print(f"✅ Loaded {len(all_movies)} movies from current Plex server")
            return all_movies
            
        except Exception as e:
            print(f"❌ Error getting current Plex data: {e}")
            return []
    
    def extract_from_database(self, db_path: str, server_name: str) -> List[Dict[str, Any]]:
        """Extract watch history from a Plex database file"""
        try:
            print(f"🗄️ Extracting from {server_name} database: {os.path.basename(db_path)}")
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try different table structures for different Plex versions
            queries = [
                # Modern Plex structure
                """
                SELECT 
                    m.title,
                    m.year,
                    m.rating,
                    m.duration,
                    m.summary,
                    m.studio,
                    m.content_rating,
                    m.view_count,
                    m.last_viewed_at,
                    m.media_item_id
                FROM metadata_items m
                WHERE m.metadata_type = 1 
                AND m.view_count > 0
                ORDER BY m.last_viewed_at DESC
                """,
                # Alternative structure with view history
                """
                SELECT 
                    m.title,
                    m.year,
                    m.rating,
                    m.duration,
                    m.summary,
                    m.studio,
                    m.content_rating,
                    COUNT(v.id) as view_count,
                    MAX(v.started_at) as last_viewed_at,
                    m.id
                FROM metadata_items m
                LEFT JOIN media_parts p ON m.id = p.metadata_item_id
                LEFT JOIN media_streams s ON p.id = s.media_part_id
                LEFT JOIN view_history v ON m.id = v.metadata_item_id
                WHERE m.metadata_type = 1
                GROUP BY m.id
                HAVING view_count > 0
                ORDER BY last_viewed_at DESC
                """,
                # Simple structure
                """
                SELECT 
                    title,
                    year,
                    rating,
                    duration,
                    summary,
                    studio,
                    content_rating,
                    view_count,
                    last_viewed_at,
                    id
                FROM metadata_items
                WHERE metadata_type = 1 
                AND view_count > 0
                ORDER BY last_viewed_at DESC
                """
            ]
            
            for query in queries:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        columns = [description[0] for description in cursor.description]
                        
                        # Convert to list of dictionaries
                        movies = []
                        for row in rows:
                            movie = dict(zip(columns, row))
                            
                            # Normalize the data
                            normalized_movie = {
                                "title": movie.get("title", ""),
                                "year": str(movie.get("year", "")),
                                "rating": str(movie.get("rating", "0")),
                                "duration": movie.get("duration", 0),
                                "summary": movie.get("summary", ""),
                                "studio": movie.get("studio", ""),
                                "contentRating": movie.get("content_rating", ""),
                                "viewCount": str(movie.get("view_count", 0)),
                                "lastViewedAt": movie.get("last_viewed_at", ""),
                                "type": "movie",
                                "source": f"{server_name}_backup",
                                "database_file": os.path.basename(db_path)
                            }
                            
                            # Convert timestamp if present
                            if normalized_movie["lastViewedAt"]:
                                try:
                                    # Plex timestamps are usually Unix timestamps
                                    timestamp = int(normalized_movie["lastViewedAt"])
                                    normalized_movie["viewedAt"] = datetime.fromtimestamp(timestamp).isoformat()
                                except:
                                    normalized_movie["viewedAt"] = normalized_movie["lastViewedAt"]
                            
                            movies.append(normalized_movie)
                        
                        conn.close()
                        print(f"✅ Extracted {len(movies)} movies from {server_name}")
                        return movies
                        
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e) or "no such table" in str(e):
                        continue  # Try next query
                    else:
                        raise e
            
            conn.close()
            print(f"⚠️ No data found in {server_name} database")
            return []
            
        except Exception as e:
            print(f"⚠️ Error extracting from {server_name} database {db_path}: {e}")
            return []
    
    def load_backup_data(self, backup_directory: str = "backups") -> List[Dict[str, Any]]:
        """Load data from all backup sources"""
        print("📦 Loading backup data from multiple sources...")
        
        all_backup_data = []
        
        # Process azog_plex backups
        azog_path = f"{backup_directory}/azog_plex"
        if os.path.exists(azog_path):
            print(f"🖥️ Processing azog_plex backups...")
            azog_files = glob.glob(f"{azog_path}/com.plexapp.plugins.library.db*")
            for db_file in azog_files:
                if not db_file.endswith(("-shm", "-wal", ".backup")):
                    data = self.extract_from_database(db_file, "azog")
                    all_backup_data.extend(data)
        
        # Process bilbo_plex backups
        bilbo_path = f"{backup_directory}/bilbo_plex"
        if os.path.exists(bilbo_path):
            print(f"🖥️ Processing bilbo_plex backups...")
            bilbo_files = glob.glob(f"{bilbo_path}/com.plexapp.plugins.library.db*")
            for db_file in bilbo_files:
                if not db_file.endswith(("-shm", "-wal", ".backup")):
                    data = self.extract_from_database(db_file, "bilbo")
                    all_backup_data.extend(data)
        
        print(f"📊 Total backup items loaded: {len(all_backup_data)}")
        return all_backup_data
    
    def deduplicate_movies(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate movies based on title and year"""
        print("🔄 Deduplicating movies...")
        
        seen = set()
        unique_movies = []
        duplicates_removed = 0
        
        for movie in movies:
            # Create a unique key based on title and year
            key = f"{movie.get('title', '').lower().strip()}_{movie.get('year', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_movies.append(movie)
            else:
                duplicates_removed += 1
                # Keep the one with more view data
                for i, existing in enumerate(unique_movies):
                    if f"{existing.get('title', '').lower().strip()}_{existing.get('year', '')}" == key:
                        if int(movie.get('viewCount', 0)) > int(existing.get('viewCount', 0)):
                            unique_movies[i] = movie
                        break
        
        print(f"✅ Deduplication complete: {duplicates_removed} duplicates removed")
        return unique_movies
    
    def calculate_statistics(self, movies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        print("📊 Calculating statistics...")
        
        if not movies:
            return {"totalMovies": 0, "totalViews": 0, "averageRating": 0}
        
        total_views = sum(int(movie.get("viewCount", 0)) for movie in movies)
        ratings = [float(movie.get("rating", 0)) for movie in movies if movie.get("rating", "0") != "0"]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Genre analysis (if available)
        genres = {}
        for movie in movies:
            # This would need TMDB integration for proper genre analysis
            pass
        
        # Decade analysis
        decades = {}
        for movie in movies:
            year = movie.get("year", "")
            if year and year.isdigit():
                decade = f"{year[:3]}0s"
                decades[decade] = decades.get(decade, 0) + 1
        
        return {
            "totalMovies": len(movies),
            "totalViews": total_views,
            "averageRating": round(average_rating, 2),
            "topDecades": sorted(decades.items(), key=lambda x: x[1], reverse=True)[:5],
            "sources": {
                "current_plex": len([m for m in movies if m.get("source") == "current_plex"]),
                "azog_backup": len([m for m in movies if m.get("source") == "azog_backup"]),
                "bilbo_backup": len([m for m in movies if m.get("source") == "bilbo_backup"])
            }
        }
    
    def save_blended_data(self, blended_data: Dict[str, Any]) -> str:
        """Save blended data to file and optionally upload to S3"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = f"blended-plex-data-{timestamp}.json"
        
        print(f"💾 Saving blended data to {output_file}...")
        
        with open(output_file, 'w') as f:
            json.dump(blended_data, f, indent=2)
        
        print(f"✅ Blended data saved to {output_file}")
        
        # Try to upload to S3
        try:
            import boto3
            s3 = boto3.client('s3')
            s3_key = f"plex-recommendations/{output_file}"
            s3.upload_file(output_file, self.S3_BUCKET, s3_key)
            print(f"☁️ Uploaded to S3: s3://{self.S3_BUCKET}/{s3_key}")
        except Exception as e:
            print(f"⚠️ Could not upload to S3: {e}")
        
        return output_file
    
    def run_comprehensive_blending(self) -> str:
        """Main blending function that combines all data sources"""
        print("🎬 Enhanced Plex Data Blender")
        print("=" * 60)
        
        # Get current Plex data
        current_data = self.get_current_plex_data()
        
        # Get backup data
        backup_data = self.load_backup_data()
        
        # Combine all data
        all_movies = current_data + backup_data
        
        if not all_movies:
            print("❌ No data sources found to blend")
            return None
        
        print(f"📊 Raw data collected: {len(all_movies)} total items")
        
        # Deduplicate
        unique_movies = self.deduplicate_movies(all_movies)
        
        # Calculate statistics
        statistics = self.calculate_statistics(unique_movies)
        
        # Create blended data structure
        blended_data = {
            "watchHistory": unique_movies,
            "statistics": statistics,
            "sources": {
                "current_plex": len([m for m in unique_movies if m.get("source") == "current_plex"]),
                "azog_backup": len([m for m in unique_movies if m.get("source") == "azog_backup"]),
                "bilbo_backup": len([m for m in unique_movies if m.get("source") == "bilbo_backup"]),
                "deduplication_removed": len(all_movies) - len(unique_movies),
                "total_unique_movies": len(unique_movies)
            },
            "blendedAt": datetime.now().isoformat(),
            "dataQuality": {
                "completeness": "high" if len(unique_movies) > 50 else "medium",
                "reliability": "high" if len(backup_data) > 0 else "medium",
                "recency": "high" if len(current_data) > 0 else "low"
            }
        }
        
        # Save blended data
        output_file = self.save_blended_data(blended_data)
        
        print("\n🎉 Enhanced data blending complete!")
        print(f"📊 Final statistics:")
        print(f"   - Total unique movies: {blended_data['statistics']['totalMovies']}")
        print(f"   - From current Plex: {blended_data['sources']['current_plex']}")
        print(f"   - From azog backup: {blended_data['sources']['azog_backup']}")
        print(f"   - From bilbo backup: {blended_data['sources']['bilbo_backup']}")
        print(f"   - Duplicates removed: {blended_data['sources']['deduplication_removed']}")
        print(f"   - Data quality: {blended_data['dataQuality']['completeness']} completeness, {blended_data['dataQuality']['reliability']} reliability")
        
        return output_file

def main():
    blender = EnhancedPlexDataBlender()
    output_file = blender.run_comprehensive_blending()
    
    if output_file:
        print(f"\n🚀 Next steps:")
        print(f"   1. The blended data is saved in: {output_file}")
        print(f"   2. Update your Lambda function to use this enhanced dataset")
        print(f"   3. Run the recommendation update to see improved results")
        print(f"   4. Check the ML Analytics section for better accuracy metrics")

if __name__ == "__main__":
    main()
