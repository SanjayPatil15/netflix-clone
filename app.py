# -*- coding: utf-8 -*-
# CINESENSE - Movie Recommender System
# Gmail OTP + Genre + Search + AI + Watchlist - FULLY WORKING

import sys
import codecs

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_mail import Mail, Message
import os, pickle, re, json, random, pandas as pd
from datetime import datetime, timedelta
from difflib import get_close_matches
import time
import glob
from urllib.parse import quote  # for safe deep links
from urllib.parse import quote_plus  # add at top if not already
from pytube import Search
import re
import requests




# --- Local Imports ---
from backend.utils.DataLoader import DataLoader
from backend.utils.auth import load_users, save_users, save_session, clear_session, load_session
from backend.models.ALSModel import ALSRecommender
from backend.models.DemographicsModel import DemographicRecommender
from backend.models.ContentSimilarity import ContentBasedRecommender
from backend.models.HybridModel import HybridRecommender

OMDB_API_KEY = "55988766"
TMDB_API_KEY = "a4a29e010ff1222cfcf4b851a99fddb3"
YOUTUBE_API_KEY = "AIzaSyC24htkpXTRAeLXMKf4liYiUyIMtrPV1uU"


# ---------------- HELPERS ----------------
def fuzzy_find(title, all_titles, cutoff=0.5):
    matches = get_close_matches(title.lower(), [t.lower() for t in all_titles], n=1, cutoff=cutoff)
    if matches:
        for t in all_titles:
            if t.lower() == matches[0]:
                return t
    return None


# ---------------- APP CONFIG ----------------
app = Flask(__name__,
            template_folder='frontend/templates',
            static_folder='frontend/static')
app.secret_key = "your_secret_key"

# Completely disable caching for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Override Flask's static file serving to force no-cache
@app.route('/static/<path:filename>')
def custom_static(filename):
    """Custom static file handler that forces no-cache headers"""
    response = send_from_directory('frontend/static', filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    return response

@app.after_request
def add_no_cache_headers(response):
    """
    Add no-cache headers to all responses during development.
    This prevents 304 (Not Modified) responses.
    """
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# ✅ Gmail Config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='avik82of53@gmail.com',
    MAIL_PASSWORD='cxujzcndtpoegnll',
    MAIL_DEFAULT_SENDER=('CineSense Support', 'avik82of53@gmail.com')
)
mail = Mail(app)
print("✅ Flask app started — CineSense fully connected")


# ---------------- PATHS ----------------
CACHE_DIR = "model_cache"
ALS_CACHE = os.path.join(CACHE_DIR, "als_model.pkl")
CONTENT_CACHE = os.path.join(CACHE_DIR, "content_vectors.pkl")
POSTERS_DIR = os.path.join("frontend", "static", "posters")
DEFAULT_POSTER = "/static/default_poster.png"
WATCHLIST_FILE = os.path.join(CACHE_DIR, "watchlist.json")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(POSTERS_DIR, exist_ok=True)
if not os.path.exists(WATCHLIST_FILE):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({}, f)


# ---------------- LOAD DATA ----------------
loader = DataLoader("data/movielens", "data/wikipedia")
ratings_df = loader.load_ratings_data()
movies_df = loader.load_movies_data()
users_df = loader.load_users_data()


# ---------------- SMALL HELPERS ----------------
def clean_filename(title: str) -> str:
    """Strip punctuation, replace spaces, keep a single 4-digit year if present."""
    t = re.sub(r"[^\w\s]", "", title)
    t = t.replace(" ", "_")
    m = re.search(r"(\d{4})", title)
    year = m.group(1) if m else ""
    return f"{t}_{year}" if year else t


def find_poster(title: str, folder: str = "posters") -> str:
    """
    Smart poster finder that searches frontend/static/<folder> for .jpg/.png.
    Matches are case-insensitive and allow extra suffixes (e.g. _1996_1996).
    """
    # base pattern to match
    base = re.sub(r"[^\w\s]", "", title).replace(" ", "_").lower()

    # gather candidates
    patterns = [os.path.join("frontend", "static", folder, "*.jpg"),
                os.path.join("frontend", "static", folder, "*.jpeg"),
                os.path.join("frontend", "static", folder, "*.png")]
    candidates = []
    for p in patterns:
        candidates.extend(glob.glob(p))

    # try stricter first (startswith), then contains
    for path in candidates:
        name = os.path.basename(path).lower()
        if name.startswith(base):  # best case
            # Return path relative to static folder for Flask
            return "/static/" + folder + "/" + os.path.basename(path)
    for path in candidates:
        name = os.path.basename(path).lower()
        if base in name:
            # Return path relative to static folder for Flask
            return "/static/" + folder + "/" + os.path.basename(path)

    return DEFAULT_POSTER


