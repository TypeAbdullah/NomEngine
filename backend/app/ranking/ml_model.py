"""
Extensible Machine Learning / Learning-to-Rank (LTR) Interface
Provides abstract base and default heuristic ranker that can be swapped for XGBoost / Neural models.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RankingModel(ABC):
    """Abstract interface for modern ML ranking models."""

    @abstractmethod
    def extract_features(
        self, query: str, doc_metadata: Dict[str, Any], lexical_score: float
    ) -> List[float]:
        """Extracts dense feature vector for a (query, document) pair."""
        pass

    @abstractmethod
    def predict(self, feature_vector: List[float]) -> float:
        """Scores relevance from feature vector."""
        pass


class DefaultLinearRankingModel(RankingModel):
    """
    Default linear feature combination model.
    Serves as the foundation and template for future ML/GBDT model weights.
    """

    def extract_features(
        self, query: str, doc_metadata: Dict[str, Any], lexical_score: float
    ) -> List[float]:
        word_count = doc_metadata.get("word_count", 0)
        page_rank = doc_metadata.get("page_rank", 1.0)
        spam_score = doc_metadata.get("spam_score", 0.0)
        quality_score = doc_metadata.get("quality_score", 1.0)

        # Feature vector:
        # [0] Lexical BM25
        # [1] PageRank
        # [2] Quality
        # [3] Spam Penalty
        # [4] Content Length (log scale)
        return [
            float(lexical_score),
            float(page_rank),
            float(quality_score),
            float(spam_score),
            min(10.0, word_count / 500.0),
        ]

    def predict(self, feature_vector: List[float]) -> float:
        weights = [0.45, 0.20, 0.15, -0.30, 0.10]
        score = sum(w * f for w, f in zip(weights, feature_vector))
        return max(0.0, score)


default_ml_ranker = DefaultLinearRankingModel()
