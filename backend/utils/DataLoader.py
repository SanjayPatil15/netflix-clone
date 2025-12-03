"""
Data Loader for CineSense - Database-backed version
Provides backward compatibility with CSV loading while using database
"""

import pandas as pd
import os
from typing import Optional
from backend.database import get_db, Movie, User, Rating


class DataLoader:
    """
    Load movie, user, and rating data from database or CSV files.
    Provides pandas DataFrames for compatibility with existing models.
    """
    
    def __init__(self, movielens_dir: str, wikipedia_dir: str = None):
        self.movielens_dir = movielens_dir
        self.wikipedia_dir = wikipedia_dir
        self._use_database = True
        
        # Check if database exists
        # Go up two levels from backend/utils/ to reach project root, then into data/
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'cinesense.db')
        if not os.path.exists(db_path):
            print("⚠️ Database not found, falling back to CSV files")
            self._use_database = False
    
    def load_movies_data(self) -> pd.DataFrame:
        """Load movies data from database or CSV"""
        if self._use_database:
            try:
                with get_db() as db:
                    movies = db.query(Movie).all()
                    data = [{
                        'movieId': m.movie_id,
                        'title': m.title,
                        'genres': m.genres,
                        'year': m.year,
                        'summary': m.summary or '',
                        'avg_rating': m.avg_rating,
                        'rating_count': m.rating_count
                    } for m in movies]
                    df = pd.DataFrame(data)
                    print(f"✅ Loaded {len(df)} movies from database")
                    return df
            except Exception as e:
                print(f"⚠️ Database error: {e}, falling back to CSV")
                self._use_database = False
        
        # Fallback to CSV
        movies_path = os.path.join(self.movielens_dir, 'movies.csv')
        df = pd.read_csv(movies_path)
        
        # Add summary column if Wikipedia data available
        if self.wikipedia_dir:
            wiki_path = os.path.join(self.wikipedia_dir, 'wiki_movie_plots_deduped.csv')
            if os.path.exists(wiki_path):
                try:
                    wiki_df = pd.read_csv(wiki_path)
                    if 'Title' in wiki_df.columns and 'Plot' in wiki_df.columns:
                        # Create a mapping of title to plot
                        wiki_dict = dict(zip(
                            wiki_df['Title'].str.lower(),
                            wiki_df['Plot']
                        ))
                        # Add summary column
                        df['summary'] = df['title'].str.lower().map(wiki_dict).fillna('')
                except Exception as e:
                    print(f"⚠️ Could not load Wikipedia data: {e}")
                    df['summary'] = ''
        
        print(f"✅ Loaded {len(df)} movies from CSV")
        return df
    
    def load_ratings_data(self) -> pd.DataFrame:
        """Load ratings data from database or CSV"""
        if self._use_database:
            try:
                with get_db() as db:
                    ratings = db.query(Rating).join(User).join(Movie).all()
                    data = [{
                        'userId': r.user.email,  # Use email as userId for app users
                        'movieId': r.movie.movie_id,
                        'rating': r.rating,
                        'timestamp': int(r.timestamp.timestamp()) if r.timestamp else 0
                    } for r in ratings]
                    df = pd.DataFrame(data)
                    print(f"✅ Loaded {len(df)} ratings from database")
                    return df
            except Exception as e:
                print(f"⚠️ Database error: {e}, falling back to CSV")
                self._use_database = False
        
        # Fallback to CSV
        ratings_path = os.path.join(self.movielens_dir, 'ratings.csv')
        df = pd.read_csv(ratings_path)
        print(f"✅ Loaded {len(df)} ratings from CSV")
        return df
    
    def load_users_data(self) -> pd.DataFrame:
        """Load users data from database or CSV"""
        if self._use_database:
            try:
                with get_db() as db:
                    users = db.query(User).all()
                    data = [{
                        'userId': u.email,
                        'age': u.age or 0,
                        'gender': u.gender or 'M',
                        'preferred_genre': u.preferred_genre
                    } for u in users]
                    df = pd.DataFrame(data)
                    print(f"✅ Loaded {len(df)} users from database")
                    return df
            except Exception as e:
                print(f"⚠️ Database error: {e}, falling back to CSV")
                self._use_database = False
        
        # Fallback to CSV
        users_path = os.path.join(self.movielens_dir, 'users.csv')
        df = pd.read_csv(users_path)
        print(f"✅ Loaded {len(df)} users from CSV")
        return df
    
    def load_wikipedia_data(self) -> pd.DataFrame:
        """Load Wikipedia movie plots data with encoding handling"""
        if not self.wikipedia_dir:
            return pd.DataFrame()
        
        wiki_path = os.path.join(self.wikipedia_dir, 'wiki_movie_plots_deduped.csv')
        if not os.path.exists(wiki_path):
            return pd.DataFrame()
        
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(wiki_path, encoding=encoding, on_bad_lines='skip')
                print(f"✅ Loaded {len(df)} Wikipedia plots (encoding: {encoding})")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"⚠️ Error with {encoding}: {e}")
                continue
        
        print(f"⚠️ Could not load Wikipedia data with any encoding")
        return pd.DataFrame()