def get_poster(title: str) -> str:
    """
    Get movie poster with priority:
    1. TMDB API (high quality) - ALWAYS TRY FIRST
    2. Local static/posters folder - Only if TMDB fails
    3. Fallback to default poster
    """
    import re
    
    # Extract year from title if present
    year_match = re.search(r'\((\d{4})\)', title)
    year = int(year_match.group(1)) if year_match else None
    clean_title = re.sub(r'\s*\(\d{4}\)\s*$', '', title).strip()
    
    # ALWAYS TRY TMDB API FIRST - Don't check local files first!
    try:
        import tmdbsimple as tmdb
        tmdb.API_KEY = TMDB_API_KEY
        
        search = tmdb.Search()
        if year:
            response = search.movie(query=clean_title, year=year)
        else:
            response = search.movie(query=clean_title)
        
        if response.get('results') and len(response['results']) > 0:
            poster_path = response['results'][0].get('poster_path')
            if poster_path:
                tmdb_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                print(f"✓ TMDB poster found for '{title}': {tmdb_url}")
                return tmdb_url
        
        print(f"⚠ No TMDB results for '{title}', trying local...")
    except Exception as e:
        print(f"✗ TMDB API error for '{title}': {e}")
    
    # Only use local posters if TMDB completely failed
    filename = clean_filename(title)
    exact_jpg = os.path.join(POSTERS_DIR, f"{filename}.jpg")
    exact_png = os.path.join(POSTERS_DIR, f"{filename}.png")
    
    if os.path.exists(exact_jpg):
        print(f"→ Using local poster: {exact_jpg}")
        return "/static/posters/" + os.path.basename(exact_jpg)
    if os.path.exists(exact_png):
        print(f"→ Using local poster: {exact_png}")
        return "/static/posters/" + os.path.basename(exact_png)
    
    # Final fallback
    print(f"→ Using fallback for '{title}'")
    return find_poster(title, folder="posters")


def load_watchlist():
    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)


def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- LOAD MODELS ----------------
print("⏳ Loading models...")
demo_model = DemographicRecommender(users_df, ratings_df, movies_df)
demo_model.build_user_profiles()

if os.path.exists(ALS_CACHE):
    with open(ALS_CACHE, "rb") as f:
        als_model = pickle.load(f)
else:
    als_model = ALSRecommender()
    als_model.train(ratings_df)
    with open(ALS_CACHE, "wb") as f:
        pickle.dump(als_model, f)

with open(CONTENT_CACHE, "rb") as f:
    fused_vectors = pickle.load(f)

content_model = ContentBasedRecommender(fused_vectors, movies_df["movieId"].tolist(), top_k=100)
hybrid_model = HybridRecommender(als_model, content_model, demo_model, weights=(0.4, 0.3, 0.3))
print("✅ Models ready!")


# ---------------- AUTH + OTP SYSTEM ----------------
otp_store = {}


@app.route("/")
def home():
    email = load_session()
    if email:
        return redirect(url_for("dashboard"))
    else:
        # Show landing page for non-logged-in users
        return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login_view():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        users = load_users()
        if email in users and users[email]["password"] == password:
            save_session(email)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials!")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup_view():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        users = load_users()
        if email in users:
            flash("Email already exists.")
        else:
            user_data = {
                "name": request.form["name"],
                "age": request.form["age"],
                "gender": request.form["gender"],
                "country": request.form.get("country", "Other"),  # New field
                "password": request.form["password"]
                # Note: genres will be saved separately after genre selection page
            }
            users[email] = user_data
            save_users(users)
            save_session(email)
            return redirect(url_for("choose_genre"))
    return render_template("signup.html")


@app.route("/save_genres", methods=["POST"])
def save_genres():
    """Save user's selected genres (called from choose_genre page)"""
    email = load_session()
    if not email:
        return jsonify({"status": "error", "message": "Not logged in"})
    
    data = request.get_json()
    genres = data.get("genres", [])
    is_first_time = data.get("is_first_time", False)
    
    # Validate based on first time or not
    if is_first_time and len(genres) != 3:
        return jsonify({"status": "error", "message": "Please select exactly 3 genres"})
    elif not is_first_time and len(genres) != 1:
        return jsonify({"status": "error", "message": "Please select 1 genre"})
    
    # Save to users JSON
    users = load_users()
    if email in users:
        if is_first_time:
            # First time: save as preferred genres
            users[email]["genres"] = ",".join(genres)
        else:
            # Returning user: just browsing, don't overwrite preferences
            # We'll use this for filtering movies by genre
            pass
        save_users(users)
    
    # Also update database if user exists there (only for first time)
    if is_first_time:
        try:
            db = next(get_db())
            user = db.query(User).filter_by(email=email).first()
            if user:
                user.preferred_genres = ",".join(genres)
                db.commit()
        except Exception as e:
            print(f"Error updating genres in database: {e}")
    
    return jsonify({
        "status": "success",
        "message": "Genres saved",
        "redirect": "/dashboard" if is_first_time else f"/recommend_by_genre/{genres[0]}"
    })


@app.route("/logout")
def logout():
    clear_session()
    return redirect(url_for("login_view"))


