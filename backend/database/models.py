"""
Database Models for CineSense Movie Recommender
Using SQLAlchemy ORM with proper indexing and relationships
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model with authentication and profile information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    preferred_genre = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = relationship('Rating', back_populates='user', cascade='all, delete-orphan')
    watchlist_items = relationship('Watchlist', back_populates='user', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_age_gender', 'age', 'gender'),
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"


class Movie(Base):
    """Movie model with metadata and content information"""
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, unique=True, nullable=False, index=True)  # Original MovieLens ID
    title = Column(String(500), nullable=False, index=True)
    year = Column(Integer, index=True)
    genres = Column(String(200))  # Pipe-separated genres
    summary = Column(Text)
    plot = Column(Text)
    director = Column(String(200))
    cast = Column(Text)  # JSON string of cast members
    poster_path = Column(String(500))
    imdb_id = Column(String(20))
    tmdb_id = Column(Integer)
    avg_rating = Column(Float, default=0.0, index=True)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = relationship('Rating', back_populates='movie', cascade='all, delete-orphan')
    watchlist_items = relationship('Watchlist', back_populates='movie', cascade='all, delete-orphan')
    
    # Indexes for search and filtering
    __table_args__ = (
        Index('idx_movie_title', 'title'),
        Index('idx_movie_year', 'year'),
        Index('idx_movie_rating', 'avg_rating'),
        Index('idx_movie_title_year', 'title', 'year'),
        Index('idx_movie_genres', 'genres'),
    )
    
    def __repr__(self):
        return f"<Movie(title='{self.title}', year={self.year})>"
    
    def to_dict(self):
        """Convert movie to dictionary for API responses"""
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'title': self.title,
            'year': self.year,
            'genres': self.genres.split('|') if self.genres else [],
            'summary': self.summary,
            'poster_path': self.poster_path,
            'avg_rating': round(self.avg_rating, 2) if self.avg_rating else 0,
            'rating_count': self.rating_count
        }


class Rating(Base):
    """User ratings for movies"""
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='ratings')
    movie = relationship('Movie', back_populates='ratings')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_rating_user', 'user_id'),
        Index('idx_rating_movie', 'movie_id'),
        Index('idx_rating_user_movie', 'user_id', 'movie_id', unique=True),
        Index('idx_rating_value', 'rating'),
    )
    
    def __repr__(self):
        return f"<Rating(user_id={self.user_id}, movie_id={self.movie_id}, rating={self.rating})>"


class Watchlist(Base):
    """User watchlist for movies"""
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='watchlist_items')
    movie = relationship('Movie', back_populates='watchlist_items')
    
    # Indexes
    __table_args__ = (
        Index('idx_watchlist_user', 'user_id'),
        Index('idx_watchlist_movie', 'movie_id'),
        Index('idx_watchlist_user_movie', 'user_id', 'movie_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, movie_id={self.movie_id})>"


class SearchHistory(Base):
    """Track user search history for analytics and recommendations"""
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_search_user', 'user_id'),
        Index('idx_search_query', 'query'),
        Index('idx_search_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SearchHistory(query='{self.query}', timestamp={self.timestamp})>"

