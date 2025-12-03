"""
Advanced Search Service for CineSense
Provides powerful search with filters, fuzzy matching, and recommendations
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy import or_, and_, func
from backend.database import get_db, Movie, Rating, User, SearchHistory
from difflib import get_close_matches
import re


class SearchService:
    """Advanced search functionality with filters and fuzzy matching"""
    
    @staticmethod
    def search_movies(
        query: str,
        genres: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        min_rating: Optional[float] = None,
        sort_by: str = 'relevance',
        limit: int = 50,
        user_email: Optional[str] = None
    ) -> List[Dict]:
        """
        Advanced movie search with multiple filters
        
        Args:
            query: Search query string
            genres: List of genres to filter by
            year_min: Minimum year
            year_max: Maximum year
            min_rating: Minimum average rating
            sort_by: Sort order ('relevance', 'rating', 'year', 'title')
            limit: Maximum results to return
            user_email: User email for search history tracking
        
        Returns:
            List of movie dictionaries
        """
        with get_db() as db:
            # Base query
            q = db.query(Movie)
            
            # Text search (title matching)
            if query:
                query_lower = query.lower().strip()
                q = q.filter(
                    or_(
                        Movie.title.ilike(f'%{query_lower}%'),
                        Movie.summary.ilike(f'%{query_lower}%')
                    )
                )
            
            # Genre filter
            if genres:
                genre_filters = [Movie.genres.ilike(f'%{g}%') for g in genres]
                q = q.filter(or_(*genre_filters))
            
            # Year range filter
            if year_min:
                q = q.filter(Movie.year >= year_min)
            if year_max:
                q = q.filter(Movie.year <= year_max)
            
            # Rating filter
            if min_rating:
                q = q.filter(Movie.avg_rating >= min_rating)
            
            # Sorting
            if sort_by == 'rating':
                q = q.order_by(Movie.avg_rating.desc(), Movie.rating_count.desc())
            elif sort_by == 'year':
                q = q.order_by(Movie.year.desc())
            elif sort_by == 'title':
                q = q.order_by(Movie.title.asc())
            else:  # relevance (default)
                # Sort by rating count and average rating for relevance
                q = q.order_by(Movie.rating_count.desc(), Movie.avg_rating.desc())
            
            # Execute query
            movies = q.limit(limit).all()
            
            # Track search history
            if user_email and query:
                SearchService._track_search(db, user_email, query, len(movies))
            
            # Convert to dictionaries
            return [movie.to_dict() for movie in movies]
    
    @staticmethod
    def fuzzy_search(query: str, limit: int = 10) -> List[Dict]:
        """
        Fuzzy search for movie titles using difflib
        Useful for autocomplete and typo tolerance
        """
        with get_db() as db:
            # Get all movie titles
            all_movies = db.query(Movie).all()
            all_titles = {m.title.lower(): m for m in all_movies}
            
            # Find close matches
            query_lower = query.lower().strip()
            matches = get_close_matches(query_lower, all_titles.keys(), n=limit, cutoff=0.4)
            
            # Return matched movies
            return [all_titles[match].to_dict() for match in matches]
    
    @staticmethod
    def search_by_genre(genre: str, limit: int = 50, sort_by: str = 'rating') -> List[Dict]:
        """Search movies by genre with sorting"""
        return SearchService.search_movies(
            query='',
            genres=[genre],
            sort_by=sort_by,
            limit=limit
        )
    
    @staticmethod
    def get_trending_movies(limit: int = 20) -> List[Dict]:
        """Get trending movies based on rating count and average rating"""
        with get_db() as db:
            movies = db.query(Movie)\
                .filter(Movie.rating_count > 10)\
                .order_by(
                    (Movie.avg_rating * func.log(Movie.rating_count + 1)).desc()
                )\
                .limit(limit)\
                .all()
            
            return [movie.to_dict() for movie in movies]
    
    @staticmethod
    def get_top_rated_movies(limit: int = 50, min_ratings: int = 20) -> List[Dict]:
        """Get top rated movies with minimum rating threshold"""
        with get_db() as db:
            movies = db.query(Movie)\
                .filter(Movie.rating_count >= min_ratings)\
                .order_by(Movie.avg_rating.desc())\
                .limit(limit)\
                .all()
            
            return [movie.to_dict() for movie in movies]
    
    @staticmethod
    def get_recent_movies(limit: int = 50) -> List[Dict]:
        """Get recent movies sorted by year"""
        with get_db() as db:
            movies = db.query(Movie)\
                .filter(Movie.year.isnot(None))\
                .order_by(Movie.year.desc())\
                .limit(limit)\
                .all()
            
            return [movie.to_dict() for movie in movies]
    
    @staticmethod
    def get_movie_by_title(title: str, fuzzy: bool = True) -> Optional[Dict]:
        """
        Get a single movie by title
        
        Args:
            title: Movie title to search for
            fuzzy: Use fuzzy matching if exact match not found
        
        Returns:
            Movie dictionary or None
        """
        with get_db() as db:
            # Try exact match first (case-insensitive)
            movie = db.query(Movie).filter(
                func.lower(Movie.title) == title.lower()
            ).first()
            
            if movie:
                return movie.to_dict()
            
            # Try fuzzy match if enabled
            if fuzzy:
                results = SearchService.fuzzy_search(title, limit=1)
                return results[0] if results else None
            
            return None
    
    @staticmethod
    def get_movie_by_id(movie_id: int) -> Optional[Dict]:
        """Get movie by MovieLens ID"""
        with get_db() as db:
            movie = db.query(Movie).filter_by(movie_id=movie_id).first()
            return movie.to_dict() if movie else None
    
    @staticmethod
    def get_similar_movies(movie_title: str, limit: int = 12) -> List[Dict]:
        """
        Get similar movies based on genre overlap
        This is a simple implementation; can be enhanced with content-based filtering
        """
        with get_db() as db:
            # Get the source movie
            source_movie = db.query(Movie).filter(
                func.lower(Movie.title) == movie_title.lower()
            ).first()
            
            if not source_movie or not source_movie.genres:
                return []
            
            # Get genres
            source_genres = source_movie.genres.split('|')
            
            # Find movies with overlapping genres
            similar_movies = []
            for genre in source_genres:
                movies = db.query(Movie)\
                    .filter(
                        Movie.genres.ilike(f'%{genre}%'),
                        Movie.id != source_movie.id
                    )\
                    .order_by(Movie.avg_rating.desc())\
                    .limit(limit * 2)\
                    .all()
                similar_movies.extend(movies)
            
            # Remove duplicates and sort by rating
            seen = set()
            unique_movies = []
            for movie in similar_movies:
                if movie.id not in seen:
                    seen.add(movie.id)
                    unique_movies.append(movie)
            
            unique_movies.sort(key=lambda m: m.avg_rating, reverse=True)
            return [m.to_dict() for m in unique_movies[:limit]]
    
    @staticmethod
    def get_user_recommendations(user_email: str, limit: int = 20) -> List[Dict]:
        """
        Get personalized recommendations based on user's ratings and preferences
        """
        with get_db() as db:
            user = db.query(User).filter_by(email=user_email).first()
            if not user:
                return SearchService.get_trending_movies(limit)
            
            # Get user's highly rated movies
            high_ratings = db.query(Rating)\
                .filter(Rating.user_id == user.id, Rating.rating >= 4.0)\
                .join(Movie)\
                .all()
            
            if not high_ratings:
                # No ratings yet, use preferred genre
                if user.preferred_genre:
                    return SearchService.search_by_genre(user.preferred_genre, limit)
                return SearchService.get_trending_movies(limit)
            
            # Get genres from highly rated movies
            liked_genres = set()
            for rating in high_ratings:
                if rating.movie.genres:
                    liked_genres.update(rating.movie.genres.split('|'))
            
            # Get movies from liked genres that user hasn't rated
            rated_movie_ids = {r.movie_id for r in db.query(Rating).filter_by(user_id=user.id).all()}
            
            recommendations = []
            for genre in liked_genres:
                movies = db.query(Movie)\
                    .filter(
                        Movie.genres.ilike(f'%{genre}%'),
                        ~Movie.id.in_(rated_movie_ids)
                    )\
                    .order_by(Movie.avg_rating.desc())\
                    .limit(limit)\
                    .all()
                recommendations.extend(movies)
            
            # Remove duplicates and sort
            seen = set()
            unique_recs = []
            for movie in recommendations:
                if movie.id not in seen:
                    seen.add(movie.id)
                    unique_recs.append(movie)
            
            unique_recs.sort(key=lambda m: m.avg_rating, reverse=True)
            return [m.to_dict() for m in unique_recs[:limit]]
    
    @staticmethod
    def _track_search(db, user_email: str, query: str, results_count: int):
        """Track search history for analytics"""
        try:
            user = db.query(User).filter_by(email=user_email).first()
            if user:
                search_record = SearchHistory(
                    user_id=user.id,
                    query=query,
                    results_count=results_count
                )
                db.add(search_record)
                db.commit()
        except Exception as e:
            print(f"⚠️ Error tracking search: {e}")
    
    @staticmethod
    def get_search_suggestions(query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query
        Returns list of movie titles
        """
        if not query or len(query) < 2:
            return []
        
        with get_db() as db:
            movies = db.query(Movie.title)\
                .filter(Movie.title.ilike(f'%{query}%'))\
                .order_by(Movie.rating_count.desc())\
                .limit(limit)\
                .all()
            
            return [m.title for m in movies]

