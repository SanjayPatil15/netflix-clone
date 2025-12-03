# 🎬 CineSense - AI-Powered Movie Recommender

A Netflix-style movie recommendation system powered by machine learning, featuring hybrid recommendations, advanced search, and an interactive AI chatbot.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🤖 **Hybrid AI Recommendations** - Combines collaborative filtering, content-based, and demographic filtering
- 🔍 **Advanced Search** - Multi-filter search with fuzzy matching and autocomplete
- 💬 **AI Chatbot** - Interactive movie recommendations via natural language
- 📊 **Personalized Dashboard** - Netflix-style UI with genre carousels
- ❤️ **Watchlist Management** - Save and organize your favorite movies
- 🎥 **Movie Details Modal** - View trailers, ratings, and similar movies
- 🔐 **User Authentication** - Secure login/signup with Gmail OTP verification
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd movie_recommender
```

2. **Create and activate virtual environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
python setup_database.py
```
This will:
- Create SQLite database at `data/cinesense.db`
- Migrate MovieLens dataset (1684 movies, 100K+ ratings)
- Create indexes for performance

5. **Train ML models** (First time only, takes 2-5 minutes)
```bash
python main.py
```
This will:
- Train ALS collaborative filtering model
- Generate content-based similarity vectors (Word2Vec + TF-IDF)
- Cache models in `model_cache/`

6. **Run the application**
```bash
python app.py
```

7. **Access the application**
```
http://localhost:5000
```

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   HTML/CSS   │  │  JavaScript  │  │    Jinja2    │      │
│  │  (Netflix UI)│  │   (Modal,    │  │  Templates   │      │
│  │              │  │   Search)    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      Flask Application                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routes: Auth, Dashboard, Search, Recommendations    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                       Backend Services                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Search     │  │Recommendation│  │     Auth     │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      ML Models Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  ALS Model   │  │   Content    │  │ Demographics │      │
│  │(Collaborative│  │  Similarity  │  │    Model     │      │
│  │  Filtering)  │  │ (Word2Vec +  │  │              │      │
│  │              │  │   TF-IDF)    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                            ↓                                 │
│                  ┌──────────────────┐                        │
│                  │  Hybrid Model    │                        │
│                  │ (Weighted Combo) │                        │
│                  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SQLite Database (SQLAlchemy ORM)                    │   │
│  │  - Users, Movies, Ratings, Watchlist, SearchHistory  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```
![1764522225477](utils/README/1764522225477.png)

### Directory Structure

```
movie_recommender/
├── app.py                    # Main Flask application
├── main.py                   # ML model training script
├── setup_database.py         # Database initialization
├── requirements.txt          # Python dependencies
│
├── backend/                  # Backend code
│   ├── database/            # Database layer
│   │   ├── config.py        # DB configuration
│   │   ├── models.py        # SQLAlchemy models
│   │   └── migrate_data.py  # Data migration
│   ├── models/              # ML models
│   │   ├── ALSModel.py      # Collaborative filtering
│   │   ├── ContentSimilarity.py  # Content-based
│   │   ├── DemographicsModel.py  # Demographic filtering
│   │   └── HybridModel.py   # Hybrid recommendations
│   └── utils/               # Utilities
│       ├── DataLoader.py    # Data loading
│       ├── auth.py          # Authentication
│       ├── search_service.py      # Search functionality
│       ├── recommendation_service.py  # Recommendations
│       └── TextProcessing.py      # NLP processing
│
├── frontend/                # Frontend code
│   ├── templates/          # HTML templates
│   │   ├── base.html       # Base template
│   │   ├── dashboard.html  # Main dashboard
│   │   ├── login.html      # Login page
│   │   ├── signup.html     # Registration
│   │   └── ...             # Other templates
│   └── static/             # Static assets
│       ├── css/            # Stylesheets
│       ├── posters/        # Movie posters (1600+)
│       └── genre_posters/  # Genre images
│
├── data/                    # Data files
│   ├── cinesense.db        # SQLite database
│   ├── movielens/          # MovieLens dataset
│   └── wikipedia/          # Wikipedia movie data
│
├── model_cache/             # Cached ML models
│   ├── als_model.pkl       # Trained ALS model
│   └── content_vectors.pkl # Content vectors
│
└── scripts/                 # Utility scripts
    ├── poster_generation/  # Poster generation
    ├── data_conversion/    # Data conversion
    └── archive/            # Archived scripts
```

## 🛠️ Tech Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM for database operations
- **SQLite** - Lightweight database with WAL mode
- **Flask-Mail** - Email integration for OTP

### Machine Learning
- **scikit-learn** - Machine learning algorithms
- **implicit** - ALS collaborative filtering
- **gensim** - Word2Vec for text embeddings
- **scipy** - Sparse matrix operations
- **pandas & numpy** - Data manipulation

### Frontend
- **Jinja2** - Template engine
- **HTML5/CSS3** - Modern web standards
- **JavaScript** - Interactive features
- **Netflix-style UI** - Dark theme with carousels

### APIs & Services
- **YouTube Data API** - Trailer integration
- **Gmail SMTP** - OTP email delivery

## 🔄 Application Flow

### 1. User Registration/Login Flow
```
User → Signup Form → Email Validation → OTP Verification → Dashboard
                                    ↓
                            Store in Database
