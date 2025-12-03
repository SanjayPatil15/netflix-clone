class DemographicRecommender:
    """
    IEEE-Compliant Demographic Similarity Model using PSO-optimized weights:
    L1 (Age) = 0.31, L2 (Gender) = 0.27, L3 (Genre Preferences) = 0.42  (Equation 19)
    """

    # ✅ Fixed IEEE Weights (from paper, optimized by PSO)
    L1 = 0.31  # Age
    L2 = 0.27  # Gender
    L3 = 0.42  # Genre Preference

    def __init__(self, users_df, ratings_df, movies_df):
        self.users_df = users_df
        self.ratings_df = ratings_df
        self.movies_df = movies_df
        self.user_profiles = {}

    # ---------------- BUILD USER PROFILES ----------------
    def build_user_profiles(self):
        for user_id in self.users_df["userId"]:
            liked_movie_ids = self._get_liked_movies(user_id)
            liked_genres = self._get_liked_genres(liked_movie_ids)
            profile = {
                "liked_genres": liked_genres,
                "age": self._get_user_age(user_id),
                "gender": self._get_user_gender(user_id),
            }
            self.user_profiles[user_id] = profile

    # ---------------- INTERNAL HELPERS ----------------
    def _get_liked_movies(self, user_id):
        user_ratings = self.ratings_df[self.ratings_df["userId"] == user_id]
        return user_ratings[user_ratings["rating"] >= 4.0]["movieId"].tolist()

    def _get_liked_genres(self, movie_ids):
        genres = []
        for movie_id in movie_ids:
            row = self.movies_df[self.movies_df["movieId"] == movie_id]
            if not row.empty:
                genres += row.iloc[0]["genres"].split("|")
        return genres

    def _get_user_age(self, user_id):
        row = self.users_df[self.users_df["userId"] == user_id]
        return int(row.iloc[0]["age"]) if not row.empty else 0

    def _get_user_gender(self, user_id):
        row = self.users_df[self.users_df["userId"] == user_id]
        return row.iloc[0]["gender"] if not row.empty else "M"

    # ---------------- SIMILARITY (IEEE FORMULA) ----------------
    def _compute_similarity(self, userA, userB):
        age_sim = max(0, 1 - abs(userA["age"] - userB["age"]) / 50)  # Age closeness factor
        gender_sim = 1 if userA["gender"] == userB["gender"] else 0
        genre_overlap = len(set(userA["liked_genres"]) & set(userB["liked_genres"]))
        genre_sim = genre_overlap / max(len(set(userA["liked_genres"])), 1)

        # 🎯 IEEE Weight Integration
        return (
            (self.L1 * age_sim) +
            (self.L2 * gender_sim) +
            (self.L3 * genre_sim)
        )

    # ---------------- RECOMMENDATION BY SIMILAR USERS ----------------
    def recommend_by_similarity(self, user_id, top_n=10):
        if user_id not in self.user_profiles:
            return []

        target_profile = self.user_profiles[user_id]
        similarities = {}

        # Compute similarity with all other users using IEEE weights
        for other_id, profile in self.user_profiles.items():
            if other_id == user_id:
                continue
            similarities[other_id] = self._compute_similarity(target_profile, profile)

        # Pick top similar users
        top_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get movies liked by them
        candidate_movies = {}
        for uid, _ in top_users:
            user_ratings = self.ratings_df[self.ratings_df["userId"] == uid]
            high_rated = user_ratings[user_ratings["rating"] >= 4.0]["movieId"].tolist()
            for mid in high_rated:
                candidate_movies[mid] = candidate_movies.get(mid, 0) + 1

        # Sort by popularity among similar users
        recommended_ids = sorted(candidate_movies.items(), key=lambda x: x[1], reverse=True)
        return [movie_id for movie_id, _ in recommended_ids[:top_n]]

    # ---------------- ✅ FIXED: GENRE-BASED RECOMMENDER ----------------
    def recommend_by_genre(self, genre, movies_df, limit=20):
        """
        Simple fallback for genre-based recommendations.
        Filters movies by the given genre and returns top titles.
        """
        genre = genre.lower()
        filtered = movies_df[movies_df["genres"].str.lower().str.contains(genre, na=False)]
        if "rating" in filtered.columns:
            filtered = filtered.sort_values("rating", ascending=False)
        return filtered["title"].head(limit).tolist()
