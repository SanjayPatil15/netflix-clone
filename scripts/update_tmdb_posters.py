"""
Script to update movie posters from TMDB API
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db
from backend.database.models import Movie
from backend.services.tmdb_service import get_tmdb_service
import re

def extract_year_from_title(title):
    """Extract year from movie title if present"""
    match = re.search(r'\((\d{4})\)', title)
    if match:
        return int(match.group(1))
    return None

def clean_title(title):
    """Remove year from title"""
    return re.sub(r'\s*\(\d{4}\)\s*$', '', title).strip()

def update_movie_posters(limit=None):
    """
    Update movie posters from TMDB
    
    Args:
        limit: Maximum number of movies to update (None for all)
    """
    db = next(get_db())
    tmdb_service = get_tmdb_service()
    
    # Get all movies
    query = db.query(Movie)
    if limit:
        query = query.limit(limit)
    
    movies = query.all()
    
    print(f"Updating posters for {len(movies)} movies...")
    
    updated_count = 0
    failed_count = 0
    
    for i, movie in enumerate(movies, 1):
        # Extract year and clean title
        year = extract_year_from_title(movie.title)
        clean_movie_title = clean_title(movie.title)
        
        print(f"[{i}/{len(movies)}] Processing: {clean_movie_title} ({year or 'no year'})")
        
        # Get poster URL from TMDB
        poster_url = tmdb_service.get_poster_url(clean_movie_title, year)
        
        if poster_url:
            # Update movie poster in database
            movie.poster_url = poster_url
            updated_count += 1
            print(f"  ✓ Updated poster: {poster_url}")
        else:
            failed_count += 1
            print(f"  ✗ No poster found")
        
        # Commit every 10 movies to avoid losing progress
        if i % 10 == 0:
            db.commit()
            print(f"  → Committed {i} movies")
    
    # Final commit
    db.commit()
    
    print("\n" + "="*60)
    print(f"Update complete!")
    print(f"  Updated: {updated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(movies)}")
    print("="*60)

def update_specific_movies(movie_titles):
    """
    Update posters for specific movies
    
    Args:
        movie_titles: List of movie titles
    """
    db = next(get_db())
    tmdb_service = get_tmdb_service()
    
    print(f"Updating posters for {len(movie_titles)} specific movies...")
    
    for title in movie_titles:
        movie = db.query(Movie).filter(Movie.title == title).first()
        
        if not movie:
            print(f"✗ Movie not found: {title}")
            continue
        
        year = extract_year_from_title(movie.title)
        clean_movie_title = clean_title(movie.title)
        
        poster_url = tmdb_service.get_poster_url(clean_movie_title, year)
        
        if poster_url:
            movie.poster_url = poster_url
            db.commit()
            print(f"✓ Updated: {title}")
        else:
            print(f"✗ No poster found: {title}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update movie posters from TMDB')
    parser.add_argument('--limit', type=int, help='Limit number of movies to update')
    parser.add_argument('--movies', nargs='+', help='Specific movie titles to update')
    
    args = parser.parse_args()
    
    if args.movies:
        update_specific_movies(args.movies)
    else:
        update_movie_posters(args.limit)

# Made with Bob
