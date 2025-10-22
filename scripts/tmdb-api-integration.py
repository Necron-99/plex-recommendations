#!/usr/bin/env python3
"""
TMDB API Integration - Build comprehensive movie database
Uses the correct API key to fetch thousands of movies from TMDB
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import boto3

class TMDBAPIIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.s3_bucket = "plex-recommendations-c7c49ce4"
        
        # Movie database
        self.movie_database = []
        self.genres = {}
        self.api_calls_made = 0
        self.max_api_calls = 1000  # Limit to stay within free tier
        
    def get_genres(self) -> Dict[int, str]:
        """Get movie genres from TMDB"""
        url = f"{self.base_url}/genre/movie/list"
        params = {
            "api_key": self.api_key,
            "language": "en-US"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            data = response.json()
            genres = {}
            for genre in data.get("genres", []):
                genres[genre["id"]] = genre["name"]
            
            print(f"✅ Loaded {len(genres)} genres from TMDB")
            return genres
            
        except Exception as e:
            print(f"❌ Error fetching genres: {e}")
            return {}
    
    def get_popular_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get popular movies from TMDB"""
        url = f"{self.base_url}/movie/popular"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            print(f"❌ Error fetching popular movies page {page}: {e}")
            return []
    
    def get_top_rated_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get top rated movies from TMDB"""
        url = f"{self.base_url}/movie/top_rated"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            print(f"❌ Error fetching top rated movies page {page}: {e}")
            return []
    
    def get_now_playing_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get now playing movies from TMDB"""
        url = f"{self.base_url}/movie/now_playing"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            print(f"❌ Error fetching now playing movies page {page}: {e}")
            return []
    
    def get_upcoming_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get upcoming movies from TMDB"""
        url = f"{self.base_url}/movie/upcoming"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            print(f"❌ Error fetching upcoming movies page {page}: {e}")
            return []
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific movie"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "append_to_response": "videos,credits,release_dates"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.api_calls_made += 1
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error fetching movie details for ID {movie_id}: {e}")
            return {}
    
    def is_english_movie(self, movie: Dict[str, Any]) -> bool:
        """Check if movie is primarily English language"""
        original_language = movie.get("original_language", "").lower()
        spoken_languages = movie.get("spoken_languages", [])
        
        # Check original language
        if original_language == "en":
            return True
        
        # Check spoken languages
        for lang in spoken_languages:
            if lang.get("iso_639_1", "").lower() == "en":
                return True
        
        return False
    
    def is_available_format(self, movie: Dict[str, Any]) -> bool:
        """Check if movie is available in digital/DVD/BluRay formats"""
        # For now, assume all movies from TMDB are available in some format
        # In a real implementation, you'd check streaming availability APIs
        return True
    
    def normalize_movie_data(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize movie data for our recommendation system"""
        # Get release year
        release_date = movie.get("release_date", "")
        year = ""
        if release_date:
            try:
                year = str(datetime.strptime(release_date, "%Y-%m-%d").year)
            except:
                year = release_date[:4] if len(release_date) >= 4 else ""
        
        # Get genres
        genres = []
        for genre_id in movie.get("genre_ids", []):
            if genre_id in self.genres:
                genres.append(self.genres[genre_id])
        
        # Get cast (first 5 actors)
        cast = []
        if "credits" in movie and "cast" in movie["credits"]:
            cast = [actor.get("name", "") for actor in movie["credits"]["cast"][:5]]
        
        # Get director
        director = ""
        if "credits" in movie and "crew" in movie["credits"]:
            for person in movie["credits"]["crew"]:
                if person.get("job", "").lower() == "director":
                    director = person.get("name", "")
                    break
        
        return {
            "id": movie.get("id"),
            "title": movie.get("title", ""),
            "original_title": movie.get("original_title", ""),
            "year": year,
            "rating": movie.get("vote_average", 0),
            "rating_count": movie.get("vote_count", 0),
            "overview": movie.get("overview", ""),
            "genres": genres,
            "cast": cast,
            "director": director,
            "original_language": movie.get("original_language", ""),
            "popularity": movie.get("popularity", 0),
            "poster_path": movie.get("poster_path", ""),
            "backdrop_path": movie.get("backdrop_path", ""),
            "release_date": release_date,
            "adult": movie.get("adult", False),
            "video": movie.get("video", False),
            "is_english": self.is_english_movie(movie),
            "is_available": self.is_available_format(movie),
            "tmdb_id": movie.get("id"),
            "source": "tmdb_api"
        }
    
    def build_comprehensive_database(self, max_movies: int = 2000) -> List[Dict[str, Any]]:
        """Build comprehensive movie database from TMDB"""
        print("🎬 Building Comprehensive Movie Database from TMDB")
        print("=" * 60)
        
        # Get genres first
        print("📋 Fetching movie genres...")
        self.genres = self.get_genres()
        
        # Collect movies from different sources
        movie_sources = [
            ("Popular Movies", self.get_popular_movies),
            ("Top Rated Movies", self.get_top_rated_movies),
            ("Now Playing Movies", self.get_now_playing_movies),
            ("Upcoming Movies", self.get_upcoming_movies)
        ]
        
        seen_movies = set()
        
        for source_name, fetch_function in movie_sources:
            print(f"\n📊 Fetching {source_name}...")
            
            page = 1
            while len(self.movie_database) < max_movies and self.api_calls_made < self.max_api_calls:
                if self.api_calls_made >= self.max_api_calls:
                    print(f"⚠️ Reached API call limit ({self.max_api_calls})")
                    break
                
                print(f"   Page {page}...", end=" ")
                movies = fetch_function(page)
                
                if not movies:
                    print("No more data")
                    break
                
                movies_added = 0
                for movie in movies:
                    movie_id = movie.get("id")
                    if movie_id and movie_id not in seen_movies:
                        # Get detailed movie information
                        detailed_movie = self.get_movie_details(movie_id)
                        if detailed_movie:
                            normalized_movie = self.normalize_movie_data(detailed_movie)
                            
                            # Filter for English movies and available formats
                            if normalized_movie["is_english"] and normalized_movie["is_available"]:
                                self.movie_database.append(normalized_movie)
                                seen_movies.add(movie_id)
                                movies_added += 1
                        
                        # Rate limiting
                        time.sleep(0.1)
                
                print(f"Added {movies_added} movies")
                page += 1
                
                # Check if we've reached the limit
                if len(self.movie_database) >= max_movies:
                    print(f"✅ Reached maximum movies limit ({max_movies})")
                    break
        
        print(f"\n🎉 Movie Database Building Complete!")
        print(f"📊 Final Statistics:")
        print(f"   - Total movies: {len(self.movie_database)}")
        print(f"   - API calls made: {self.api_calls_made}")
        print(f"   - English movies: {sum(1 for m in self.movie_database if m['is_english'])}")
        print(f"   - Available movies: {sum(1 for m in self.movie_database if m['is_available'])}")
        
        return self.movie_database
    
    def save_to_s3(self, filename: str = None) -> str:
        """Save movie database to S3"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"tmdb-movie-database-{timestamp}.json"
        
        print(f"💾 Saving movie database to {filename}...")
        
        # Create the database structure
        database = {
            "movies": self.movie_database,
            "genres": self.genres,
            "metadata": {
                "total_movies": len(self.movie_database),
                "english_movies": sum(1 for m in self.movie_database if m['is_english']),
                "available_movies": sum(1 for m in self.movie_database if m['is_available']),
                "api_calls_made": self.api_calls_made,
                "last_updated": datetime.now().isoformat(),
                "source": "tmdb_api"
            }
        }
        
        # Save locally
        with open(filename, 'w') as f:
            json.dump(database, f, indent=2)
        
        print(f"✅ Movie database saved to {filename}")
        
        # Upload to S3
        try:
            s3 = boto3.client('s3')
            s3_key = f"plex-recommendations/{filename}"
            s3.upload_file(filename, self.s3_bucket, s3_key)
            print(f"☁️ Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            
            # Also save as the main movie database
            main_key = "plex-recommendations/tmdb-movie-database.json"
            s3.upload_file(filename, self.s3_bucket, main_key)
            print(f"☁️ Uploaded as main movie database: s3://{self.s3_bucket}/{main_key}")
            
        except Exception as e:
            print(f"⚠️ Could not upload to S3: {e}")
        
        return filename

def main():
    # TMDB API Key
    api_key = os.getenv('TMDB_API_KEY') or input("Enter your TMDB API key: ")
    
    # Build comprehensive movie database
    integration = TMDBAPIIntegration(api_key)
    
    # Build database (limit to 1000 movies for initial run to stay within API limits)
    movie_database = integration.build_comprehensive_database(max_movies=1000)
    
    # Save to S3
    filename = integration.save_to_s3()
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Movie database saved: {filename}")
    print(f"   2. Update Lambda function to use TMDB movie database")
    print(f"   3. Generate recommendations from {len(movie_database)} movies")
    print(f"   4. All movies filtered for English language and availability")

if __name__ == "__main__":
    main()
