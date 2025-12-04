# CineSense Setup Guide

This guide will help you set up and run the new features added to CineSense.

## New Features Added

### 1. Enhanced Signup Flow
- ✅ Country field added to signup for better demographics
- ✅ Genre preference removed from signup (now asked after signup)
- ✅ Multi-select genre selection (exactly 3 genres required)

### 2. TMDB Integration
- ✅ TMDB API service for fetching movie posters
- ✅ Automatic poster URL caching
- ✅ Script to update all movie posters from TMDB

### 3. Improved Movie Modal
- ✅ Auto-play trailer when modal opens (no click needed)
- ✅ Bigger trailer section (500px height for better viewing)

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `tmdbsimple==2.9.1` - TMDB API client
- `Flask==3.0.0` - Web framework
- `google-api-python-client==2.108.0` - YouTube API client
- All other existing dependencies

### Step 2: Get TMDB API Key

1. Go to https://www.themoviedb.org/
2. Create a free account
3. Go to Settings → API
4. Request an API key (choose "Developer" option)
5. Copy your API key

### Step 3: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:TMDB_API_KEY="your_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set TMDB_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export TMDB_API_KEY="your_api_key_here"
```

**Or create a .env file:**
```
TMDB_API_KEY=your_api_key_here
```

### Step 4: Run Database Migrations

Run these scripts in order:

```bash
# 1. Add country and genres fields to users table
python scripts/add_country_and_genres.py

# 2. Add poster_url field to movies table
python scripts/add_poster_url_field.py
```

### Step 5: Update Movie Posters (Optional but Recommended)

This will fetch high-quality posters from TMDB for all movies:

```bash
# Update all movies (this may take a while)
python scripts/update_tmdb_posters.py

# Or update only first 100 movies for testing
python scripts/update_tmdb_posters.py --limit 100

# Or update specific movies
python scripts/update_tmdb_posters.py --movies "The Matrix (1999)" "Inception (2010)"
```

**Note:** The script will:
- Cache poster URLs to avoid repeated API calls
- Commit every 10 movies to avoid losing progress
- Show progress for each movie

### Step 6: Run the Application

```bash
python app.py
```

The application will be available at: http://localhost:5000

## Testing the New Features

### 1. Test Signup Flow

1. Go to http://localhost:5000/signup
2. Fill in the form (notice the country dropdown)
3. Submit the form
4. You'll be redirected to genre selection page
5. Select exactly 3 genres (counter shows "Selected: X/3")
6. Submit button appears only when 3 genres are selected

### 2. Test Movie Modal

1. Login and go to dashboard
2. Click on any movie card
3. **Trailer should auto-play immediately** (no need to click "Watch Trailer")
4. Trailer section is now bigger (500px height)
5. Movie poster should be high-quality from TMDB (if you ran the update script)

### 3. Test TMDB Posters

1. Check if movies have better quality posters
2. Posters are fetched from TMDB's CDN
3. Fallback to local posters if TMDB poster not available

## File Structure

```
movie_recommender/
├── backend/
│   ├── database/
│   │   ├── models.py          # Updated with poster_url and country fields
│   │   └── connection.py
│   └── services/
│       └── tmdb_service.py    # NEW: TMDB API integration
├── frontend/
│   └── templates/
│       ├── signup.html        # Updated with country field
│       ├── choose_genre.html  # NEW: Multi-select genre page
│       └── base.html          # Updated with auto-play trailer
├── scripts/
│   ├── add_country_and_genres.py    # Migration script
│   ├── add_poster_url_field.py      # Migration script
│   └── update_tmdb_posters.py       # Poster update script
├── requirements.txt           # Updated with new dependencies
└── SETUP_GUIDE.md            # This file
```

## Troubleshooting

### Issue: TMDB API Key Error
**Solution:** Make sure you've set the `TMDB_API_KEY` environment variable correctly.

### Issue: Migration Script Fails
**Solution:** Check if the database file exists and you have write permissions.

### Issue: Posters Not Updating
**Solution:** 
1. Check your TMDB API key is valid
2. Check your internet connection
3. Look at the console output for specific errors

### Issue: Trailer Not Auto-Playing
**Solution:** 
1. Some browsers block autoplay - check browser settings
2. Make sure YouTube API is working
3. Check browser console for errors

### Issue: Genre Selection Not Working
**Solution:**
1. Clear browser cache
2. Make sure JavaScript is enabled
3. Check browser console for errors

## API Rate Limits

TMDB API has the following limits:
- **Free tier:** 40 requests per 10 seconds
- The script handles this by processing movies sequentially
- Poster URLs are cached to avoid repeated API calls

## Database Schema Changes

### Users Table
- Added: `country` (VARCHAR 100)
- Changed: `preferred_genre` → `preferred_genres` (VARCHAR 200, comma-separated)

### Movies Table
- Added: `poster_url` (VARCHAR 500) - TMDB poster URL

## Next Steps

1. ✅ Run all migration scripts
2. ✅ Set up TMDB API key
3. ✅ Update movie posters
4. ✅ Test signup flow
5. ✅ Test movie modal with auto-play
6. ✅ Verify TMDB posters are loading

## Support

If you encounter any issues:
1. Check the console output for error messages
2. Verify all environment variables are set
3. Make sure all dependencies are installed
4. Check database file permissions

## Notes

- The TMDB service caches poster URLs in `model_cache/tmdb_posters_cache.json`
- Local posters in `static/posters/` are still used as fallback
- Genre selection requires exactly 3 genres for better recommendations
- Country data helps improve demographic-based recommendations