# ---------------- OTP ROUTES ----------------
@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        users = load_users()
        if not email:
            return jsonify({"status": "error", "message": "Email required."})
        if not email.endswith("@gmail.com"):
            return jsonify({"status": "error", "message": "Only Gmail addresses allowed."})
        if email not in users:
            return jsonify({"status": "error", "message": "Email not registered."})
        otp = str(random.randint(100000, 999999))
        otp_store[email] = {"otp": otp, "expires": datetime.utcnow() + timedelta(minutes=10)}
        with app.app_context():
            msg = Message(
                subject="🎬 CineSense OTP Verification",
                recipients=[email],
                body=f"Your CineSense OTP is {otp}\nIt expires in 10 minutes."
            )
            mail.send(msg)
        print(f"✅ OTP sent to {email}: {otp}")
        return jsonify({"status": "success", "redirect": url_for("verify_otp", email=email)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/verify_otp/<email>", methods=["GET", "POST"])
def verify_otp(email):
    record = otp_store.get(email.lower())
    if not record:
        flash("OTP expired or not found.")
        return redirect(url_for("login_view"))
    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        if otp == record["otp"]:
            return redirect(url_for("reset_password_page", email=email))
        flash("❌ Invalid OTP.")
    return render_template("verify_otp.html", email=email)


@app.route("/reset_password/<email>", methods=["GET", "POST"])
def reset_password_page(email):
    users = load_users()
    if request.method == "POST":
        new_pass = request.form.get("new_password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        if len(new_pass) < 8 or not re.search(r"[A-Z]", new_pass) or not re.search(r"\d", new_pass):
            flash("Password must be at least 8 chars with one uppercase and one number.")
            return render_template("reset_password.html", email=email)
        if new_pass != confirm:
            flash("Passwords do not match.")
            return render_template("reset_password.html", email=email)
        users[email]["password"] = new_pass
        save_users(users)
        otp_store.pop(email, None)
        flash("✅ Password reset successful! Please log in.")
        return redirect(url_for("login_view"))
    return render_template("reset_password.html", email=email)


# ---------------- GENRE ----------------
@app.route("/choose_genre")
def choose_genre():
    email = load_session()
    if not email:
        return redirect(url_for("login_view"))
    users = load_users()
    user = users.get(email)
    
    # Check if user has already selected genres (first time vs returning)
    is_first_time = not user.get("genres")
    
    genres = ["Action", "Romance", "Comedy", "Thriller", "Sci-Fi", "Horror", "Adventure", "Drama"]
    genres = [g.strip() for g in genres if g.strip()]
    all_posters = [f for f in os.listdir(POSTERS_DIR) if f.endswith(".jpg")]
    random_bg = random.choice(all_posters) if all_posters else "default_poster.png"
    
    return render_template("choose_genre.html",
                         user=user,
                         genres=genres,
                         random_bg=random_bg,
                         is_first_time=is_first_time)


@app.route("/dashboard")
def dashboard():
    email = load_session()
    if not email:
        return redirect(url_for("login_view"))

    users = load_users()
    user = users.get(email)

    # Get user's watchlist and ratings
    user_watchlist = load_watchlist().get(email, [])
    
    # Get user's preferred genres
    user_genres = user.get("genres", "").split(",") if user.get("genres") else []
    user_genres = [g.strip() for g in user_genres if g.strip()]
    
    # Load user ratings to filter out disliked movies
    ratings_file = "data/user_ratings.json"
    user_ratings = {}
    try:
        with open(ratings_file, 'r') as f:
            all_ratings = json.load(f)
            user_ratings = all_ratings.get(email, {})
    except:
        pass
    
    # Get disliked movies (rating = 1)
    disliked_movies = [title for title, data in user_ratings.items() if data.get("rating") == 1]
    
    # 🎯 AI Picks (personalized by genre and ratings)
    ai_movies = []
    try:
        rec = None
        try:
            rec = hybrid_model.recommend(user_id=email, top_n=60)  # Get more to filter
        except TypeError:
            try:
                rec = hybrid_model.recommend(user_id=email, n=60)
            except TypeError:
                rec = hybrid_model.recommend(email)
        
        movie_ids = []
        if rec:
            first = rec[0]
            if isinstance(first, (list, tuple)):
                for item in rec:
                    movie_ids.append(int(item[0]))
            else:
                movie_ids = [int(x) for x in rec]
        
        # Convert movie IDs to titles and filter by user's genres
        titles = []
        for movie_id in movie_ids:
            movie_row = movies_df[movies_df["movieId"] == movie_id]
            if not movie_row.empty:
                title = movie_row.iloc[0]["title"]
                genres = movie_row.iloc[0].get("genres", "")
                
                # If user has genre preferences, prioritize those
                if user_genres:
                    if any(ug.lower() in genres.lower() for ug in user_genres):
                        titles.append(title)
                else:
                    titles.append(title)
        
        # Filter out watchlist and disliked movies
        filtered_titles = [t for t in titles if t not in user_watchlist and t not in disliked_movies]
        
        # If not enough, add genre-based recommendations
        if len(filtered_titles) < 12 and user_genres:
            for genre in user_genres:
                genre_movies = movies_df[movies_df["genres"].str.contains(genre, case=False, na=False)]
                genre_ids = genre_movies["movieId"].tolist()
                genre_ratings = ratings_df[ratings_df["movieId"].isin(genre_ids)]
                top_genre_ids = genre_ratings.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(20).index.tolist()
                
                for movie_id in top_genre_ids:
                    movie_row = movies_df[movies_df["movieId"] == movie_id]
                    if not movie_row.empty:
                        title = movie_row.iloc[0]["title"]
                        if title not in filtered_titles and title not in user_watchlist and title not in disliked_movies:
                            filtered_titles.append(title)
                            if len(filtered_titles) >= 20:
                                break
                if len(filtered_titles) >= 20:
                    break
        
        if filtered_titles:
            ai_movies = [{"title": t, "poster": get_poster(t), "reason": "AI Personalized for You"} for t in filtered_titles[:12]]
    except Exception as e:
        print(f"[WARN] AI recommendations failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to genre-based trending if no AI recommendations
    if not ai_movies:
        if user_genres:
            # Get top rated from user's genres
            for genre in user_genres:
                genre_movies = movies_df[movies_df["genres"].str.contains(genre, case=False, na=False)]
                genre_ids = genre_movies["movieId"].tolist()
                genre_ratings = ratings_df[ratings_df["movieId"].isin(genre_ids)]
                top_ids = genre_ratings.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(15).index.tolist()
                trending_titles = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()
                filtered_trending = [t for t in trending_titles if t not in user_watchlist and t not in disliked_movies]
                ai_movies.extend([{"title": t, "poster": get_poster(t), "reason": f"{genre} Picks"} for t in filtered_trending[:4]])
                if len(ai_movies) >= 12:
                    break
        else:
            # Generic top rated
            top_ids = ratings_df.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(30).index.tolist()
            trending_titles = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()
            filtered_trending = [t for t in trending_titles if t not in user_watchlist and t not in disliked_movies]
            ai_movies = [{"title": t, "poster": get_poster(t), "reason": "Top Rated"} for t in filtered_trending[:12]]

    # ❤️ Watchlist
    watchlist_data = load_watchlist().get(email, [])
    watchlist_movies = [{"title": t, "poster": get_poster(t)} for t in watchlist_data]

    # 🎭 Genre posters
    genres = [
        {"name": "Action", "poster": "action.jpg"},
        {"name": "Romance", "poster": "romance.jpg"},
        {"name": "Comedy", "poster": "comedy.jpg"},
        {"name": "Thriller", "poster": "thriller.jpg"},
        {"name": "Sci-Fi", "poster": "sci-fi.jpg"},
        {"name": "Horror", "poster": "horror.jpg"},
        {"name": "Adventure", "poster": "adventure.jpg"},
        {"name": "Drama", "poster": "drama.jpg"}
    ]

    # 🔥 Trending Fallback
    trending_titles = random.sample(movies_df["title"].tolist(), 12)
    trending = [{"title": t, "poster": get_poster(t)} for t in trending_titles]

    return render_template(
        "dashboard.html",
        user=user,
        ai_movies=ai_movies,
        watchlist_movies=watchlist_movies,
        genres=genres,
        trending=trending
    )


@app.route("/recommend_by_genre/<path:genre>")
def recommend_by_genre(genre):
    email = load_session()
    if not email:
        return redirect(url_for("login_view"))
    genre = str(genre or "").strip()
    if not genre:
        flash("Invalid genre selected.")
        return redirect(url_for("choose_genre"))
    try:
        recs = demo_model.recommend_by_genre(genre, movies_df)
    except Exception:
        pool = movies_df[movies_df["genres"].str.contains(genre, case=False, na=False)]
        if pool.empty:
            top_ids = ratings_df.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(50).index.tolist()
            titles = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()
        else:
            titles = pool["title"].head(50).tolist()
        recs = titles
    normalized = [str(r[0]) if isinstance(r, (list, tuple)) else str(r) for r in recs]
    movies = [{"title": t, "poster": get_poster(t), "reason": f"Genre: {genre}"} for t in normalized[:50]]
    return render_template("recommendations.html", recommendations=movies, selected_genre=genre)


# ---------------- AI PICKS ----------------
@app.route("/ai")
def ai_suggestions():
    email = load_session()
    if not email:
        return redirect(url_for("login_view"))
    
    # Get user data
    users = load_users()
    user = users.get(email, {})
    user_watchlist = load_watchlist().get(email, [])
    
    # Get user's preferred genres
    user_genres = user.get("genres", "").split(",") if user.get("genres") else []
    user_genres = [g.strip() for g in user_genres if g.strip()]
    
    # Load user ratings to filter out disliked movies
    ratings_file = "data/user_ratings.json"
    user_ratings = {}
    try:
        with open(ratings_file, 'r') as f:
            all_ratings = json.load(f)
            user_ratings = all_ratings.get(email, {})
    except:
        pass
    
    # Get disliked movies (rating = 1)
    disliked_movies = [title for title, data in user_ratings.items() if data.get("rating") == 1]
    
    try:
        # Start with hybrid model recommendations
        rec = None
        try:
            rec = hybrid_model.recommend(user_id=email, top_n=60)  # Get more to filter
        except TypeError:
            try:
                rec = hybrid_model.recommend(user_id=email, n=60)
            except TypeError:
                rec = hybrid_model.recommend(email)
        
        movie_ids = []
        if rec:
            first = rec[0]
            if isinstance(first, (list, tuple)):
                # Extract movie IDs from tuples (movie_id, score)
                for item in rec:
                    movie_ids.append(int(item[0]))
            else:
                # Direct movie IDs
                movie_ids = [int(x) for x in rec]
        
        # Convert movie IDs to titles and filter by user's genres
        titles = []
        for movie_id in movie_ids:
            movie_row = movies_df[movies_df["movieId"] == movie_id]
            if not movie_row.empty:
                title = movie_row.iloc[0]["title"]
                genres = movie_row.iloc[0].get("genres", "")
                
                # If user has genre preferences, prioritize those
                if user_genres:
                    # Check if movie matches any of user's preferred genres
                    if any(ug.lower() in genres.lower() for ug in user_genres):
                        titles.append(title)
                else:
                    titles.append(title)
        
        # Filter out watchlist movies and disliked movies
        filtered_titles = [t for t in titles if t not in user_watchlist and t not in disliked_movies]
        
        # If not enough personalized recommendations, add genre-based ones
        if len(filtered_titles) < 20 and user_genres:
            for genre in user_genres:
                genre_movies = movies_df[movies_df["genres"].str.contains(genre, case=False, na=False)]
                # Get top rated movies from this genre
                genre_ids = genre_movies["movieId"].tolist()
                genre_ratings = ratings_df[ratings_df["movieId"].isin(genre_ids)]
                top_genre_ids = genre_ratings.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(20).index.tolist()
                
                for movie_id in top_genre_ids:
                    movie_row = movies_df[movies_df["movieId"] == movie_id]
                    if not movie_row.empty:
                        title = movie_row.iloc[0]["title"]
                        if title not in filtered_titles and title not in user_watchlist and title not in disliked_movies:
                            filtered_titles.append(title)
                            if len(filtered_titles) >= 30:
                                break
                if len(filtered_titles) >= 30:
                    break
        
        # Fallback to top rated if still not enough
        if not filtered_titles:
            top_ids = ratings_df.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(30).index.tolist()
            all_titles = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()
            filtered_titles = [t for t in all_titles if t not in user_watchlist and t not in disliked_movies]
        
        movies = [{"title": t, "poster": get_poster(t), "reason": "AI Personalized for You"} for t in filtered_titles[:20]]
        return render_template("recommendations.html", recommendations=movies, selected_genre="AI Picks")
    except Exception as e:
        print("❌ AI Picks error:", e)
        import traceback
        traceback.print_exc()
        flash("AI Recommendation temporarily unavailable.")
        return redirect(url_for("choose_genre"))


@app.route("/get_trailer/<path:title>")
def get_trailer(title):
    q = f"{title} trailer"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&q={q}&key={YOUTUBE_API_KEY}"

    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        vid = data["items"][0]["id"]["videoId"] if data.get("items") else None
        return jsonify({"videoId": vid})
    except Exception as e:
        print("TRAILER ERROR:", e)
        return jsonify({"videoId": None})









# ---------------- WATCHLIST ----------------
@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
    email = load_session()
    if not email:
        return jsonify({"status": "error", "message": "Login required"})
    data = request.get_json()
    title = data.get("title")
    wl = load_watchlist()
    wl.setdefault(email, [])
    if title not in wl[email]:
        wl[email].append(title)
    save_watchlist(wl)
    return jsonify({"status": "success", "message": f"{title} added to watchlist"})


@app.route("/remove_from_watchlist", methods=["POST"])
def remove_from_watchlist():
    email = load_session()
    data = request.get_json()
    title = data.get("title")
    wl = load_watchlist()
    if email in wl and title in wl[email]:
        wl[email].remove(title)
        save_watchlist(wl)
    save_watchlist(wl)
    return jsonify({"status": "success", "message": f"{title} removed from watchlist"})


@app.route("/watchlist")
def watchlist():
    email = load_session()
    user = load_users().get(email)
    watchlist_data = load_watchlist().get(email, [])
    movies = [{"title": t, "poster": get_poster(t)} for t in watchlist_data]
    return render_template("watchlist.html", user=user, watchlist=movies)


# ---------------- CHATBOT ----------------
@app.route("/ai_chat", methods=["POST"])
def ai_chat():
    from urllib.parse import quote

    data = request.get_json() or {}
    raw_msg = data.get("message", "")
    query = (raw_msg or "").strip().lower()
    email = load_session()

    # 👋 Auto greeting when chat opens (WITH GENRE BUTTONS)
    if query == "__init__":
        genres_html = """
        <div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>
          <span class='genre-chip' data-genre='Action'>🔥 Action</span>
          <span class='genre-chip' data-genre='Romance'>❤️ Romance</span>
          <span class='genre-chip' data-genre='Comedy'>😂 Comedy</span>
          <span class='genre-chip' data-genre='Thriller'>😱 Thriller</span>
          <span class='genre-chip' data-genre='Sci-Fi'>🚀 Sci-Fi</span>
          <span class='genre-chip' data-genre='Horror'>👻 Horror</span>
          <span class='genre-chip' data-genre='Drama'>🎭 Drama</span>
        </div>
        """
        return jsonify({
            "response": "👋 Hey there! I’m CineSense AI — ready to recommend your next favorite movie!<br><br>Pick a genre👇" 
                        + genres_html
        })

    if not query:
        return jsonify({"response": "🎬 Try saying: 'Recommend a sci-fi movie' or 'Suggest a romance film'."})

    try:
        # ----- helper -----
        def as_movie_items(titles):
            items = []
            for t in titles:
                items.append({
                    "title": t,
                    "poster": get_poster(t),
                    "url": f"/recommend_by_movie/{quote(t)}"
                })
            return items

        all_titles = movies_df["title"].dropna().tolist()
        genre_keywords = {
            "action": "Action", "romance": "Romance", "comedy": "Comedy", "horror": "Horror",
            "drama": "Drama", "sci-fi": "Sci-Fi", "scifi": "Sci-Fi", "science fiction": "Sci-Fi",
            "thriller": "Thriller", "adventure": "Adventure"
        }

        # 🤝 small talk
        if any(x in query for x in ["how are you", "how are u", "how's it going", "hows it going", "what's up", "whats up"]):
            return jsonify({"response": "😊 I’m great and ready to recommend movies! What mood or genre are you in?"})
        if any(x in query for x in ["thank you", "thanks", "thanks a lot"]):
            return jsonify({"response": "🙌 You’re welcome! Want me to pick a genre for you?"})

        time.sleep(0.35)

        # 👋 greetings
        if any(word in query for word in ("hi", "hello", "hey")):
            return jsonify({"response": "👋 Hey there! I’m CineSense AI — ready to recommend your next favorite movie!"})

        # 🎭 Genre intent / general recommendation
        found_genre = next((v for k, v in genre_keywords.items() if k in query), None)
        wants_recs = any(w in query for w in ("recommend", "suggest", "show", "movie", "film", "watch"))

        if wants_recs or found_genre:
            if found_genre:
                try:
                    recs = demo_model.recommend_by_genre(found_genre, movies_df)[:5]
                except:
                    pool = movies_df[movies_df["genres"].str.contains(found_genre, case=False, na=False)]
                    recs = pool["title"].head(5).tolist() if not pool.empty else []
                movies = as_movie_items(recs)
                if movies:
                    return jsonify({
                        "response_type": "movie_list",
                        "message": f"🎭 Here are some **{found_genre}** movies you might enjoy:",
                        "movies": movies
                    })
                return jsonify({"response": f"😕 Couldn't find {found_genre} picks right now. Try another genre?"})
            else:
                rec = None
                try:    rec = hybrid_model.recommend(user_id=email, top_n=5)
                except: rec = hybrid_model.recommend(email)

                titles = []
                if rec:
                    first = rec[0]
                    if isinstance(first, (list, tuple)):
                        titles = [str(a[0]) for a in rec]
                    else:
                        titles = [str(x) for x in rec]

                if not titles:
                    top_ids = ratings_df.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(5).index.tolist()
                    titles = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()

                movies = as_movie_items(titles)
                return jsonify({
                    "response_type": "movie_list",
                    "message": "🎬 Here are some personalized picks for you:",
                    "movies": movies
                })

        # 🎥 Movie title mentioned → similar movies
        from difflib import get_close_matches
        matched_title = next((t for t in all_titles if t.lower() in query), None)
        if not matched_title:
            candidates = get_close_matches(query, [t.lower() for t in all_titles], n=1, cutoff=0.45)
            if candidates:
                lc_to_real = {t.lower(): t for t in all_titles}
                matched_title = lc_to_real.get(candidates[0])

        if matched_title:
            recs = []
            try:
                if hasattr(content_model, "recommend_similar"):
                    recs = content_model.recommend_similar(matched_title, movies_df, top_n=5)
                else:
                    recs = []
            except:
                recs = []

            movies = as_movie_items(recs)
            if movies:
                return jsonify({
                    "response_type": "movie_list",
                    "message": f"🎥 Since you mentioned **{matched_title}**, you might enjoy these:",
                    "movies": movies
                })
            return jsonify({"response": f"😕 Couldn't find similar movies to **{matched_title}** right now."})

        return jsonify({"response": "🤔 Try: 'Recommend me a thriller movie' or 'Suggest something romantic'."})

    except Exception as e:
        print("AI Chat error:", e)
        return jsonify({"response": "😅 Something went wrong. Try again!"})



# ---------------- SEARCH ----------------
@app.route("/search_suggestions")
def search_suggestions():
    """
    Enhanced contextual search with filters:
      - Genre filtering
      - Year range filtering
      - Fuzzy matching
      - Returns detailed movie info with posters
    """
    query = request.args.get("query", "")
    genre_filter = request.args.get("genre", "")
    year_filter = request.args.get("year", "")
    
    if not query:
        return jsonify([])

    q = query.strip().lower()
    if not q:
        return jsonify([])

    # Start with all movies
    filtered_df = movies_df.copy()
    
    # Apply genre filter
    if genre_filter:
        filtered_df = filtered_df[filtered_df["genres"].str.contains(genre_filter, case=False, na=False)]
    
    # Apply year filter
    if year_filter:
        if year_filter == "2020s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(202[0-9])", regex=True, na=False)]
        elif year_filter == "2010s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(201[0-9])", regex=True, na=False)]
        elif year_filter == "2000s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(200[0-9])", regex=True, na=False)]
        elif year_filter == "1990s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(199[0-9])", regex=True, na=False)]
        elif year_filter == "1980s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(198[0-9])", regex=True, na=False)]
        elif year_filter == "1970s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(197[0-9])", regex=True, na=False)]
        elif year_filter == "older":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(19[0-6][0-9])", regex=True, na=False)]
    
    # Search in filtered results
    matches = filtered_df[filtered_df["title"].str.lower().str.contains(q, na=False)]
    
    # Build detailed results
    results = []
    for _, row in matches.head(10).iterrows():
        title = row["title"]
        # Extract year from title
        year_match = re.search(r"\((\d{4})\)", title)
        year = year_match.group(1) if year_match else ""
        
        results.append({
            "title": title,
            "genre": row.get("genres", "Unknown"),
            "year": year,
            "poster": get_poster(title)
        })
    
    # If no exact matches, try fuzzy matching
    if not results:
        all_titles = filtered_df["title"].dropna().tolist()
        fuzzy = get_close_matches(q, [t.lower() for t in all_titles], n=6, cutoff=0.45)
        if fuzzy:
            lc_to_real = {t.lower(): t for t in all_titles}
            for f in fuzzy:
                real = lc_to_real.get(f)
                if real:
                    row = filtered_df[filtered_df["title"] == real].iloc[0]
                    year_match = re.search(r"\((\d{4})\)", real)
                    year = year_match.group(1) if year_match else ""
                    results.append({
                        "title": real,
                        "genre": row.get("genres", "Unknown"),
                        "year": year,
                        "poster": get_poster(real)
                    })
    
    return jsonify(results)


