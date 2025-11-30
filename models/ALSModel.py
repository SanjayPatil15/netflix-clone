import numpy as np
from scipy.sparse import coo_matrix
from implicit.als import AlternatingLeastSquares


class ALSRecommender:
    def __init__(self, factors=50, regularization=0.1, iterations=20):
        self.model = AlternatingLeastSquares(
            factors=factors, regularization=regularization, iterations=iterations
        )
        self.user_map = {}
        self.item_map = {}
        self.user_inv_map = {}
        self.item_inv_map = {}
        self.user_item_matrix = None  # Store the matrix

    def prepare_matrix(self, ratings):
        # Encode user and item ids
        self.user_map = {uid: idx for idx, uid in enumerate(ratings["userId"].unique())}
        self.item_map = {
            iid: idx for idx, iid in enumerate(ratings["movieId"].unique())
        }
        self.user_inv_map = {idx: uid for uid, idx in self.user_map.items()}
        self.item_inv_map = {idx: iid for iid, idx in self.item_map.items()}

        rows = ratings["userId"].map(self.user_map).values
        cols = ratings["movieId"].map(self.item_map).values
        data = ratings["rating"].values.astype(np.float32)

        user_item_matrix = coo_matrix(
            (data, (rows, cols)), shape=(len(self.user_map), len(self.item_map))
        )
        return user_item_matrix

    def train(self, ratings):
        self.user_item_matrix = self.prepare_matrix(ratings)
        self.model.fit(self.user_item_matrix.tocsr())

    def recommend(self, user_id, N=10):
        if user_id not in self.user_map:
            return []

        user_index = self.user_map[user_id]
        user_items_csr = self.user_item_matrix.tocsr()

        recommended = self.model.recommend(
            user_index, user_items_csr, N=N, filter_already_liked_items=False
        )

        movie_ids = [self.item_inv_map[idx] for idx in recommended[0]]
        scores = recommended[1]
        return list(zip(movie_ids, scores))
