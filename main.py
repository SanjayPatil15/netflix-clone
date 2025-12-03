# -*- coding: utf-8 -*-
import pandas as pd
import pickle
import os
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from backend.utils.DataLoader import DataLoader
from backend.utils.TextProcessing import TextProcessor
from backend.models.ALSModel import ALSRecommender

# Cache Paths
CACHE_DIR = "model_cache"
ALS_CACHE = os.path.join(CACHE_DIR, "als_model.pkl")
CONTENT_CACHE = os.path.join(CACHE_DIR, "content_vectors.pkl")

os.makedirs(CACHE_DIR, exist_ok=True)

def main():
    print("\nTRAIN MODE (One-Time AI Setup)...")

    # ✅ Load dataset
    loader = DataLoader("data/movielens", "data/wikipedia")
    ratings_df = loader.load_ratings_data()
    movies_df = loader.load_movies_data()
    
    # Load Wikipedia plots with error handling
    try:
        wiki_df = loader.load_wikipedia_data()
        if not wiki_df.empty and 'Plot' in wiki_df.columns:
            wiki_plots = wiki_df["Plot"].fillna("").tolist()
        else:
            print("⚠️ Wikipedia data not available, using movie summaries from database")
            wiki_plots = movies_df.get("summary", pd.Series([""] * len(movies_df))).fillna("").tolist()
    except Exception as e:
        print(f"⚠️ Could not load Wikipedia plots: {e}")
        print("   Using movie summaries from database instead")
        wiki_plots = movies_df.get("summary", pd.Series([""] * len(movies_df))).fillna("").tolist()
    
    # Ensure we have enough plots
    if len(wiki_plots) < len(movies_df):
        # Pad with empty strings if needed
        wiki_plots.extend([""] * (len(movies_df) - len(wiki_plots)))
    elif len(wiki_plots) > len(movies_df):
        # Trim if too many
        wiki_plots = wiki_plots[:len(movies_df)]

    # ✅ Step 1: ALS Model Train/Load
    if os.path.exists(ALS_CACHE):
        print("⚡ ALS Model already cached → Skipping training.")
    else:
        print("🚀 Training ALS Model (First Time Only)...")
        als_model = ALSRecommender()
        als_model.train(ratings_df)
        pickle.dump(als_model, open(ALS_CACHE, "wb"))
        print("✅ ALS Model Cached at model_cache/als_model.pkl")

    # ✅ Step 2: Fast Content Fusion Train/Load
    if os.path.exists(CONTENT_CACHE):
        print("⚡ Content Embeddings already cached → Skipping processing.")
    else:
        print("🔄 Generating Fast AI Content Embeddings...")
        processor = TextProcessor(wiki_plots)
        processor.train_word2vec()
        fused_vectors = processor.compute_ll_cbow_fusion_vectors()
        pickle.dump(fused_vectors, open(CONTENT_CACHE, "wb"))
        print("✅ Content Embeddings Saved at model_cache/content_vectors.pkl")

    print("\n✅ AI Engine Fully Prepared!")
    print("🚀 NEXT: Run >>> python app.py <<< to launch Netflix-Style Web App FAST.")

if __name__ == "__main__":
    main()
