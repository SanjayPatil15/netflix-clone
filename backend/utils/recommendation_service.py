"""
Enhanced Recommendation Service for CineSense
Combines database queries with existing ML models for better recommendations
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy import func, and_
from backend.database import get_db, Movie, Rating, User, Watchlist
import random


class RecommendationService:
    """Enhanced recommendation service using database and ML models"""
    
    def __init__(self, hybrid_model=None, content_model=None, demo_model=None):
        """
        Initialize with existing ML models for hybrid recommendations
        
        Args:
            hybrid_model: Existing HybridRecommender instance
            content_model: Existing ContentBasedRecommender instance
            demo_model: Existing DemographicRecommender instance
        """
        self.hybrid_model = hybrid_model
        self.content_model = content_model
        self.demo_model = demo_model
    
    def get_personalized_recommendations(
        self,
        user_email: str,
        limit: int = 20,
        exclude_watched: bool = True
    ) -> List[Dict]:
        """
        Get personalized recommendations combining multiple strategies
        
        Args:
            user_email: User's email
            limit: Number of recommendations
            exclude_watched: Exclude movies user has already rated
        
        Returns:
            List of recommended movies with scores
        """
        with get_db() as db:
            user = db.query(User).filter_by(email=user_email).first()
            if not user:
                return self._get_popular_movies(limit)
            
            # Get user's rated movies
            user_ratings = db.query(Rating).filter_by(user_id=user.id).all()
            
            if not user_ratings:
                # New user - use demographic and genre preferences
                return self._get_cold_start_recommendations(user, limit)
            
            # Combine multiple recommendation strategies
            recommendations = {}
            
            # 1. Collaborative filtering (similar users)
            collab_recs = self._get_collaborative_recommendations(user, limit * 2)
            for movie, score in collab_recs:
                recommendations[movie['id']] = {
                    'movie': movie,
                    'score': score * 0.4,  # Weight: 40%
                    'reason': 'Users like you enjoyed this'
                }
            
            # 2. Content-based (similar to liked movies)
            content_recs = self._get_content_based_recommendations(user, limit * 2)
            for movie, score in content_recs:
                if movie['id'] in recommendations:
                    recommendations[movie['id']]['score'] += score * 0.3
                else:
                    recommendations[movie['id']] = {
                        'movie': movie,
                        'score': score * 0.3,  # Weight: 30%
                        'reason': 'Similar to movies you liked'
                    }
            
            # 3. Genre-based (user's preferred genres)
            genre_recs = self._get_genre_recommendations(user, limit * 2)
            for movie, score in genre_recs:
                if movie['id'] in recommendations:
                    recommendations[movie['id']]['score'] += score * 0.3
                else:
                    recommendations[movie['id']] = {
                        'movie': movie,
                        'score': score * 0.3,  # Weight: 30%
                        'reason': f"Popular {user.preferred_genre} movie"
                    }
            
            # Exclude already rated movies if requested
            if exclude_watched:
                rated_movie_ids = {r.movie_id for r in user_ratings}
                recommendations = {
                    k: v for k, v in recommendations.items()
                    if v['movie']['id'] not in rated_movie_ids
                }
            
            # Sort by combined score
            sorted_recs = sorted(
                recommendations.values(),
                key=lambda x: x['score'],
                reverse=True
            )
            
            return [
                {
                    **rec['movie'],
                    'recommendation_score': round(rec['score'], 3),
                    'reason': rec['reason']
                }
                for rec in sorted_recs[:limit]
            ]
    
    def _get_collaborative_recommendations(
        self,
        user: User,
        limit: int
    ) -> List[Tuple[Dict, float]]:
        """Get recommendations based on similar users' ratings"""
        with get_db() as db:
            # Find users with similar rating patterns
            user_ratings = db.query(Rating).filter_by(user_id=user.id).all()
            if not user_ratings:
                return []
            
            # Get movies user rated highly
            liked_movie_ids = [r.movie_id for r in user_ratings if r.rating >= 4.0]
            
            if not liked_movie_ids:
                return []
            
            # Find other users who also liked these movies
            similar_users = db.query(Rating.user_id, func.count(Rating.id).label('overlap'))\
                .filter(
                    Rating.movie_id.in_(liked_movie_ids),
                    Rating.rating >= 4.0,
                    Rating.user_id != user.id
                )\
                .group_by(Rating.user_id)\
                .order_by(func.count(Rating.id).desc())\
                .limit(10)\
                .all()
            
            if not similar_users:
                return []
            
            similar_user_ids = [u.user_id for u in similar_users]
            
            # Get movies these similar users liked
            rated_movie_ids = {r.movie_id for r in user_ratings}
            
            recommended_movies = db.query(
                Movie,
                func.count(Rating.id).label('recommendation_count'),
                func.avg(Rating.rating).label('avg_rating')
            )\
                .join(Rating)\
                .filter(
                    Rating.user_id.in_(similar_user_ids),
                    Rating.rating >= 4.0,
                    ~Movie.id.in_(rated_movie_ids)
                )\
                .group_by(Movie.id)\
                .order_by(
                    func.count(Rating.id).desc(),
                    func.avg(Rating.rating).desc()
                )\
                .limit(limit)\
                .all()
            
            return [
                (movie.to_dict(), min(1.0, (count / len(similar_user_ids)) * (avg_rating / 5.0)))
                for movie, count, avg_rating in recommended_movies
            ]
    
    def _get_content_based_recommendations(
        self,
        user: User,
        limit: int
    ) -> List[Tuple[Dict, float]]:
        """Get recommendations based on content similarity to liked movies"""
        with get_db() as db:
            # Get user's highly rated movies
            high_ratings = db.query(Rating)\
                .filter(Rating.user_id == user.id, Rating.rating >= 4.0)\
                .join(Movie)\
                .order_by(Rating.rating.desc())\
                .limit(5)\
                .all()
            
            if not high_ratings:
                return []
            
            # Get genres from liked movies
            liked_genres = set()
            for rating in high_ratings:
                if rating.movie.genres:
                    liked_genres.update(rating.movie.genres.split('|'))
            
            # Find movies with similar genres
            rated_movie_ids = {r.movie_id for r in db.query(Rating).filter_by(user_id=user.id).all()}
            
            similar_movies = []
            for genre in liked_genres:
                movies = db.query(Movie)\
                    .filter(
                        Movie.genres.ilike(f'%{genre}%'),
                        ~Movie.id.in_(rated_movie_ids)
                    )\
                    .order_by(Movie.avg_rating.desc())\
                    .limit(limit)\
                    .all()
                similar_movies.extend(movies)
            
            # Remove duplicates and calculate scores
            seen = set()
            unique_movies = []
            for movie in similar_movies:
                if movie.id not in seen:
                    seen.add(movie.id)
                    # Score based on genre overlap and rating
                    movie_genres = set(movie.genres.split('|')) if movie.genres else set()
                    overlap = len(movie_genres & liked_genres)
                    score = (overlap / len(liked_genres)) * (movie.avg_rating / 5.0) if liked_genres else 0
                    unique_movies.append((movie.to_dict(), score))
            
            unique_movies.sort(key=lambda x: x[1], reverse=True)
            return unique_movies[:limit]
    
    def _get_genre_recommendations(
        self,
        user: User,
        limit: int
    ) -> List[Tuple[Dict, float]]:
        """Get top-rated movies from user's preferred genre"""
        if not user.preferred_genre:
            return []
        
        with get_db() as db:
            rated_movie_ids = {r.movie_id for r in db.query(Rating).filter_by(user_id=user.id).all()}
            
            movies = db.query(Movie)\
                .filter(
                    Movie.genres.ilike(f'%{user.preferred_genre}%'),
                    ~Movie.id.in_(rated_movie_ids),
                    Movie.rating_count >= 10
                )\
                .order_by(Movie.avg_rating.desc())\
                .limit(limit)\
                .all()
            
            return [(m.to_dict(), m.avg_rating / 5.0) for m in movies]
    
    def _get_cold_start_recommendations(
        self,
        user: User,
        limit: int
    ) -> List[Dict]:
        """Get recommendations for new users with no ratings"""
        with get_db() as db:
            # Use preferred genre if available
            if user.preferred_genre:
                movies = db.query(Movie)\
                    .filter(
                        Movie.genres.ilike(f'%{user.preferred_genre}%'),
                        Movie.rating_count >= 20
                    )\
                    .order_by(Movie.avg_rating.desc())\
                    .limit(limit)\
                    .all()
                
                return [
                    {
                        **m.to_dict(),
                        'reason': f'Popular {user.preferred_genre} movie',
                        'recommendation_score': m.avg_rating / 5.0
                    }
                    for m in movies
                ]
            
            # Otherwise, return popular movies
            return self._get_popular_movies(limit)
    
    def _get_popular_movies(self, limit: int) -> List[Dict]:
        """Get popular movies based on ratings"""
        with get_db() as db:
            movies = db.query(Movie)\
                .filter(Movie.rating_count >= 20)\
                .order_by(
                    (Movie.avg_rating * func.log(Movie.rating_count + 1)).desc()
                )\
                .limit(limit)\
                .all()
            
            return [
                {
                    **m.to_dict(),
                    'reason': 'Popular movie',
                    'recommendation_score': (m.avg_rating / 5.0) * 0.8
                }
                for m in movies
            ]
    
    def get_similar_movies(
        self,
        movie_title: str,
        limit: int = 12
    ) -> List[Dict]:
        """
        Get movies similar to the given movie
        Uses genre overlap and content similarity
        """
        with get_db() as db:
            # Find the source movie
            source_movie = db.query(Movie).filter(
                func.lower(Movie.title) == movie_title.lower()
            ).first()
            
            if not source_movie:
                return []
            
            if not source_movie.genres:
                return []
            
            # Get source genres
            source_genres = set(source_movie.genres.split('|'))
            
            # Find similar movies
            all_movies = db.query(Movie)\
                .filter(Movie.id != source_movie.id)\
                .all()
            
            # Calculate similarity scores
            similar_movies = []
            for movie in all_movies:
                if not movie.genres:
                    continue
                
                movie_genres = set(movie.genres.split('|'))
                overlap = len(source_genres & movie_genres)
                
                if overlap > 0:
                    # Similarity score based on genre overlap and rating
                    similarity = (overlap / len(source_genres)) * 0.7 + (movie.avg_rating / 5.0) * 0.3
                    similar_movies.append((movie, similarity))
            
            # Sort by similarity
            similar_movies.sort(key=lambda x: x[1], reverse=True)
            
            return [
                {
                    **m.to_dict(),
                    'similarity_score': round(score, 3),
                    'reason': f'Similar to {source_movie.title}'
                }
                for m, score in similar_movies[:limit]
            ]
    
    def get_trending_movies(self, limit: int = 20) -> List[Dict]:
        """Get trending movies with high engagement"""
        with get_db() as db:
            movies = db.query(Movie)\
                .filter(Movie.rating_count > 10)\
                .order_by(
                    (Movie.avg_rating * func.log(Movie.rating_count + 1)).desc()
                )\
                .limit(limit)\
                .all()
            
            return [
                {
                    **m.to_dict(),
                    'reason': 'Trending now',
                    'trending_score': round((m.avg_rating / 5.0) * (1 + (m.rating_count / 1000)), 3)
                }
                for m in movies
            ]

