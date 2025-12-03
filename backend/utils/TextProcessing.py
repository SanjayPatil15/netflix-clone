"""
Text Processing Module for CineSense
Handles text vectorization and embedding generation for content-based filtering
"""

import numpy as np
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from typing import List


class TextProcessor:
    """
    Process movie plots and descriptions to create embeddings
    for content-based recommendations
    """
    
    def __init__(self, texts: List[str], vector_size: int = 100):
        """
        Initialize text processor
        
        Args:
            texts: List of text documents (movie plots)
            vector_size: Dimension of word embeddings
        """
        self.texts = texts
        self.vector_size = vector_size
        self.word2vec_model = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        # Preprocess texts
        self.processed_texts = [self._preprocess(text) for text in texts]
        self.tokenized_texts = [text.split() for text in self.processed_texts]
    
    def _preprocess(self, text: str) -> str:
        """
        Preprocess text: lowercase, remove special characters
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def train_word2vec(self, min_count: int = 2, window: int = 5, workers: int = 4):
        """
        Train Word2Vec model on the texts
        
        Args:
            min_count: Minimum word frequency
            window: Context window size
            workers: Number of worker threads
        """
        print(f"🔄 Training Word2Vec model (vector_size={self.vector_size})...")
        
        self.word2vec_model = Word2Vec(
            sentences=self.tokenized_texts,
            vector_size=self.vector_size,
            window=window,
            min_count=min_count,
            workers=workers,
            epochs=10
        )
        
        print(f"✅ Word2Vec trained with {len(self.word2vec_model.wv)} words")
    
    def train_tfidf(self, max_features: int = 5000):
        """
        Train TF-IDF vectorizer
        
        Args:
            max_features: Maximum number of features
        """
        print(f"🔄 Training TF-IDF vectorizer (max_features={max_features})...")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2)  # Unigrams and bigrams
        )
        
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.processed_texts)
        
        print(f"✅ TF-IDF trained with {self.tfidf_matrix.shape[1]} features")
    
    def get_word2vec_vectors(self) -> np.ndarray:
        """
        Get Word2Vec document vectors by averaging word vectors
        
        Returns:
            Array of document vectors (n_docs, vector_size)
        """
        if self.word2vec_model is None:
            raise ValueError("Word2Vec model not trained. Call train_word2vec() first.")
        
        doc_vectors = []
        
        for tokens in self.tokenized_texts:
            # Get vectors for words in vocabulary
            word_vectors = []
            for word in tokens:
                if word in self.word2vec_model.wv:
                    word_vectors.append(self.word2vec_model.wv[word])
            
            # Average word vectors to get document vector
            if word_vectors:
                doc_vector = np.mean(word_vectors, axis=0)
            else:
                # If no words in vocabulary, use zero vector
                doc_vector = np.zeros(self.vector_size)
            
            doc_vectors.append(doc_vector)
        
        return np.array(doc_vectors)
    
    def get_tfidf_vectors(self) -> np.ndarray:
        """
        Get TF-IDF vectors
        
        Returns:
            TF-IDF matrix as dense array
        """
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF not trained. Call train_tfidf() first.")
        
        return self.tfidf_matrix.toarray()
    
    def compute_ll_cbow_fusion_vectors(self) -> np.ndarray:
        """
        Compute fused vectors combining Word2Vec and TF-IDF
        This creates a hybrid representation for better content-based filtering
        
        Returns:
            Fused document vectors
        """
        print("🔄 Computing fused vectors (Word2Vec + TF-IDF)...")
        
        # Get Word2Vec vectors
        w2v_vectors = self.get_word2vec_vectors()
        
        # Train and get TF-IDF vectors
        if self.tfidf_matrix is None:
            self.train_tfidf()
        tfidf_vectors = self.get_tfidf_vectors()
        
        # Normalize vectors
        w2v_norm = w2v_vectors / (np.linalg.norm(w2v_vectors, axis=1, keepdims=True) + 1e-10)
        tfidf_norm = tfidf_vectors / (np.linalg.norm(tfidf_vectors, axis=1, keepdims=True) + 1e-10)
        
        # Concatenate normalized vectors
        fused_vectors = np.concatenate([w2v_norm, tfidf_norm], axis=1)
        
        print(f"✅ Fused vectors created: shape {fused_vectors.shape}")
        
        return fused_vectors
    
    def get_simple_vectors(self) -> np.ndarray:
        """
        Get simple averaged Word2Vec vectors (faster alternative)
        
        Returns:
            Document vectors
        """
        if self.word2vec_model is None:
            self.train_word2vec()
        
        return self.get_word2vec_vectors()


# Utility functions for backward compatibility
def create_content_vectors(texts: List[str], method: str = 'fusion') -> np.ndarray:
    """
    Create content vectors from texts
    
    Args:
        texts: List of text documents
        method: 'fusion' for Word2Vec+TF-IDF, 'word2vec' for Word2Vec only
        
    Returns:
        Document vectors
    """
    processor = TextProcessor(texts)
    processor.train_word2vec()
    
    if method == 'fusion':
        return processor.compute_ll_cbow_fusion_vectors()
    else:
        return processor.get_word2vec_vectors()