@app.route("/search")
def search_page():
    """
    Full search results page with filters
    """
    query = request.args.get("q", "")
    genre_filter = request.args.get("genre", "")
    year_filter = request.args.get("year", "")
    
    email = load_session()
    users = load_users()
    user = users.get(email) if email else None
    
    if not query:
        flash("Please enter a search query")
        return redirect(url_for("dashboard"))
    
    # Start with all movies
    filtered_df = movies_df.copy()
    
    # Apply genre filter
    if genre_filter:
        filtered_df = filtered_df[filtered_df["genres"].str.contains(genre_filter, case=False, na=False)]
    
    # Apply year filter
    if year_filter:
        if year_filter == "2020s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(202[0-9])", regex=True, na=False)]
        elif year_filter == "2010s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(201[0-9])", regex=True, na=False)]
        elif year_filter == "2000s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(200[0-9])", regex=True, na=False)]
        elif year_filter == "1990s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(199[0-9])", regex=True, na=False)]
        elif year_filter == "1980s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(198[0-9])", regex=True, na=False)]
        elif year_filter == "1970s":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(197[0-9])", regex=True, na=False)]
        elif year_filter == "older":
            filtered_df = filtered_df[filtered_df["title"].str.contains(r"(19[0-6][0-9])", regex=True, na=False)]
    
    # Search in filtered results
    q = query.strip().lower()
    matches = filtered_df[filtered_df["title"].str.lower().str.contains(q, na=False)]
    
    # If no exact matches, try fuzzy
    if matches.empty:
        all_titles = filtered_df["title"].dropna().tolist()
        fuzzy = get_close_matches(q, [t.lower() for t in all_titles], n=50, cutoff=0.4)
        if fuzzy:
            lc_to_real = {t.lower(): t for t in all_titles}
            fuzzy_titles = [lc_to_real.get(f) for f in fuzzy if lc_to_real.get(f)]
            matches = filtered_df[filtered_df["title"].isin(fuzzy_titles)]
    
    # Build results
    results = []
    for _, row in matches.head(50).iterrows():
        title = row["title"]
        results.append({
            "title": title,
            "poster": get_poster(title),
            "reason": f"Search: {query}" + (f" | {genre_filter}" if genre_filter else "") + (f" | {year_filter}" if year_filter else "")
        })
    
    search_title = f"Search: {query}"
    if genre_filter:
        search_title += f" | {genre_filter}"
    if year_filter:
        search_title += f" | {year_filter}"
    
    return render_template("recommendations.html", recommendations=results, user=user, selected_genre=search_title)


