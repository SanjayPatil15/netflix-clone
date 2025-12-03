"""
Test script for CineSense database and search functionality
Run this after setup to verify everything is working
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db, Movie, User, Rating, Watchlist
from backend.utils.search_service import SearchService
from backend.utils.recommendation_service import RecommendationService


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("🔌 Testing Database Connection")
    print("="*60)
    
    try:
        with get_db() as db:
            count = db.query(Movie).count()
            print(f"✅ Database connected successfully")
            print(f"   Found {count} movies in database")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_movie_queries():
    """Test basic movie queries"""
    print("\n" + "="*60)
    print("🎬 Testing Movie Queries")
    print("="*60)
    
    try:
        with get_db() as db:
            # Test 1: Get all movies
            movies = db.query(Movie).limit(5).all()
            print(f"✅ Retrieved {len(movies)} sample movies:")
            for movie in movies[:3]:
                print(f"   - {movie.title} ({movie.year})")
            
            # Test 2: Search by genre
            action_movies = db.query(Movie).filter(
                Movie.genres.ilike('%Action%')
            ).limit(3).all()
            print(f"\n✅ Found {len(action_movies)} Action movies:")
            for movie in action_movies:
                print(f"   - {movie.title}")
            
            # Test 3: Top rated movies
            top_rated = db.query(Movie).filter(
                Movie.rating_count >= 10
            ).order_by(Movie.avg_rating.desc()).limit(3).all()
            print(f"\n✅ Top 3 rated movies:")
            for movie in top_rated:
                print(f"   - {movie.title}: {movie.avg_rating:.2f}/5.0 ({movie.rating_count} ratings)")
            
            return True
    except Exception as e:
        print(f"❌ Movie queries failed: {e}")
        return False


def test_search_service():
    """Test search service functionality"""
    print("\n" + "="*60)
    print("🔍 Testing Search Service")
    print("="*60)
    
    try:
        # Test 1: Basic search
        results = SearchService.search_movies("matrix", limit=3)
        print(f"✅ Search for 'matrix': Found {len(results)} results")
        for movie in results[:3]:
            print(f"   - {movie['title']}")
        
        # Test 2: Genre search
        action_results = SearchService.search_by_genre("Action", limit=3)
        print(f"\n✅ Genre search 'Action': Found {len(action_results)} results")
        for movie in action_results[:3]:
            print(f"   - {movie['title']}")
        
        # Test 3: Fuzzy search
        fuzzy_results = SearchService.fuzzy_search("inceptoin", limit=3)
        print(f"\n✅ Fuzzy search 'inceptoin': Found {len(fuzzy_results)} results")
        for movie in fuzzy_results:
            print(f"   - {movie['title']}")
        
        # Test 4: Trending movies
        trending = SearchService.get_trending_movies(limit=3)
        print(f"\n✅ Trending movies: Found {len(trending)} results")
        for movie in trending:
            print(f"   - {movie['title']} (Rating: {movie['avg_rating']:.2f})")
        
        # Test 5: Search suggestions
        suggestions = SearchService.get_search_suggestions("toy", limit=5)
        print(f"\n✅ Suggestions for 'toy': {len(suggestions)} results")
        for title in suggestions[:3]:
            print(f"   - {title}")
        
        return True
    except Exception as e:
        print(f"❌ Search service failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recommendation_service():
    """Test recommendation service"""
    print("\n" + "="*60)
    print("🎯 Testing Recommendation Service")
    print("="*60)
    
    try:
        rec_service = RecommendationService()
        
        # Test 1: Trending movies
        trending = rec_service.get_trending_movies(limit=3)
        print(f"✅ Trending recommendations: {len(trending)} movies")
        for movie in trending:
            print(f"   - {movie['title']}")
        
        # Test 2: Similar movies
        similar = rec_service.get_similar_movies("Toy Story", limit=3)
        print(f"\n✅ Similar to 'Toy Story': {len(similar)} movies")
        for movie in similar:
            print(f"   - {movie['title']}")
        
        return True
    except Exception as e:
        print(f"❌ Recommendation service failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_operations():
    """Test user-related operations"""
    print("\n" + "="*60)
    print("👥 Testing User Operations")
    print("="*60)
    
    try:
        with get_db() as db:
            # Count users
            user_count = db.query(User).count()
            print(f"✅ Found {user_count} users in database")
            
            # Count ratings
            rating_count = db.query(Rating).count()
            print(f"✅ Found {rating_count} ratings in database")
            
            # Sample user
            sample_user = db.query(User).first()
            if sample_user:
                print(f"\n✅ Sample user: {sample_user.email}")
                user_ratings = db.query(Rating).filter_by(user_id=sample_user.id).count()
                print(f"   - Has {user_ratings} ratings")
                
                watchlist_count = db.query(Watchlist).filter_by(user_id=sample_user.id).count()
                print(f"   - Has {watchlist_count} items in watchlist")
            
            return True
    except Exception as e:
        print(f"❌ User operations failed: {e}")
        return False


def test_advanced_search():
    """Test advanced search with filters"""
    print("\n" + "="*60)
    print("🔬 Testing Advanced Search")
    print("="*60)
    
    try:
        # Test with multiple filters
        results = SearchService.search_movies(
            query="",
            genres=["Action", "Thriller"],
            year_min=1990,
            year_max=2000,
            min_rating=4.0,
            sort_by="rating",
            limit=5
        )
        print(f"✅ Advanced search (Action/Thriller, 1990-2000, rating>=4.0):")
        print(f"   Found {len(results)} results")
        for movie in results[:3]:
            print(f"   - {movie['title']} ({movie['year']}) - {movie['avg_rating']:.2f}/5.0")
        
        return True
    except Exception as e:
        print(f"❌ Advanced search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 CineSense Database & Search Test Suite")
    print("="*70)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Movie Queries", test_movie_queries),
        ("Search Service", test_search_service),
        ("Recommendation Service", test_recommendation_service),
        ("User Operations", test_user_operations),
        ("Advanced Search", test_advanced_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database and search are working perfectly!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

