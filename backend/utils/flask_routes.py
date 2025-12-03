"""
Enhanced Flask Routes for CineSense with Database Integration
This module provides route handlers that can be integrated into app.py
"""

from flask import request, jsonify, flash, redirect, url_for, render_template
from utils.search_service import SearchService
from utils.recommendation_service import RecommendationService
from database import get_db, Movie, User, Rating, Watchlist
from utils.auth import load_session, get_user_by_email
from typing import Optional


class EnhancedRoutes:
    """Enhanced route handlers with database integration"""
    
    def __init__(self, app, recommendation_service: Optional[RecommendationService] = None):
        self.app = app
        self.rec_service = recommendation_service or RecommendationService()
    
    def register_routes(self):
        """Register all enhanced routes"""
        
        @self.app.route("/api/search")
        def api_search():
            """
            Advanced search API endpoint
            Query params:
                - q: search query
                - genres: comma-separated genres
                - year_min: minimum year
                - year_max: maximum year
                - min_rating: minimum rating
                - sort: sort order (relevance, rating, year, title)
                - limit: max results
            """
            query = request.args.get('q', '')
            genres = request.args.get('genres', '').split(',') if request.args.get('genres') else None
            year_min = int(request.args.get('year_min')) if request.args.get('year_min') else None
            year_max = int(request.args.get('year_max')) if request.args.get('year_max') else None
            min_rating = float(request.args.get('min_rating')) if request.args.get('min_rating') else None
            sort_by = request.args.get('sort', 'relevance')
            limit = int(request.args.get('limit', 50))
            
            user_email = load_session()
            
            results = SearchService.search_movies(
                query=query,
                genres=genres,
                year_min=year_min,
                year_max=year_max,
                min_rating=min_rating,
                sort_by=sort_by,
                limit=limit,
                user_email=user_email
            )
            
            return jsonify({
                'status': 'success',
                'count': len(results),
                'results': results
            })
        
        @self.app.route("/api/search/suggestions")
        def api_search_suggestions():
            """Get search suggestions for autocomplete"""
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            
            if not query or len(query) < 2:
                return jsonify([])
            
            suggestions = SearchService.get_search_suggestions(query, limit)
            return jsonify(suggestions)
        
        @self.app.route("/api/movies/trending")
        def api_trending_movies():
            """Get trending movies"""
            limit = int(request.args.get('limit', 20))
            movies = SearchService.get_trending_movies(limit)
            return jsonify({
                'status': 'success',
                'count': len(movies),
                'movies': movies
            })
        
        @self.app.route("/api/movies/top-rated")
        def api_top_rated():
            """Get top rated movies"""
            limit = int(request.args.get('limit', 50))
            min_ratings = int(request.args.get('min_ratings', 20))
            movies = SearchService.get_top_rated_movies(limit, min_ratings)
            return jsonify({
                'status': 'success',
                'count': len(movies),
                'movies': movies
            })
        
        @self.app.route("/api/movies/<int:movie_id>")
        def api_movie_details(movie_id):
            """Get detailed movie information"""
            movie = SearchService.get_movie_by_id(movie_id)
            if not movie:
                return jsonify({'status': 'error', 'message': 'Movie not found'}), 404
            
            # Get user's rating if logged in
            user_email = load_session()
            user_rating = None
            in_watchlist = False
            
            if user_email:
                with get_db() as db:
                    user = db.query(User).filter_by(email=user_email).first()
                    if user:
                        movie_obj = db.query(Movie).filter_by(movie_id=movie_id).first()
                        if movie_obj:
                            rating = db.query(Rating).filter_by(
                                user_id=user.id,
                                movie_id=movie_obj.id
                            ).first()
                            if rating:
                                user_rating = rating.rating
                            
                            watchlist_item = db.query(Watchlist).filter_by(
                                user_id=user.id,
                                movie_id=movie_obj.id
                            ).first()
                            in_watchlist = watchlist_item is not None
            
            return jsonify({
                'status': 'success',
                'movie': movie,
                'user_rating': user_rating,
                'in_watchlist': in_watchlist
            })
        
        @self.app.route("/api/movies/<path:title>/similar")
        def api_similar_movies(title):
            """Get similar movies"""
            limit = int(request.args.get('limit', 12))
            similar = self.rec_service.get_similar_movies(title, limit)
            return jsonify({
                'status': 'success',
                'count': len(similar),
                'movies': similar
            })
        
        @self.app.route("/api/recommendations/personalized")
        def api_personalized_recommendations():
            """Get personalized recommendations for logged-in user"""
            user_email = load_session()
            if not user_email:
                return jsonify({
                    'status': 'error',
                    'message': 'Login required'
                }), 401
            
            limit = int(request.args.get('limit', 20))
            exclude_watched = request.args.get('exclude_watched', 'true').lower() == 'true'
            
            recommendations = self.rec_service.get_personalized_recommendations(
                user_email=user_email,
                limit=limit,
                exclude_watched=exclude_watched
            )
            
            return jsonify({
                'status': 'success',
                'count': len(recommendations),
                'recommendations': recommendations
            })
        
        @self.app.route("/api/ratings", methods=['POST'])
        def api_add_rating():
            """Add or update a movie rating"""
            user_email = load_session()
            if not user_email:
                return jsonify({'status': 'error', 'message': 'Login required'}), 401
            
            data = request.get_json()
            movie_id = data.get('movie_id')
            rating_value = data.get('rating')
            
            if not movie_id or not rating_value:
                return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
            
            try:
                with get_db() as db:
                    user = db.query(User).filter_by(email=user_email).first()
                    movie = db.query(Movie).filter_by(movie_id=movie_id).first()
                    
                    if not user or not movie:
                        return jsonify({'status': 'error', 'message': 'User or movie not found'}), 404
                    
                    # Check if rating exists
                    existing_rating = db.query(Rating).filter_by(
                        user_id=user.id,
                        movie_id=movie.id
                    ).first()
                    
                    if existing_rating:
                        existing_rating.rating = float(rating_value)
                    else:
                        new_rating = Rating(
                            user_id=user.id,
                            movie_id=movie.id,
                            rating=float(rating_value)
                        )
                        db.add(new_rating)
                    
                    db.commit()
                    
                    # Update movie average rating
                    ratings = db.query(Rating).filter_by(movie_id=movie.id).all()
                    movie.rating_count = len(ratings)
                    movie.avg_rating = sum(r.rating for r in ratings) / len(ratings)
                    db.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': 'Rating saved',
                        'new_avg_rating': round(movie.avg_rating, 2)
                    })
            
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route("/api/watchlist", methods=['GET'])
        def api_get_watchlist():
            """Get user's watchlist"""
            user_email = load_session()
            if not user_email:
                return jsonify({'status': 'error', 'message': 'Login required'}), 401
            
            try:
                with get_db() as db:
                    user = db.query(User).filter_by(email=user_email).first()
                    if not user:
                        return jsonify({'status': 'error', 'message': 'User not found'}), 404
                    
                    watchlist_items = db.query(Watchlist)\
                        .filter_by(user_id=user.id)\
                        .join(Movie)\
                        .all()
                    
                    movies = [item.movie.to_dict() for item in watchlist_items]
                    
                    return jsonify({
                        'status': 'success',
                        'count': len(movies),
                        'movies': movies
                    })
            
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route("/api/watchlist/add", methods=['POST'])
        def api_add_to_watchlist():
            """Add movie to watchlist"""
            user_email = load_session()
            if not user_email:
                return jsonify({'status': 'error', 'message': 'Login required'}), 401
            
            data = request.get_json()
            movie_id = data.get('movie_id')
            
            if not movie_id:
                return jsonify({'status': 'error', 'message': 'Missing movie_id'}), 400
            
            try:
                with get_db() as db:
                    user = db.query(User).filter_by(email=user_email).first()
                    movie = db.query(Movie).filter_by(movie_id=movie_id).first()
                    
                    if not user or not movie:
                        return jsonify({'status': 'error', 'message': 'User or movie not found'}), 404
                    
                    # Check if already in watchlist
                    existing = db.query(Watchlist).filter_by(
                        user_id=user.id,
                        movie_id=movie.id
                    ).first()
                    
                    if existing:
                        return jsonify({
                            'status': 'info',
                            'message': 'Already in watchlist'
                        })
                    
                    watchlist_item = Watchlist(
                        user_id=user.id,
                        movie_id=movie.id
                    )
                    db.add(watchlist_item)
                    db.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'{movie.title} added to watchlist'
                    })
            
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route("/api/watchlist/remove", methods=['POST'])
        def api_remove_from_watchlist():
            """Remove movie from watchlist"""
            user_email = load_session()
            if not user_email:
                return jsonify({'status': 'error', 'message': 'Login required'}), 401
            
            data = request.get_json()
            movie_id = data.get('movie_id')
            
            if not movie_id:
                return jsonify({'status': 'error', 'message': 'Missing movie_id'}), 400
            
            try:
                with get_db() as db:
                    user = db.query(User).filter_by(email=user_email).first()
                    movie = db.query(Movie).filter_by(movie_id=movie_id).first()
                    
                    if not user or not movie:
                        return jsonify({'status': 'error', 'message': 'User or movie not found'}), 404
                    
                    watchlist_item = db.query(Watchlist).filter_by(
                        user_id=user.id,
                        movie_id=movie.id
                    ).first()
                    
                    if watchlist_item:
                        db.delete(watchlist_item)
                        db.commit()
                        return jsonify({
                            'status': 'success',
                            'message': f'{movie.title} removed from watchlist'
                        })
                    else:
                        return jsonify({
                            'status': 'info',
                            'message': 'Not in watchlist'
                        })
            
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

