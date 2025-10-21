#!/usr/bin/env python3
"""
Plex Data Blender - Combines Current Plex Statistics with Backup Data
This script intelligently merges data from multiple sources for comprehensive ML recommendations
"""

import json
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import hashlib

class PlexDataBlender:
    def __init__(self):
        self.combined_data = {
            "watchHistory": [],
            "statistics": {},
            "sources": [],
            "blendedAt": datetime.now().isoformat()
        }
        self.duplicate_threshold = 0.8  # Similarity threshold for deduplication
    
    def load_current_plex_data(self, file_path: str = None) -> Dict[str, Any]:
        """Load current Plex data from S3 or local file"""
        print("📡 Loading current Plex data...")
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded current Plex data from {file_path}")
                return data
        
        # Try to find the latest export
        export_files = glob.glob("plex-export-*.json") + glob.glob("enhanced-plex-history-*.json") + glob.glob("current-plex-data-*.json")
        if export_files:
            latest_file = max(export_files, key=os.path.getctime)
            with open(latest_file, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded current Plex data from {latest_file}")
                return data
        
        print("⚠️ No current Plex data found")
        return {}
    
    def load_backup_data(self, backup_directory: str = "backups") -> List[Dict[str, Any]]:
        """Load backup data from various sources including database files"""
        print("💾 Loading backup data...")
        
        backup_data = []
        
        # Look for backup files
        backup_patterns = [
            "backups/*.json",
            "backups/*/*.json",
            "plex-backup-*.json",
            "plex-db-*.json",
            "watch-history-*.json"
        ]
        
        for pattern in backup_patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    if file_path.endswith('.json'):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                backup_data.extend(data)
                            elif isinstance(data, dict) and 'watchHistory' in data:
                                backup_data.extend(data['watchHistory'])
                            else:
                                backup_data.append(data)
                        print(f"✅ Loaded backup data from {file_path}")
                except Exception as e:
                    print(f"⚠️ Error loading {file_path}: {e}")
        
        # Extract data from database files
        db_data = self.extract_database_backups(backup_directory)
        backup_data.extend(db_data)
        
        print(f"📊 Total backup items loaded: {len(backup_data)}")
        return backup_data
    
    def extract_database_backups(self, backup_directory: str) -> List[Dict[str, Any]]:
        """Extract data from Plex database backup files"""
        print("🗄️ Extracting data from database backups...")
        
        db_data = []
        
        # Look for database files in backup directories
        db_patterns = [
            f"{backup_directory}/*/com.plexapp.plugins.library.db",
            f"{backup_directory}/*/com.plexapp.plugins.library.db-*"
        ]
        
        for pattern in db_patterns:
            files = glob.glob(pattern)
            for db_file in files:
                try:
                    print(f"📊 Extracting from database: {db_file}")
                    extracted_data = self.extract_from_database(db_file)
                    if extracted_data:
                        db_data.extend(extracted_data)
                        print(f"✅ Extracted {len(extracted_data)} items from {db_file}")
                except Exception as e:
                    print(f"⚠️ Error extracting from {db_file}: {e}")
        
        return db_data
    
    def extract_from_database(self, db_path: str) -> List[Dict[str, Any]]:
        """Extract watch history from a Plex database file"""
        try:
            import sqlite3
            
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
                # Alternative structure
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
                                'title': movie.get('title', ''),
                                'year': str(movie.get('year', '')),
                                'rating': str(movie.get('rating', '0')),
                                'duration': movie.get('duration', 0),
                                'summary': movie.get('summary', ''),
                                'studio': movie.get('studio', ''),
                                'contentRating': movie.get('content_rating', ''),
                                'viewCount': str(movie.get('view_count', 0)),
                                'lastViewedAt': movie.get('last_viewed_at', ''),
                                'type': 'movie',
                                'source': 'database_backup',
                                'database_file': os.path.basename(db_path)
                            }
                            
                            # Convert timestamp if present
                            if normalized_movie['lastViewedAt']:
                                try:
                                    # Plex timestamps are usually Unix timestamps
                                    timestamp = int(normalized_movie['lastViewedAt'])
                                    normalized_movie['viewedAt'] = datetime.fromtimestamp(timestamp).isoformat()
                                except:
                                    normalized_movie['viewedAt'] = normalized_movie['lastViewedAt']
                            
                            movies.append(normalized_movie)
                        
                        conn.close()
                        return movies
                        
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e) or "no such table" in str(e):
                        continue  # Try next query
                    else:
                        raise e
            
            conn.close()
            return []
            
        except Exception as e:
            print(f"⚠️ Error extracting from database {db_path}: {e}")
            return []
    
    def generate_movie_id(self, movie: Dict[str, Any]) -> str:
        """Generate a unique ID for a movie"""
        title = movie.get('title', '').lower().strip()
        year = str(movie.get('year', ''))
        
        # Normalize title (remove special characters, extra spaces)
        normalized_title = ''.join(c for c in title if c.isalnum() or c.isspace()).strip()
        normalized_title = ' '.join(normalized_title.split())
        
        return hashlib.md5(f"{normalized_title}_{year}".encode()).hexdigest()[:12]
    
    def calculate_similarity(self, movie1: Dict[str, Any], movie2: Dict[str, Any]) -> float:
        """Calculate similarity between two movies"""
        title1 = movie1.get('title', '').lower().strip()
        title2 = movie2.get('title', '').lower().strip()
        year1 = movie1.get('year', '')
        year2 = movie2.get('year', '')
        
        # Exact match
        if title1 == title2 and year1 == year2:
            return 1.0
        
        # Title similarity (simple word overlap)
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        title_similarity = len(intersection) / len(union) if union else 0.0
        
        # Year similarity
        year_similarity = 1.0 if year1 == year2 else 0.0
        
        # Combined similarity (weighted)
        return (title_similarity * 0.8) + (year_similarity * 0.2)
    
    def deduplicate_movies(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate movies based on similarity"""
        print("🔄 Deduplicating movies...")
        
        unique_movies = []
        seen_ids = set()
        
        for movie in movies:
            movie_id = self.generate_movie_id(movie)
            
            # Check for exact duplicates
            if movie_id in seen_ids:
                continue
            
            # Check for similar movies
            is_duplicate = False
            for existing_movie in unique_movies:
                similarity = self.calculate_similarity(movie, existing_movie)
                if similarity > self.duplicate_threshold:
                    # Merge data from both sources
                    merged_movie = self.merge_movie_data(existing_movie, movie)
                    unique_movies[unique_movies.index(existing_movie)] = merged_movie
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_movies.append(movie)
                seen_ids.add(movie_id)
        
        print(f"✅ Deduplicated: {len(movies)} → {len(unique_movies)} movies")
        return unique_movies
    
    def merge_movie_data(self, movie1: Dict[str, Any], movie2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data from two movie entries"""
        merged = movie1.copy()
        
        # Merge view counts
        view_count1 = int(movie1.get('viewCount', 0))
        view_count2 = int(movie2.get('viewCount', 0))
        merged['viewCount'] = max(view_count1, view_count2)
        
        # Merge ratings (use the higher rating)
        rating1 = float(movie1.get('rating', 0))
        rating2 = float(movie2.get('rating', 0))
        merged['rating'] = max(rating1, rating2) if rating1 > 0 and rating2 > 0 else max(rating1, rating2)
        
        # Merge genres (combine unique genres)
        genres1 = movie1.get('genres', [])
        genres2 = movie2.get('genres', [])
        if isinstance(genres1, list) and isinstance(genres2, list):
            merged['genres'] = list(set(genres1 + genres2))
        elif isinstance(genres1, list):
            merged['genres'] = genres1
        elif isinstance(genres2, list):
            merged['genres'] = genres2
        
        # Merge TMDB metadata (prefer more complete data)
        tmdb1 = movie1.get('tmdb_metadata', {})
        tmdb2 = movie2.get('tmdb_metadata', {})
        if len(tmdb2) > len(tmdb1):
            merged['tmdb_metadata'] = tmdb2
        elif len(tmdb1) > 0:
            merged['tmdb_metadata'] = tmdb1
        
        # Add source tracking
        sources = merged.get('sources', [])
        if 'sources' not in movie1:
            sources.append('current_plex')
        if 'sources' not in movie2:
            sources.append('backup_data')
        merged['sources'] = list(set(sources))
        
        return merged
    
    def blend_data_sources(self, current_data: Dict[str, Any], backup_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Blend current Plex data with backup data"""
        print("🔄 Blending data sources...")
        
        # Extract watch history from current data
        if isinstance(current_data, list):
            current_movies = current_data
        elif isinstance(current_data, dict):
            current_movies = current_data.get('watchHistory', [])
        else:
            current_movies = []
        
        # Combine all movies
        all_movies = current_movies + backup_data
        
        print(f"📊 Total movies before blending: {len(all_movies)}")
        print(f"   - Current Plex: {len(current_movies)}")
        print(f"   - Backup data: {len(backup_data)}")
        
        # Deduplicate and merge
        blended_movies = self.deduplicate_movies(all_movies)
        
        # Calculate blended statistics
        blended_stats = self.calculate_blended_statistics(blended_movies)
        
        # Prepare blended data
        blended_data = {
            "watchHistory": blended_movies,
            "statistics": blended_stats,
            "sources": {
                "current_plex": len(current_movies),
                "backup_data": len(backup_data),
                "blended_total": len(blended_movies),
                "deduplication_removed": len(all_movies) - len(blended_movies)
            },
            "blendedAt": datetime.now().isoformat(),
            "exportedAt": datetime.now().isoformat()
        }
        
        print(f"✅ Blending complete: {len(blended_movies)} unique movies")
        return blended_data
    
    def calculate_blended_statistics(self, movies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from blended data"""
        print("📊 Calculating blended statistics...")
        
        stats = {
            "totalMovies": len(movies),
            "dateRange": {},
            "genreDistribution": {},
            "decadeDistribution": {},
            "ratingDistribution": {},
            "sourceDistribution": {},
            "enrichedMovies": 0,
            "averageRating": 0,
            "totalWatchTime": 0
        }
        
        if not movies:
            return stats
        
        # Calculate date range
        dates = []
        for movie in movies:
            if movie.get('viewedAt'):
                try:
                    dates.append(datetime.fromisoformat(movie['viewedAt'].replace('Z', '+00:00')))
                except:
                    pass
        
        if dates:
            stats["dateRange"] = {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat(),
                "span_days": (max(dates) - min(dates)).days
            }
        
        # Calculate distributions
        rating_sum = 0
        rating_count = 0
        
        for movie in movies:
            # Genre distribution
            genres = movie.get('genres', [])
            if isinstance(genres, list):
                for genre in genres:
                    stats["genreDistribution"][genre] = stats["genreDistribution"].get(genre, 0) + 1
            
            # Decade distribution
            year = movie.get('year')
            if year:
                try:
                    decade = (int(year) // 10) * 10
                    stats["decadeDistribution"][f"{decade}s"] = stats["decadeDistribution"].get(f"{decade}s", 0) + 1
                except:
                    pass
            
            # Rating distribution
            rating = movie.get('rating')
            if rating:
                try:
                    rating_val = float(rating)
                    rating_sum += rating_val
                    rating_count += 1
                    rating_range = int(rating_val)
                    stats["ratingDistribution"][rating_range] = stats["ratingDistribution"].get(rating_range, 0) + 1
                except:
                    pass
            
            # Source distribution
            sources = movie.get('sources', ['unknown'])
            for source in sources:
                stats["sourceDistribution"][source] = stats["sourceDistribution"].get(source, 0) + 1
            
            # Enriched movies count
            if movie.get('tmdb_metadata'):
                stats["enrichedMovies"] += 1
            
            # Watch time
            duration = movie.get('duration')
            if duration:
                try:
                    stats["totalWatchTime"] += int(duration)
                except:
                    pass
        
        # Calculate average rating
        if rating_count > 0:
            stats["averageRating"] = rating_sum / rating_count
        
        # Sort distributions
        stats["topGenres"] = sorted(stats["genreDistribution"].items(), key=lambda x: x[1], reverse=True)[:10]
        stats["topDecades"] = sorted(stats["decadeDistribution"].items(), key=lambda x: x[1], reverse=True)[:5]
        
        print(f"✅ Statistics calculated:")
        print(f"   - Total movies: {stats['totalMovies']}")
        print(f"   - Enriched movies: {stats['enrichedMovies']}")
        print(f"   - Average rating: {stats['averageRating']:.1f}")
        print(f"   - Top genre: {stats['topGenres'][0][0] if stats['topGenres'] else 'N/A'}")
        
        return stats
    
    def save_blended_data(self, blended_data: Dict[str, Any], output_file: str = None) -> str:
        """Save blended data to file and S3"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_file = f"blended-plex-data-{timestamp}.json"
        
        # Save locally
        with open(output_file, 'w') as f:
            json.dump(blended_data, f, indent=2)
        
        print(f"💾 Blended data saved to: {output_file}")
        
        # Try to upload to S3
        try:
            import boto3
            s3_client = boto3.client('s3', region_name='us-east-1')
            
            # Upload as latest
            s3_client.put_object(
                Bucket='plex-recommendations-c7c49ce4',
                Key='plex-data/latest.json',
                Body=json.dumps(blended_data, indent=2),
                ContentType='application/json'
            )
            
            # Upload as timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            s3_client.put_object(
                Bucket='plex-recommendations-c7c49ce4',
                Key=f'plex-data/blended-{timestamp}.json',
                Body=json.dumps(blended_data, indent=2),
                ContentType='application/json'
            )
            
            print("✅ Blended data uploaded to S3")
            
        except Exception as e:
            print(f"⚠️ Could not upload to S3: {e}")
        
        return output_file
    
    def run_blending(self, current_data_file: str = None, backup_directory: str = "backups") -> str:
        """Main blending function"""
        print("🎬 Plex Data Blender")
        print("=" * 50)
        
        # Load current data
        current_data = self.load_current_plex_data(current_data_file)
        
        # Load backup data
        backup_data = self.load_backup_data(backup_directory)
        
        if not current_data and not backup_data:
            print("❌ No data sources found to blend")
            return None
        
        # Blend the data
        blended_data = self.blend_data_sources(current_data, backup_data)
        
        # Save blended data
        output_file = self.save_blended_data(blended_data)
        
        print("\n🎉 Data blending complete!")
        print(f"📊 Final statistics:")
        print(f"   - Total movies: {blended_data['statistics']['totalMovies']}")
        print(f"   - From current Plex: {blended_data['sources']['current_plex']}")
        print(f"   - From backups: {blended_data['sources']['backup_data']}")
        print(f"   - Duplicates removed: {blended_data['sources']['deduplication_removed']}")
        print(f"   - Enriched with TMDB: {blended_data['statistics']['enrichedMovies']}")
        
        return output_file

def main():
    blender = PlexDataBlender()
    
    # You can specify custom paths here
    current_data_file = None  # Will auto-detect
    backup_directory = "backups"  # Directory containing backup files
    
    output_file = blender.run_blending(current_data_file, backup_directory)
    
    if output_file:
        print(f"\n🚀 Next steps:")
        print(f"   1. Test the ML recommendations: open website/index.html")
        print(f"   2. Click 'Update Recommendations' to see blended data in action")
        print(f"   3. Check the ML Analytics section for performance metrics")

if __name__ == "__main__":
    main()
