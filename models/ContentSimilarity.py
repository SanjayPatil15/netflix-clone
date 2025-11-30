import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    """
    Memory-efficient content-based recommender using on-demand cosine similarity.
    """

    def __init__(self, vectors, movie_ids, top_k=100):
        self.vectors = np.array(vectors)
        self.movie_ids = movie_ids
        self.top_k = top_k
        print(f"✅ Content model initialized with {len(movie_ids)} movies")

    def recommend_similar(self, title, movies_df, top_n=10):
        """
        Recommend similar movies for a given title using cosine similarity.
        Computed on-demand to save RAM.
        """
        # Find index of the movie
        idx = movies_df[movies_df["title"].str.lower() == title.lower()].index
        if len(idx) == 0:
            print(f"⚠️ Movie not found: {title}")
            return []

        idx = idx[0]

        # Compute similarity only for that movie vector
        movie_vec = self.vectors[idx].reshape(1, -1)
        sim_scores = cosine_similarity(movie_vec, self.vectors)[0]

        # Get top similar movie indices
        similar_idx = sim_scores.argsort()[-top_n-1:][::-1]
        similar_titles = [
            movies_df.iloc[i]["title"]
            for i in similar_idx
            if i != idx
        ][:top_n]

        print(f"🎯 Found {len(similar_titles)} similar to {title}")
        return similar_titles
