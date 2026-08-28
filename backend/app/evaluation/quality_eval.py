"""
Information Retrieval (IR) Ranking Evaluation Framework
Calculates Precision@K, Recall@K, MRR, and NDCG against relevance judgments.
"""
import math
from typing import Dict, List, Set, Tuple
from app.search.engine import search_engine


# Standard evaluation test queries and gold-standard ground-truth URLs / relevant patterns
BENCHMARK_JUDGMENTS: Dict[str, Dict[str, int]] = {
    "python": {
        "python.org": 3,
        "docs.python.org": 3,
        "en.wikipedia.org/wiki/Python": 2,
        "pypi.org": 2,
    },
    "python web framework": {
        "djangoproject.com": 3,
        "palletsprojects.com/p/flask": 3,
        "fastapi.tiangolo.com": 3,
    },
    "machine learning": {
        "scikit-learn.org": 3,
        "tensorflow.org": 3,
        "pytorch.org": 3,
    },
    "best programming language": {
        "tiobe.com": 2,
        "python.org": 2,
        "rust-lang.org": 2,
    },
}


class RankingEvaluator:
    """Evaluates search engine precision, recall, MRR, and NDCG."""

    @staticmethod
    def precision_at_k(retrieved_urls: List[str], relevance_map: Dict[str, int], k: int = 10) -> float:
        """Calculates fraction of top-K results that are relevant."""
        top_k = retrieved_urls[:k]
        if not top_k:
            return 0.0

        relevant_count = sum(
            1 for url in top_k
            if any(pattern in url for pattern, rel in relevance_map.items() if rel > 0)
        )
        return relevant_count / min(k, len(top_k))

    @staticmethod
    def reciprocal_rank(retrieved_urls: List[str], relevance_map: Dict[str, int]) -> float:
        """Calculates 1 / rank of the first relevant result."""
        for rank, url in enumerate(retrieved_urls, start=1):
            if any(pattern in url for pattern, rel in relevance_map.items() if rel > 0):
                return 1.0 / rank
        return 0.0

    @staticmethod
    def dcg_at_k(retrieved_urls: List[str], relevance_map: Dict[str, int], k: int = 10) -> float:
        """Calculates Discounted Cumulative Gain at K."""
        dcg = 0.0
        for i, url in enumerate(retrieved_urls[:k], start=1):
            rel = 0
            for pattern, score in relevance_map.items():
                if pattern in url:
                    rel = max(rel, score)
            dcg += (2.0 ** rel - 1.0) / math.log2(i + 1.0)
        return dcg

    @classmethod
    def ndcg_at_k(cls, retrieved_urls: List[str], relevance_map: Dict[str, int], k: int = 10) -> float:
        """Calculates Normalized Discounted Cumulative Gain at K."""
        actual_dcg = cls.dcg_at_k(retrieved_urls, relevance_map, k)

        # Ideal ranking
        ideal_rels = sorted(relevance_map.values(), reverse=True)[:k]
        idcg = sum((2.0 ** rel - 1.0) / math.log2(i + 1.0) for i, rel in enumerate(ideal_rels, start=1))

        if idcg == 0.0:
            return 1.0 if actual_dcg == 0.0 else 0.0
        return actual_dcg / idcg

    async def run_evaluation(self, k: int = 5) -> Dict[str, float]:
        """Runs evaluation over benchmark dataset and returns aggregate metrics."""
        p_at_k_list = []
        mrr_list = []
        ndcg_list = []

        for query_str, rel_map in BENCHMARK_JUDGMENTS.items():
            resp = await search_engine.search(query_str=query_str, limit=k)
            retrieved = [item.url for item in resp.results]

            p = self.precision_at_k(retrieved, rel_map, k=k)
            rr = self.reciprocal_rank(retrieved, rel_map)
            ndcg = self.ndcg_at_k(retrieved, rel_map, k=k)

            p_at_k_list.append(p)
            mrr_list.append(rr)
            ndcg_list.append(ndcg)

        count = len(BENCHMARK_JUDGMENTS)
        return {
            f"Precision@{k}": round(sum(p_at_k_list) / count, 4) if count else 0.0,
            "MRR": round(sum(mrr_list) / count, 4) if count else 0.0,
            f"NDCG@{k}": round(sum(ndcg_list) / count, 4) if count else 0.0,
        }


evaluator = RankingEvaluator()
