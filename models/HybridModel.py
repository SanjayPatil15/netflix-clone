import numpy as np

class HybridRecommender:
    """
    Combines ALS, Content, and Demographic recommenders.
    """

    def __init__(self, als_model, content_model, demo_model, weights=(0.4, 0.3, 0.3)):
        self.als_model = als_model
        self.content_model = content_model
        self.demo_model = demo_model
        self.weights = weights  # (ALS, Content, Demographic)

    def recommend(self, user_id, top_n=10, user_ratings=None, **kwargs):
        """
        Returns hybrid recommendations using weighted average from three models.
        Flexible to accept both `top_n` or `n`.
        """

        # If called with `n`, use that
        if "n" in kwargs:
            top_n = kwargs["n"]

        als_recs = []
        content_recs = []
        demo_recs = []

        # ✅ ALS model
        try:
            als_recs = self.als_model.recommend(user_id, top_n=top_n)
        except Exception as e:
            print(f"[WARN] ALS recommend failed: {e}")

        # ✅ Content model
        try:
            if user_ratings:
                liked_titles = [title for title, r in user_ratings.items() if r >= 4]
                for title in liked_titles:
                    similar = self.content_model.recommend_similar(title, top_n=3)
                    content_recs.extend(similar)
        except Exception as e:
            print(f"[WARN] Content recommend failed: {e}")

        # ✅ Demographic model
        try:
            demo_recs = self.demo_model.recommend_by_similarity(user_id, top_n=top_n)
        except Exception as e:
            print(f"[WARN] Demo recommend failed: {e}")

        # Combine all results
        combined = {}
        for rec_list, weight in zip([als_recs, content_recs, demo_recs], self.weights):
            for movie_id in rec_list:
                combined[movie_id] = combined.get(movie_id, 0) + weight

        # Sort and return final top recommendations
        final_sorted = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return final_sorted[:top_n]

