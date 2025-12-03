"""
Migration script to populate database from existing CSV and JSON files
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_db, User, Movie, Rating, Watchlist


def extract_year_from_title(title):
    """Extract year from movie title like 'Toy Story (1995)'"""
    match = re.search(r'\((\d{4})\)', title)
    return int(match.group(1)) if match else None


def clean_title(title):
    """Remove year from title"""
    return re.sub(r'\s*\(\d{4}\)\s*$', '', title).strip()


def migrate_movies(db, movies_csv_path, wiki_csv_path=None):
    """Migrate movies from CSV to database"""
    print("\n📽️ Migrating movies...")
    
    # Load movies data
    movies_df = pd.read_csv(movies_csv_path)
    
    # Load Wikipedia plots if available
    wiki_plots = {}
    if wiki_csv_path and os.path.exists(wiki_csv_path):
        try:
            wiki_df = pd.read_csv(wiki_csv_path)
            if 'Title' in wiki_df.columns and 'Plot' in wiki_df.columns:
                wiki_plots = dict(zip(wiki_df['Title'].str.lower(), wiki_df['Plot']))
                print(f"  ✅ Loaded {len(wiki_plots)} Wikipedia plots")
        except Exception as e:
            print(f"  ⚠️ Could not load Wikipedia data: {e}")
    
    movies_added = 0
    for _, row in movies_df.iterrows():
        try:
            title = str(row['title'])
            year = extract_year_from_title(title)
            clean_movie_title = clean_title(title)
            
            # Check if movie already exists
            existing = db.query(Movie).filter_by(movie_id=int(row['movieId'])).first()
            if existing:
                continue
            
            # Get plot from Wikipedia if available
            plot = wiki_plots.get(clean_movie_title.lower(), '')
            
            movie = Movie(
                movie_id=int(row['movieId']),
                title=title,
                year=year,
                genres=str(row['genres']) if pd.notna(row['genres']) else '',
                summary=plot[:500] if plot else '',  # First 500 chars as summary
                plot=plot if plot else None
            )
            db.add(movie)
            movies_added += 1
            
            if movies_added % 100 == 0:
                db.commit()
                print(f"  ✅ Added {movies_added} movies...")
        
        except Exception as e:
            print(f"  ⚠️ Error adding movie {row.get('title', 'unknown')}: {e}")
            continue
    
    db.commit()
    print(f"✅ Successfully migrated {movies_added} movies")
    return movies_added


def migrate_users(db, users_csv_path, users_json_path):
    """Migrate users from CSV and JSON to database"""
    print("\n👥 Migrating users...")
    
    users_added = 0
    
    # First, migrate MovieLens users from CSV
    if os.path.exists(users_csv_path):
        users_df = pd.read_csv(users_csv_path)
        for _, row in users_df.iterrows():
            try:
                # Check if user exists
                user_id = int(row['userId'])
                existing = db.query(User).filter_by(email=f"movielens_user_{user_id}@system.local").first()
                if existing:
                    continue
                
                user = User(
                    email=f"movielens_user_{user_id}@system.local",
                    name=f"MovieLens User {user_id}",
                    password="system_user",  # System users don't need real passwords
                    age=int(row['age']) if pd.notna(row['age']) else None,
                    gender=str(row['gender']) if pd.notna(row['gender']) else None
                )
                db.add(user)
                users_added += 1
                
                if users_added % 100 == 0:
                    db.commit()
                    print(f"  ✅ Added {users_added} MovieLens users...")
            
            except Exception as e:
                print(f"  ⚠️ Error adding MovieLens user: {e}")
                continue
    
    # Then, migrate application users from JSON
    if os.path.exists(users_json_path):
        with open(users_json_path, 'r') as f:
            app_users = json.load(f)
        
        for email, user_data in app_users.items():
            try:
                # Check if user exists
                existing = db.query(User).filter_by(email=email).first()
                if existing:
                    continue
                
                # Handle age as string or int
                age = user_data.get('age')
                if age:
                    age = int(age) if isinstance(age, (int, str)) and str(age).isdigit() else None
                
                user = User(
                    email=email,
                    name=user_data.get('name', 'Unknown'),
                    password=user_data.get('password', ''),
                    age=age,
                    gender=user_data.get('gender'),
                    preferred_genre=user_data.get('genre')
                )
                db.add(user)
                users_added += 1
            
            except Exception as e:
                print(f"  ⚠️ Error adding app user {email}: {e}")
                continue
    
    db.commit()
    print(f"✅ Successfully migrated {users_added} users")
    return users_added


def migrate_ratings(db, ratings_csv_path, user_ratings_json_path):
    """Migrate ratings from CSV and JSON to database"""
    print("\n⭐ Migrating ratings...")
    
    ratings_added = 0
    
    # First, migrate MovieLens ratings from CSV
    if os.path.exists(ratings_csv_path):
        ratings_df = pd.read_csv(ratings_csv_path)
        
        for _, row in ratings_df.iterrows():
            try:
                # Get user and movie from database
                user_email = f"movielens_user_{int(row['userId'])}@system.local"
                user = db.query(User).filter_by(email=user_email).first()
                movie = db.query(Movie).filter_by(movie_id=int(row['movieId'])).first()
                
                if not user or not movie:
                    continue
                
                # Check if rating exists
                existing = db.query(Rating).filter_by(
                    user_id=user.id,
                    movie_id=movie.id
                ).first()
                if existing:
                    continue
                
                rating = Rating(
                    user_id=user.id,
                    movie_id=movie.id,
                    rating=float(row['rating']),
                    timestamp=datetime.fromtimestamp(int(row['timestamp'])) if pd.notna(row.get('timestamp')) else datetime.utcnow()
                )
                db.add(rating)
                ratings_added += 1
                
                if ratings_added % 500 == 0:
                    db.commit()
                    print(f"  ✅ Added {ratings_added} ratings...")
            
            except Exception as e:
                if ratings_added % 1000 == 0:
                    print(f"  ⚠️ Error adding rating: {e}")
                continue
    
    # Then, migrate application user ratings from JSON
    if os.path.exists(user_ratings_json_path):
        with open(user_ratings_json_path, 'r') as f:
            app_ratings = json.load(f)
        
        for email, movie_ratings in app_ratings.items():
            try:
                user = db.query(User).filter_by(email=email).first()
                if not user:
                    continue
                
                for movie_title, rating_value in movie_ratings.items():
                    # Find movie by title (case-insensitive)
                    movie = db.query(Movie).filter(
                        Movie.title.ilike(f"%{movie_title}%")
                    ).first()
                    
                    if not movie:
                        continue
                    
                    # Check if rating exists
                    existing = db.query(Rating).filter_by(
                        user_id=user.id,
                        movie_id=movie.id
                    ).first()
                    if existing:
                        continue
                    
                    rating = Rating(
                        user_id=user.id,
                        movie_id=movie.id,
                        rating=float(rating_value)
                    )
                    db.add(rating)
                    ratings_added += 1
            
            except Exception as e:
                print(f"  ⚠️ Error adding app user ratings for {email}: {e}")
                continue
    
    db.commit()
    print(f"✅ Successfully migrated {ratings_added} ratings")
    
    # Update movie average ratings
    update_movie_ratings(db)
    
    return ratings_added


def migrate_watchlist(db, watchlist_json_path):
    """Migrate watchlist from JSON to database"""
    print("\n📋 Migrating watchlist...")
    
    if not os.path.exists(watchlist_json_path):
        print("  ⚠️ Watchlist file not found")
        return 0
    
    with open(watchlist_json_path, 'r') as f:
        watchlist_data = json.load(f)
    
    items_added = 0
    for email, movie_titles in watchlist_data.items():
        try:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                continue
            
            for movie_title in movie_titles:
                # Find movie by title
                movie = db.query(Movie).filter(
                    Movie.title.ilike(f"%{movie_title}%")
                ).first()
                
                if not movie:
                    continue
                
                # Check if already in watchlist
                existing = db.query(Watchlist).filter_by(
                    user_id=user.id,
                    movie_id=movie.id
                ).first()
                if existing:
                    continue
                
                watchlist_item = Watchlist(
                    user_id=user.id,
                    movie_id=movie.id
                )
                db.add(watchlist_item)
                items_added += 1
        
        except Exception as e:
            print(f"  ⚠️ Error adding watchlist for {email}: {e}")
            continue
    
    db.commit()
    print(f"✅ Successfully migrated {items_added} watchlist items")
    return items_added


def update_movie_ratings(db):
    """Update average ratings and rating counts for all movies"""
    print("\n📊 Updating movie statistics...")
    
    movies = db.query(Movie).all()
    updated = 0
    
    for movie in movies:
        ratings = db.query(Rating).filter_by(movie_id=movie.id).all()
        if ratings:
            movie.rating_count = len(ratings)
            movie.avg_rating = sum(r.rating for r in ratings) / len(ratings)
            updated += 1
    
    db.commit()
    print(f"✅ Updated statistics for {updated} movies")


def main():
    """Main migration function"""
    print("=" * 60)
    print("🎬 CineSense Database Migration")
    print("=" * 60)
    
    # Initialize database
    print("\n🔧 Initializing database...")
    init_db()
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    movielens_dir = os.path.join(data_dir, 'movielens')
    wikipedia_dir = os.path.join(data_dir, 'wikipedia')
    
    movies_csv = os.path.join(movielens_dir, 'movies.csv')
    users_csv = os.path.join(movielens_dir, 'users.csv')
    ratings_csv = os.path.join(movielens_dir, 'ratings.csv')
    wiki_csv = os.path.join(wikipedia_dir, 'wiki_movie_plots_deduped.csv')
    
    users_json = os.path.join(data_dir, 'users_db.json')
    user_ratings_json = os.path.join(data_dir, 'user_ratings.json')
    watchlist_json = os.path.join(base_dir, 'model_cache', 'watchlist.json')
    
    # Perform migration
    with get_db() as db:
        # Migrate in order: movies -> users -> ratings -> watchlist
        migrate_movies(db, movies_csv, wiki_csv)
        migrate_users(db, users_csv, users_json)
        migrate_ratings(db, ratings_csv, user_ratings_json)
        migrate_watchlist(db, watchlist_json)
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

