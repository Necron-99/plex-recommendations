#!/usr/bin/env python3
"""
Lightweight ML Recommender for Plex Movies
Cost-effective machine learning that runs in Lambda with minimal additional cost
"""

import json
import numpy as np
import pickle
import gzip
from typing import Dict, List, Any, Tuple
from datetime import datetime
import hashlib

# Lightweight ML imports (these will be added to Lambda package.json)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import StandardScaler
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ Scikit-learn not available, falling back to basic recommendations")

class LightweightMLRecommender:
    """
    Cost-effective ML recommender that runs in Lambda
    Uses content-based filtering and simple collaborative filtering
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.models = {}
        self.movie_features = {}
        self.user_profiles = {}
        self.cost_tracker = {
            "monthly_budget": 10.00,  # $10/month max
            "current_cost": 0.00,
            "fallback_mode": False
        }
        
        if self.ml_available:
            self.initialize_models()
    
    def initialize_models(self):
        """Initialize lightweight ML models"""
        try:
            # Content-based filtering model
            self.models['tfidf_vectorizer'] = TfidfVectorizer(
                max_features=500,  # Keep it lightweight
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Dimensionality reduction for collaborative filtering
            self.models['svd'] = TruncatedSVD(
                n_components=20,  # Small number for Lambda
                random_state=42
            )
            
            # Feature scaler
            self.models['scaler'] = StandardScaler()
            
            print("✅ Lightweight ML models initialized")
            
        except Exception as e:
            print(f"⚠️ Error initializing ML models: {e}")
            self.ml_available = False
    
    def extract_movie_features(self, movie_data: List[Dict]) -> Dict[str, Any]:
        """
        Extract features from movie data for ML processing
        Cost-optimized feature extraction
        """
        features = {}
        
        for movie in movie_data:
            movie_id = self._get_movie_id(movie)
            
            # Basic features
            feature_vector = {
                'year': int(movie.get('year', 0)) if movie.get('year') else 0,
                'rating': float(movie.get('rating', 0)) if movie.get('rating') else 0,
                'duration': int(movie.get('duration', 0)) if movie.get('duration') else 0,
                'view_count': int(movie.get('viewCount', 0)) if movie.get('viewCount') else 0
            }
            
            # Text features for content-based filtering
            text_content = []
            if movie.get('summary'):
                text_content.append(movie['summary'])
            if movie.get('title'):
                text_content.append(movie['title'])
            if movie.get('genres') and isinstance(movie['genres'], list):
                text_content.extend(movie['genres'])
            
            feature_vector['text_content'] = ' '.join(text_content)
            
            # Genre features
            if movie.get('genres') and isinstance(movie['genres'], list):
                feature_vector['genres'] = movie['genres']
            else:
                feature_vector['genres'] = []
            
            # TMDB metadata features (if available)
            if movie.get('tmdb_metadata'):
                tmdb = movie['tmdb_metadata']
                feature_vector['tmdb_rating'] = tmdb.get('vote_average', 0)
                feature_vector['tmdb_popularity'] = tmdb.get('popularity', 0)
                feature_vector['tmdb_vote_count'] = tmdb.get('vote_count', 0)
                
                # Cast and crew features
                if tmdb.get('cast'):
                    feature_vector['cast_count'] = len(tmdb['cast'])
                    feature_vector['top_cast'] = [actor['name'] for actor in tmdb['cast'][:3]]
                else:
                    feature_vector['cast_count'] = 0
                    feature_vector['top_cast'] = []
                
                if tmdb.get('crew'):
                    directors = [crew['name'] for crew in tmdb['crew'] if crew.get('job') == 'Director']
                    feature_vector['directors'] = directors
                else:
                    feature_vector['directors'] = []
            else:
                feature_vector['tmdb_rating'] = 0
                feature_vector['tmdb_popularity'] = 0
                feature_vector['tmdb_vote_count'] = 0
                feature_vector['cast_count'] = 0
                feature_vector['top_cast'] = []
                feature_vector['directors'] = []
            
            features[movie_id] = feature_vector
        
        return features
    
    def train_content_model(self, movie_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Train content-based filtering model
        Uses TF-IDF and cosine similarity for movie recommendations
        """
        if not self.ml_available:
            return {"status": "ml_not_available"}
        
        try:
            # Prepare text data
            movie_ids = list(movie_features.keys())
            text_data = [movie_features[movie_id]['text_content'] for movie_id in movie_ids]
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.models['tfidf_vectorizer'].fit_transform(text_data)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Store results
            content_model = {
                'movie_ids': movie_ids,
                'similarity_matrix': similarity_matrix,
                'tfidf_matrix': tfidf_matrix.toarray(),
                'trained_at': datetime.now().isoformat()
            }
            
            print(f"✅ Content model trained on {len(movie_ids)} movies")
            return content_model
            
        except Exception as e:
            print(f"❌ Error training content model: {e}")
            return {"status": "error", "message": str(e)}
    
    def train_collaborative_model(self, watch_history: List[Dict]) -> Dict[str, Any]:
        """
        Train simple collaborative filtering model
        Uses user-item matrix and SVD for recommendations
        """
        if not self.ml_available:
            return {"status": "ml_not_available"}
        
        try:
            # Build user-item matrix (simplified for single user)
            # In a real multi-user system, this would be more complex
            user_ratings = {}
            movie_ids = set()
            
            for item in watch_history:
                movie_id = self._get_movie_id(item)
                movie_ids.add(movie_id)
                
                # Use view count and rating as implicit feedback
                rating = float(item.get('rating', 0)) if item.get('rating') else 0
                view_count = int(item.get('viewCount', 0)) if item.get('viewCount') else 0
                
                # Combine rating and view count for user preference
                user_ratings[movie_id] = rating + (view_count * 0.5)
            
            # Create user-item matrix (1 user, multiple items)
            movie_ids = list(movie_ids)
            user_item_matrix = np.array([[user_ratings.get(movie_id, 0) for movie_id in movie_ids]])
            
            # Apply SVD for dimensionality reduction
            if user_item_matrix.shape[1] > 1:  # Need at least 2 items
                svd_matrix = self.models['svd'].fit_transform(user_item_matrix)
                
                collaborative_model = {
                    'movie_ids': movie_ids,
                    'user_ratings': user_ratings,
                    'svd_matrix': svd_matrix,
                    'trained_at': datetime.now().isoformat()
                }
                
                print(f"✅ Collaborative model trained on {len(movie_ids)} movies")
                return collaborative_model
            else:
                return {"status": "insufficient_data", "message": "Need at least 2 movies for collaborative filtering"}
                
        except Exception as e:
            print(f"❌ Error training collaborative model: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_content_recommendations(self, movie_features: Dict[str, Any], 
                                  content_model: Dict[str, Any], 
                                  target_movie_id: str, 
                                  n_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Get content-based recommendations using TF-IDF similarity
        """
        if not self.ml_available or content_model.get("status") != "success":
            return []
        
        try:
            movie_ids = content_model['movie_ids']
            similarity_matrix = content_model['similarity_matrix']
            
            if target_movie_id not in movie_ids:
                return []
            
            # Find similar movies
            target_idx = movie_ids.index(target_movie_id)
            similarities = similarity_matrix[target_idx]
            
            # Get top similar movies (excluding the target itself)
            similar_indices = np.argsort(similarities)[::-1][1:n_recommendations+1]
            
            recommendations = []
            for idx in similar_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    recommendations.append({
                        'movie_id': movie_ids[idx],
                        'similarity_score': float(similarities[idx]),
                        'type': 'content_based'
                    })
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error getting content recommendations: {e}")
            return []
    
    def get_collaborative_recommendations(self, collaborative_model: Dict[str, Any], 
                                        n_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Get collaborative filtering recommendations
        """
        if not self.ml_available or collaborative_model.get("status") != "success":
            return []
        
        try:
            user_ratings = collaborative_model['user_ratings']
            movie_ids = collaborative_model['movie_ids']
            
            # Find movies with high user ratings that could be recommended
            # In a real system, this would use the SVD matrix for predictions
            recommendations = []
            
            for movie_id, rating in user_ratings.items():
                if rating > 0:  # User has interacted with this movie
                    recommendations.append({
                        'movie_id': movie_id,
                        'user_rating': rating,
                        'type': 'collaborative'
                    })
            
            # Sort by rating and return top recommendations
            recommendations.sort(key=lambda x: x['user_rating'], reverse=True)
            return recommendations[:n_recommendations]
            
        except Exception as e:
            print(f"❌ Error getting collaborative recommendations: {e}")
            return []
    
    def get_hybrid_recommendations(self, movie_features: Dict[str, Any], 
                                 watch_history: List[Dict],
                                 n_recommendations: int = 10) -> Dict[str, Any]:
        """
        Get hybrid recommendations combining content-based and collaborative filtering
        This is the main method that will be called from the Lambda function
        """
        if not self.ml_available:
            return {
                "status": "ml_not_available",
                "message": "Falling back to basic recommendations",
                "recommendations": []
            }
        
        try:
            # Check cost budget
            if self.cost_tracker['fallback_mode']:
                return {
                    "status": "fallback_mode",
                    "message": "Using fallback mode to control costs",
                    "recommendations": []
                }
            
            # Train models
            content_model = self.train_content_model(movie_features)
            collaborative_model = self.train_collaborative_model(watch_history)
            
            # Get recommendations from both approaches
            content_recs = []
            collaborative_recs = []
            
            if content_model.get("status") == "success":
                # Get content recommendations for top-rated movies
                top_movies = sorted(watch_history, 
                                  key=lambda x: float(x.get('rating', 0)), 
                                  reverse=True)[:3]
                
                for movie in top_movies:
                    movie_id = self._get_movie_id(movie)
                    recs = self.get_content_recommendations(movie_features, content_model, movie_id, 3)
                    content_recs.extend(recs)
            
            if collaborative_model.get("status") == "success":
                collaborative_recs = self.get_collaborative_recommendations(collaborative_model, 5)
            
            # Combine and deduplicate recommendations
            all_recommendations = content_recs + collaborative_recs
            unique_recommendations = {}
            
            for rec in all_recommendations:
                movie_id = rec['movie_id']
                if movie_id not in unique_recommendations:
                    unique_recommendations[movie_id] = rec
                else:
                    # Combine scores if movie appears in both approaches
                    existing = unique_recommendations[movie_id]
                    if 'similarity_score' in rec and 'similarity_score' in existing:
                        existing['similarity_score'] = max(existing['similarity_score'], rec['similarity_score'])
                    existing['type'] = 'hybrid'
            
            # Sort by score and return top recommendations
            final_recommendations = list(unique_recommendations.values())
            final_recommendations.sort(key=lambda x: x.get('similarity_score', x.get('user_rating', 0)), reverse=True)
            
            return {
                "status": "success",
                "message": f"Generated {len(final_recommendations)} ML recommendations",
                "recommendations": final_recommendations[:n_recommendations],
                "model_info": {
                    "content_model_trained": content_model.get("status") == "success",
                    "collaborative_model_trained": collaborative_model.get("status") == "success",
                    "total_movies_analyzed": len(movie_features),
                    "ml_available": self.ml_available
                }
            }
            
        except Exception as e:
            print(f"❌ Error in hybrid recommendations: {e}")
            return {
                "status": "error",
                "message": str(e),
                "recommendations": []
            }
    
    def _get_movie_id(self, movie: Dict[str, Any]) -> str:
        """Generate a unique ID for a movie"""
        title = movie.get('title', 'Unknown')
        year = movie.get('year', 'Unknown')
        return hashlib.md5(f"{title}_{year}".encode()).hexdigest()[:12]
    
    def save_models(self, s3_client, bucket_name: str) -> Dict[str, Any]:
        """
        Save trained models to S3 for persistence
        Cost-optimized model storage
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            # Compress and save models
            model_data = {
                'models': self.models,
                'movie_features': self.movie_features,
                'user_profiles': self.user_profiles,
                'saved_at': timestamp
            }
            
            # Compress model data
            compressed_data = gzip.compress(json.dumps(model_data, default=str).encode())
            
            # Save to S3
            key = f"ml-models/lightweight-ml-{timestamp}.pkl.gz"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=compressed_data,
                ContentType='application/gzip',
                StorageClass='INTELLIGENT_TIERING'  # Cost optimization
            )
            
            print(f"✅ ML models saved to S3: {key}")
            return {"status": "success", "s3_key": key}
            
        except Exception as e:
            print(f"❌ Error saving models: {e}")
            return {"status": "error", "message": str(e)}
    
    def load_models(self, s3_client, bucket_name: str, model_key: str = None) -> Dict[str, Any]:
        """
        Load trained models from S3
        """
        try:
            if not model_key:
                # Try to find the latest model
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix="ml-models/lightweight-ml-"
                )
                
                if 'Contents' not in response:
                    return {"status": "no_models_found"}
                
                # Get the latest model
                latest_model = max(response['Contents'], key=lambda x: x['LastModified'])
                model_key = latest_model['Key']
            
            # Download and decompress model
            response = s3_client.get_object(Bucket=bucket_name, Key=model_key)
            compressed_data = response['Body'].read()
            model_data = json.loads(gzip.decompress(compressed_data).decode())
            
            # Restore models
            self.models = model_data.get('models', {})
            self.movie_features = model_data.get('movie_features', {})
            self.user_profiles = model_data.get('user_profiles', {})
            
            print(f"✅ ML models loaded from S3: {model_key}")
            return {"status": "success", "model_key": model_key}
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return {"status": "error", "message": str(e)}

# Cost monitoring and fallback functions
def check_ml_budget(current_cost: float, monthly_budget: float = 10.00) -> Dict[str, Any]:
    """Check if ML operations are within budget"""
    if current_cost > monthly_budget:
        return {
            "within_budget": False,
            "fallback_mode": True,
            "message": "Monthly budget exceeded, using fallback mode"
        }
    else:
        return {
            "within_budget": True,
            "fallback_mode": False,
            "remaining_budget": monthly_budget - current_cost
        }

def estimate_ml_cost(operation: str, data_size: int) -> float:
    """Estimate cost of ML operations"""
    cost_per_operation = {
        "content_training": 0.001,  # $0.001 per movie
        "collaborative_training": 0.002,  # $0.002 per user interaction
        "recommendation": 0.0001,  # $0.0001 per recommendation
        "model_storage": 0.0001  # $0.0001 per MB per month
    }
    
    base_cost = cost_per_operation.get(operation, 0.001)
    return base_cost * (data_size / 100)  # Scale with data size

# Example usage and testing
if __name__ == "__main__":
    # Test the lightweight ML recommender
    print("🧪 Testing Lightweight ML Recommender")
    print("=" * 50)
    
    # Create sample data
    sample_movies = [
        {
            "title": "The Matrix",
            "year": "1999",
            "rating": "8.7",
            "summary": "A computer hacker learns about the true nature of reality",
            "genres": ["Action", "Sci-Fi"],
            "tmdb_metadata": {
                "vote_average": 8.2,
                "popularity": 85.5,
                "cast": [{"name": "Keanu Reeves"}, {"name": "Laurence Fishburne"}],
                "crew": [{"name": "Lana Wachowski", "job": "Director"}]
            }
        },
        {
            "title": "Inception",
            "year": "2010",
            "rating": "8.8",
            "summary": "A thief who steals corporate secrets through dream-sharing technology",
            "genres": ["Action", "Sci-Fi", "Thriller"],
            "tmdb_metadata": {
                "vote_average": 8.3,
                "popularity": 92.1,
                "cast": [{"name": "Leonardo DiCaprio"}, {"name": "Marion Cotillard"}],
                "crew": [{"name": "Christopher Nolan", "job": "Director"}]
            }
        }
    ]
    
    # Initialize recommender
    recommender = LightweightMLRecommender()
    
    if recommender.ml_available:
        print("✅ ML models available")
        
        # Extract features
        features = recommender.extract_movie_features(sample_movies)
        print(f"✅ Extracted features for {len(features)} movies")
        
        # Get recommendations
        recommendations = recommender.get_hybrid_recommendations(features, sample_movies)
        print(f"✅ Generated {len(recommendations.get('recommendations', []))} recommendations")
        
        # Print results
        print("\n📊 ML Recommendation Results:")
        for rec in recommendations.get('recommendations', []):
            print(f"   - Movie ID: {rec['movie_id']}")
            print(f"     Type: {rec['type']}")
            if 'similarity_score' in rec:
                print(f"     Similarity: {rec['similarity_score']:.3f}")
            if 'user_rating' in rec:
                print(f"     User Rating: {rec['user_rating']:.1f}")
            print()
    else:
        print("⚠️ ML not available, would fall back to basic recommendations")
    
    print("🎯 Lightweight ML Recommender test completed!")