# ---------------- RECOMMEND BY MOVIE ----------------
@app.route("/recommend_by_movie/<path:title>")
def recommend_by_movie(title):
    """
    Clicked a movie from search / chat:
      - fuzzy-match the title to the dataset
      - use content_model (multiple method names supported)
      - fallback to popular samples if nothing found
    """
    user_email = load_session()
    users = load_users()
    user = users.get(user_email) if user_email else None

    all_titles = movies_df["title"].dropna().tolist()
    true_title = fuzzy_find(title, all_titles, cutoff=0.45)
    if not true_title:
        flash("Movie not found in database.")
        return redirect(url_for("choose_genre"))

    similar_titles = []
    try:
        if hasattr(content_model, "recommend_similar"):
            similar_titles = content_model.recommend_similar(true_title, movies_df, top_n=12)
        elif hasattr(content_model, "get_similar"):
            try:
                sim = content_model.get_similar(true_title, top_n=12)
                if sim and isinstance(sim[0], (list, tuple)):
                    mids = [s[0] for s in sim]
                    similar_titles = movies_df[movies_df["movieId"].isin(mids)]["title"].tolist()
                else:
                    similar_titles = sim
            except Exception:
                similar_titles = []
        elif hasattr(content_model, "get_similar_by_title"):
            similar_titles = content_model.get_similar_by_title(true_title, top_n=12)
    except Exception as e:
        print("content_model error in recommend_by_movie:", e)
        similar_titles = []

    cleaned = []
    if similar_titles:
        for s in similar_titles:
            if isinstance(s, (list, tuple)) and len(s) >= 1:
                cand = s[0]
            else:
                cand = s
            try:
                if isinstance(cand, int) or (isinstance(cand, str) and cand.isdigit()):
                    mid = int(cand)
                    row = movies_df[movies_df["movieId"] == mid]
                    if not row.empty:
                        cleaned.append(str(row.iloc[0]["title"]))
                else:
                    cleaned.append(str(cand))
            except Exception:
                continue

    if not cleaned:
        top_ids = ratings_df.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(12).index.tolist()
        cleaned = movies_df[movies_df["movieId"].isin(top_ids)]["title"].tolist()

    items = [{
        "title": true_title,
        "poster": get_poster(true_title),
        "score": 1.0,
        "reason": "🎬 You searched this movie"
    }]
    for t in cleaned[:12]:
        if t.lower() == true_title.lower():
            continue
        items.append({
            "title": t,
            "poster": get_poster(t),
            "score": round(random.uniform(0.65, 0.99), 2),
            "reason": f"🎯 Similar to {true_title}"
        })

    return render_template("recommendations.html", recommendations=items, user=user, selected_genre=f"Similar to {true_title}")


