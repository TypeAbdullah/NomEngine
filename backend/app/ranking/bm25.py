"""
Okapi BM25 Scoring Algorithm
Calculates term saturation and document length normalized relevance scores.
"""
import math
from typing import Dict, List
from app.indexing.inverted_index import InvertedIndex


class BM25Scorer:
    """Okapi BM25 ranking algorithm."""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def idf(self, doc_freq: int, total_docs: int) -> float:
        """
        Calculates Inverse Document Frequency with smoothing:
        IDF(q_i) = ln( 1 + (N - n(q_i) + 0.5) / (n(q_i) + 0.5) )
        """
        if total_docs == 0:
            return 0.0
        return math.log(1.0 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def score(
        self,
        query_terms: List[str],
        doc_id: int,
        index: InvertedIndex,
    ) -> float:
        """Computes total BM25 score for a document given query terms."""
        total_docs = index.total_docs
        if total_docs == 0:
            return 0.0

        doc_len = index.doc_lengths.get(doc_id, 0)
        avg_doc_len = index.avg_doc_length

        # Length normalization factor
        len_norm = 1.0 - self.b + self.b * (doc_len / avg_doc_len) if avg_doc_len > 0 else 1.0

        score = 0.0
        for term in query_terms:
            df = index.get_document_frequency(term)
            if df == 0:
                continue

            tf = index.get_term_frequency(term, doc_id)
            if tf == 0:
                continue

            term_idf = self.idf(df, total_docs)
            term_score = term_idf * ((tf * (self.k1 + 1.0)) / (tf + self.k1 * len_norm))
            score += term_score

        return score


bm25_scorer = BM25Scorer()