```

### 2. Movie Recommendation Flow
```
User Profile → Hybrid Model → [ALS (40%) + Content (30%) + Demographics (30%)]
                                              ↓
                                    Personalized Recommendations
```

### 3. Search Flow
```
Search Query → Search Service → [Fuzzy Matching + Genre Filter + Year Filter]
                                              ↓
                                    Filtered Results with Posters
```

### 4. AI Chatbot Flow
```
User Message → Intent Detection → [Genre Request / Movie Mention / General Query]
                                              ↓
                                    Contextual Recommendations
```

## 🤖 ML Models Explained

### 1. ALS (Alternating Least Squares) - Collaborative Filtering
- **Purpose**: Finds patterns in user-movie interactions
- **Weight**: 40% in hybrid model
- **Algorithm**: Matrix factorization using implicit feedback
- **Training Data**: 100,000+ user ratings

### 2. Content-Based Filtering
- **Purpose**: Recommends similar movies based on content
- **Weight**: 30% in hybrid model
- **Features**: 
  - Word2Vec embeddings (100 dimensions)
  - TF-IDF vectors (5000 features)
  - Combined into 5100-dimensional vectors
- **Training Data**: Movie plots from Wikipedia

### 3. Demographic Filtering
- **Purpose**: Recommends based on user demographics
- **Weight**: 30% in hybrid model
- **Features**: Age, gender, preferred genre
- **Method**: Weighted average of similar users' ratings

### 4. Hybrid Model
- **Purpose**: Combines all three approaches
- **Method**: Weighted linear combination
- **Weights**: Configurable (default: 0.4, 0.3, 0.3)
- **Output**: Top-N personalized recommendations

## 📊 Database Schema

```sql
Users
├── id (PK)
├── email (unique)
├── name
├── password
├── age
├── gender
├── preferred_genre
└── created_at

Movies
├── id (PK)
├── movie_id (unique)
├── title
├── genres
├── year
├── summary
├── avg_rating
└── rating_count

Ratings
├── id (PK)
├── user_id (FK)
├── movie_id (FK)
├── rating
└── timestamp

Watchlist
├── id (PK)
├── user_id (FK)
├── movie_id (FK)
└── added_at

SearchHistory
├── id (PK)
├── user_id (FK)
├── query
└── searched_at
```

## 🔍 Key Features Explained

### Advanced Search
- **Multi-filter**: Genre, year range, minimum rating
- **Fuzzy matching**: Finds movies even with typos
- **Autocomplete**: Real-time suggestions
- **Sort options**: Relevance, rating, year

### AI Chatbot
- **Natural language**: Understands conversational queries
- **Genre detection**: Automatically detects genre requests
- **Movie similarity**: Finds similar movies when you mention one
- **Context-aware**: Remembers conversation context

### Watchlist
- **Quick add/remove**: One-click watchlist management
- **Persistent**: Stored in database
- **Visual feedback**: Instant UI updates

## 🎨 UI/UX Features

- **Netflix-style Design**: Dark theme with red accents
- **Responsive Layout**: Works on all screen sizes
- **Smooth Animations**: Hover effects and transitions
- **Movie Carousels**: Horizontal scrolling for genres
- **Modal Details**: Full-screen movie information
- **Trailer Integration**: Watch trailers without leaving the app

## 🔐 Security Features

- **Password Hashing**: Secure password storage
- **OTP Verification**: Gmail-based two-factor authentication
- **Session Management**: Secure session handling
- **Input Validation**: Prevents SQL injection and XSS
- **CSRF Protection**: Flask built-in protection

## 📈 Performance Optimizations

- **Database Indexing**: Optimized queries with indexes
- **Model Caching**: Pre-trained models loaded once
- **Connection Pooling**: Efficient database connections
- **Static File Caching**: Browser caching for assets
- **Lazy Loading**: Images loaded on demand

## 🧪 Testing

Run the database tests:
```bash
python test_database.py
```

This will verify:
- Database connection
- Movie queries
- Search functionality
- Recommendation service
- User operations

## 📝 Configuration

### Email Configuration (app.py)
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

### API Keys (app.py)
```python
YOUTUBE_API_KEY = 'your-youtube-api-key'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **MovieLens Dataset**: GroupLens Research
- **Wikipedia**: Movie plot summaries
- **Flask Community**: Web framework
- **scikit-learn**: Machine learning library

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using Flask, SQLAlchemy, and Machine Learning**