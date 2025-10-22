#!/usr/bin/env python3
"""
TMDB Movie Pool Builder - Creates comprehensive movie recommendation pool
Uses TMDB API to build a database of all movies for recommendations
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import boto3

class TMDBMoviePoolBuilder:
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        self.s3_bucket = "plex-recommendations-c7c49ce4"
        
        # Movie pool data
        self.movie_pool = {
            "movies": [],
            "genres": {},
            "languages": {},
            "decades": {},
            "ratings": {},
            "metadata": {
                "total_movies": 0,
                "english_movies": 0,
                "available_formats": 0,
                "last_updated": datetime.now().isoformat(),
                "api_calls_made": 0
            }
        }
        
    def get_popular_movies(self, page: int = 1) -> Dict[str, Any]:
        """Get popular movies from TMDB"""
        url = f"{self.base_url}/movie/popular"
        params = {
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            self.movie_pool["metadata"]["api_calls_made"] += 1
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching popular movies page {page}: {e}")
            return {}
    
    def get_top_rated_movies(self, page: int = 1) -> Dict[str, Any]:
        """Get top rated movies from TMDB"""
        url = f"{self.base_url}/movie/top_rated"
        params = {
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            self.movie_pool["metadata"]["api_calls_made"] += 1
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching top rated movies page {page}: {e}")
            return {}
    
    def get_now_playing_movies(self, page: int = 1) -> Dict[str, Any]:
        """Get now playing movies from TMDB"""
        url = f"{self.base_url}/movie/now_playing"
        params = {
            "language": "en-US",
            "page": page,
            "region": "US"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            self.movie_pool["metadata"]["api_calls_made"] += 1
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching now playing movies page {page}: {e}")
            return {}
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific movie"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "language": "en-US",
            "append_to_response": "videos,credits,release_dates"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            self.movie_pool["metadata"]["api_calls_made"] += 1
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching movie details for ID {movie_id}: {e}")
            return {}
    
    def get_genres(self) -> Dict[str, Any]:
        """Get movie genres from TMDB"""
        url = f"{self.base_url}/genre/movie/list"
        params = {"language": "en-US"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            self.movie_pool["metadata"]["api_calls_made"] += 1
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching genres: {e}")
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
        genres = [genre.get("name", "") for genre in movie.get("genres", [])]
        
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
            "source": "tmdb_pool"
        }
    
    def build_movie_pool(self, max_pages: int = 50, max_movies: int = 10000) -> Dict[str, Any]:
        """Build comprehensive movie pool from TMDB"""
        print("🎬 Building Comprehensive Movie Pool from TMDB")
        print("=" * 60)
        
        # Get genres first
        print("📋 Fetching movie genres...")
        genres_data = self.get_genres()
        if genres_data and "genres" in genres_data:
            for genre in genres_data["genres"]:
                self.movie_pool["genres"][genre["id"]] = genre["name"]
            print(f"✅ Loaded {len(self.movie_pool['genres'])} genres")
        
        # Collect movies from different sources
        movie_sources = [
            ("Popular Movies", self.get_popular_movies),
            ("Top Rated Movies", self.get_top_rated_movies),
            ("Now Playing Movies", self.get_now_playing_movies)
        ]
        
        seen_movies = set()
        
        for source_name, fetch_function in movie_sources:
            print(f"\n📊 Fetching {source_name}...")
            
            for page in range(1, max_pages + 1):
                if len(self.movie_pool["movies"]) >= max_movies:
                    print(f"✅ Reached maximum movies limit ({max_movies})")
                    break
                
                print(f"   Page {page}...", end=" ")
                data = fetch_function(page)
                
                if not data or "results" not in data:
                    print("No more data")
                    break
                
                movies_added = 0
                for movie in data["results"]:
                    movie_id = movie.get("id")
                    if movie_id and movie_id not in seen_movies:
                        # Get detailed movie information
                        detailed_movie = self.get_movie_details(movie_id)
                        if detailed_movie:
                            normalized_movie = self.normalize_movie_data(detailed_movie)
                            
                            # Filter for English movies and available formats
                            if normalized_movie["is_english"] and normalized_movie["is_available"]:
                                self.movie_pool["movies"].append(normalized_movie)
                                seen_movies.add(movie_id)
                                movies_added += 1
                                
                                # Update statistics
                                if normalized_movie["is_english"]:
                                    self.movie_pool["metadata"]["english_movies"] += 1
                                if normalized_movie["is_available"]:
                                    self.movie_pool["metadata"]["available_formats"] += 1
                        
                        # Rate limiting
                        time.sleep(0.1)
                
                print(f"Added {movies_added} movies")
                
                # Check if we've reached the end
                if page >= data.get("total_pages", 1):
                    break
        
        # Update final statistics
        self.movie_pool["metadata"]["total_movies"] = len(self.movie_pool["movies"])
        
        print(f"\n🎉 Movie Pool Building Complete!")
        print(f"📊 Final Statistics:")
        print(f"   - Total movies: {self.movie_pool['metadata']['total_movies']}")
        print(f"   - English movies: {self.movie_pool['metadata']['english_movies']}")
        print(f"   - Available formats: {self.movie_pool['metadata']['available_formats']}")
        print(f"   - API calls made: {self.movie_pool['metadata']['api_calls_made']}")
        
        return self.movie_pool
    
    def save_movie_pool(self, filename: str = None) -> str:
        """Save movie pool to file and S3"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"tmdb-movie-pool-{timestamp}.json"
        
        print(f"💾 Saving movie pool to {filename}...")
        
        with open(filename, 'w') as f:
            json.dump(self.movie_pool, f, indent=2)
        
        print(f"✅ Movie pool saved to {filename}")
        
        # Upload to S3
        try:
            s3 = boto3.client('s3')
            s3_key = f"plex-recommendations/{filename}"
            s3.upload_file(filename, self.s3_bucket, s3_key)
            print(f"☁️ Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            
            # Also save as the main movie pool
            main_key = "plex-recommendations/tmdb-movie-pool.json"
            s3.upload_file(filename, self.s3_bucket, main_key)
            print(f"☁️ Uploaded as main movie pool: s3://{self.s3_bucket}/{main_key}")
            
        except Exception as e:
            print(f"⚠️ Could not upload to S3: {e}")
        
        return filename
    
    def analyze_movie_pool(self) -> Dict[str, Any]:
        """Analyze the movie pool for insights"""
        print("\n📊 Analyzing Movie Pool...")
        
        # Genre analysis
        genre_counts = {}
        decade_counts = {}
        rating_ranges = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
        
        for movie in self.movie_pool["movies"]:
            # Genre analysis
            for genre in movie.get("genres", []):
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Decade analysis
            year = movie.get("year", "")
            if year and year.isdigit():
                decade = f"{year[:3]}0s"
                decade_counts[decade] = decade_counts.get(decade, 0) + 1
            
            # Rating analysis
            rating = movie.get("rating", 0)
            if rating < 2:
                rating_ranges["0-2"] += 1
            elif rating < 4:
                rating_ranges["2-4"] += 1
            elif rating < 6:
                rating_ranges["4-6"] += 1
            elif rating < 8:
                rating_ranges["6-8"] += 1
            else:
                rating_ranges["8-10"] += 1
        
        analysis = {
            "total_movies": len(self.movie_pool["movies"]),
            "top_genres": sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_decades": sorted(decade_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "rating_distribution": rating_ranges,
            "average_rating": sum(movie.get("rating", 0) for movie in self.movie_pool["movies"]) / len(self.movie_pool["movies"]) if self.movie_pool["movies"] else 0
        }
        
        print(f"📈 Analysis Results:")
        print(f"   - Average rating: {analysis['average_rating']:.2f}")
        print(f"   - Top genre: {analysis['top_genres'][0][0] if analysis['top_genres'] else 'N/A'}")
        print(f"   - Top decade: {analysis['top_decades'][0][0] if analysis['top_decades'] else 'N/A'}")
        
        return analysis

def main():
    # TMDB API Credentials
    api_key = os.getenv('TMDB_API_KEY') or input("Enter your TMDB API key: ")
    access_token = os.getenv('TMDB_ACCESS_TOKEN') or input("Enter your TMDB access token: ")
    
    # Build movie pool
    builder = TMDBMoviePoolBuilder(api_key, access_token)
    
    # Build comprehensive movie pool (limit to 5000 movies for initial run)
    movie_pool = builder.build_movie_pool(max_pages=20, max_movies=5000)
    
    # Analyze the pool
    analysis = builder.analyze_movie_pool()
    
    # Save to file and S3
    filename = builder.save_movie_pool()
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Movie pool saved: {filename}")
    print(f"   2. Update Lambda function to use TMDB movie pool")
    print(f"   3. Generate recommendations from comprehensive movie database")
    print(f"   4. Filter recommendations by English language and availability")

if __name__ == "__main__":
    main()