@app.route("/get_movie_poster")
def get_movie_poster():
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"poster": "/static/default_poster.png"})
    poster = get_poster(title)
    return jsonify({"poster": poster})


@app.route("/movie_details/<path:title>")
def movie_details(title):
    email = load_session()
    wl = load_watchlist().get(email, [])

    # fuzzy match title
    all_titles = movies_df["title"].dropna().tolist()
    t = fuzzy_find(title, all_titles, cutoff=0.45) or title

    row = movies_df[movies_df["title"].str.lower() == t.lower()]
    desc = "No description available."
    genre = "Unknown"
    rating = "N/A"

    if not row.empty:
        desc = row.iloc[0].get("summary", "No description.")
        genre = row.iloc[0].get("genres", "Unknown")
        mid = row.iloc[0]["movieId"]
        avg = ratings_df[ratings_df["movieId"] == mid]["rating"].mean()
        if avg:
            rating = round(float(avg), 1)

    poster = get_poster(t)
    return jsonify({
        "title": t,
        "description": desc,
        "genre": genre,
        "rating": rating,
        "poster": poster,
        "in_watchlist": t in wl
    })



# ---------------- LIKE/DISLIKE SYSTEM ----------------
@app.route("/rate_movie", methods=["POST"])
def rate_movie():
    """Rate a movie (like=5, dislike=1)"""
    email = load_session()
    if not email:
        return jsonify({"status": "error", "message": "Login required"})
    
    data = request.get_json()
    title = data.get("title")
    rating_value = data.get("rating")  # 5 for like, 1 for dislike
    
    if not title or rating_value not in [1, 5]:
        return jsonify({"status": "error", "message": "Invalid data"})
    
    # Load user ratings
    ratings_file = "data/user_ratings.json"
    try:
        with open(ratings_file, 'r') as f:
            user_ratings = json.load(f)
    except:
        user_ratings = {}
    
    # Initialize user's ratings if not exists
    if email not in user_ratings:
        user_ratings[email] = {}
    
    # Save rating
    user_ratings[email][title] = {
        "rating": rating_value,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to file
    with open(ratings_file, 'w') as f:
        json.dump(user_ratings, f, indent=2)
    
    action = "liked" if rating_value == 5 else "disliked"
    return jsonify({"status": "success", "message": f"You {action} {title}"})


@app.route("/get_user_rating/<path:title>")
def get_user_rating(title):
    """Get user's rating for a movie"""
    email = load_session()
    if not email:
        return jsonify({"rating": None})
    
    ratings_file = "data/user_ratings.json"
    try:
        with open(ratings_file, 'r') as f:
            user_ratings = json.load(f)
        
        if email in user_ratings and title in user_ratings[email]:
            return jsonify({"rating": user_ratings[email][title]["rating"]})
    except:
        pass
    
    return jsonify({"rating": None})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
# Trigger reload 
