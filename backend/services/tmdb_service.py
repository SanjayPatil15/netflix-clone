"""
TMDB API Service for fetching movie posters and metadata
"""
import tmdbsimple as tmdb
import os
import json
from pathlib import Path

# TMDB API Key - You need to get this from https://www.themoviedb.org/settings/api
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', 'YOUR_API_KEY_HERE')
tmdb.API_KEY = TMDB_API_KEY

# Cache file for poster URLs
CACHE_FILE = Path('model_cache/tmdb_posters_cache.json')

class TMDBService:
    def __init__(self):
        self.cache = self._load_cache()
        self.base_poster_url = "https://image.tmdb.org/t/p/w500"
        
    def _load_cache(self):
        """Load cached poster URLs"""
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save poster URLs to cache"""
        CACHE_FILE.parent.mkdir(exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def search_movie(self, title, year=None):
        """
        Search for a movie on TMDB
        
        Args:
            title: Movie title
            year: Release year (optional, helps with accuracy)
            
        Returns:
            dict with movie data or None
        """
        try:
            search = tmdb.Search()
            
            # Try with year first if provided
            if year:
                response = search.movie(query=title, year=year)
            else:
                response = search.movie(query=title)
            
            if response['results']:
                return response['results'][0]  # Return first match
            
            # If no results with year, try without year
            if year:
                response = search.movie(query=title)
                if response['results']:
                    return response['results'][0]
            
            return None
        except Exception as e:
            print(f"Error searching TMDB for '{title}': {e}")
            return None
    
    def get_poster_url(self, title, year=None):
        """
        Get poster URL for a movie
        
        Args:
            title: Movie title
            year: Release year (optional)
            
        Returns:
            Full poster URL or None
        """
        # Check cache first
        cache_key = f"{title}_{year}" if year else title
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Search TMDB
        movie_data = self.search_movie(title, year)
        
        if movie_data and movie_data.get('poster_path'):
            poster_url = f"{self.base_poster_url}{movie_data['poster_path']}"
            
            # Cache the result
            self.cache[cache_key] = poster_url
            self._save_cache()
            
            return poster_url
        
        # Cache negative result to avoid repeated API calls
        self.cache[cache_key] = None
        self._save_cache()
        
        return None
    
    def get_movie_details(self, title, year=None):
        """
        Get detailed movie information
        
        Args:
            title: Movie title
            year: Release year (optional)
            
        Returns:
            dict with movie details or None
        """
        movie_data = self.search_movie(title, year)
        
        if not movie_data:
            return None
        
        try:
            movie_id = movie_data['id']
            movie = tmdb.Movies(movie_id)
            details = movie.info()
            
            return {
                'title': details.get('title'),
                'overview': details.get('overview'),
                'poster_url': f"{self.base_poster_url}{details['poster_path']}" if details.get('poster_path') else None,
                'backdrop_url': f"https://image.tmdb.org/t/p/original{details['backdrop_path']}" if details.get('backdrop_path') else None,
                'release_date': details.get('release_date'),
                'vote_average': details.get('vote_average'),
                'genres': [g['name'] for g in details.get('genres', [])],
                'runtime': details.get('runtime'),
                'tagline': details.get('tagline'),
            }
        except Exception as e:
            print(f"Error getting movie details for '{title}': {e}")
            return None
    
    def batch_update_posters(self, movies_list):
        """
        Update posters for a list of movies
        
        Args:
            movies_list: List of dicts with 'title' and optionally 'year'
            
        Returns:
            dict mapping movie titles to poster URLs
        """
        results = {}
        
        for movie in movies_list:
            title = movie.get('title')
            year = movie.get('year')
            
            if not title:
                continue
            
            poster_url = self.get_poster_url(title, year)
            results[title] = poster_url
        
        return results

# Singleton instance
_tmdb_service = None

def get_tmdb_service():
    """Get or create TMDB service instance"""
    global _tmdb_service
    if _tmdb_service is None:
        _tmdb_service = TMDBService()
    return _tmdb_service

# Made with Bob
