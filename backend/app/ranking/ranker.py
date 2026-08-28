"""
Multi-Factor Relevance Ranker
Combines BM25 lexical relevance, Title matching, Exact Phrase adjacency, PageRank authority, Freshness, and Spam penalties.
"""
from typing import Dict, List, Tuple
from app.config.settings import settings
from app.indexing.inverted_index import InvertedIndex
from app.ranking.bm25 import bm25_scorer
from app.ranking.quality import quality_scorer


class RelevanceRanker:
    """Combines multiple ranking signals into a final score."""

    def __init__(self):
        self.w_bm25 = settings.WEIGHT_BM25
        self.w_title = settings.WEIGHT_TITLE
        self.w_phrase = settings.WEIGHT_PHRASE
        self.w_pagerank = settings.WEIGHT_PAGERANK
        self.w_freshness = settings.WEIGHT_FRESHNESS
        self.w_quality = settings.WEIGHT_QUALITY
        self.p_spam = settings.PENALTY_SPAM

    def update_weights(
        self,
        w_bm25: float = None,
        w_title: float = None,
        w_phrase: float = None,
        w_pagerank: float = None,
        w_freshness: float = None,
        w_quality: float = None,
        p_spam: float = None,
    ):
        """Allows dynamic real-time tuning of ranking weights from Admin UI."""
        if w_bm25 is not None: self.w_bm25 = w_bm25
        if w_title is not None: self.w_title = w_title
        if w_phrase is not None: self.w_phrase = w_phrase
        if w_pagerank is not None: self.w_pagerank = w_pagerank
        if w_freshness is not None: self.w_freshness = w_freshness
        if w_quality is not None: self.w_quality = w_quality
        if p_spam is not None: self.p_spam = p_spam

    def score_document(
        self,
        query_terms: List[str],
        phrase_groups: List[List[str]],
        doc_id: int,
        index: InvertedIndex,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates the composite relevance score and detailed signal breakdown.
        """
        metadata = index.doc_metadata.get(doc_id, {})
        title = metadata.get("title", "").lower()
        published_at = metadata.get("published_at")
        page_rank = float(metadata.get("page_rank", 1.0))
        spam_score = float(metadata.get("spam_score", 0.0))
        quality_score = float(metadata.get("quality_score", 1.0))

        # 1. BM25 Lexical Score
        bm25_val = bm25_scorer.score(query_terms, doc_id, index)

        # 2. Title Match Bonus
        title_matches = sum(1 for t in query_terms if t in title)
        title_score = (title_matches / len(query_terms)) * 5.0 if query_terms else 0.0

        # 3. Exact Phrase Adjacency Bonus
        phrase_score = 0.0
        for phrase_terms in phrase_groups:
            if index.verify_phrase(phrase_terms, doc_id):
                phrase_score += 4.0

        # 4. PageRank Link Authority (log damped)
        pagerank_score = min(5.0, page_rank)

        # 5. Freshness Score
        freshness_score = quality_scorer.calculate_freshness_score(published_at) * 2.0

        # 6. Quality Score
        quality_val = quality_score * 2.0

        # 7. Spam Penalty
        spam_penalty = spam_score * 10.0

        # Weighted composite score
        total_score = (
            (self.w_bm25 * bm25_val)
            + (self.w_title * title_score)
            + (self.w_phrase * phrase_score)
            + (self.w_pagerank * pagerank_score)
            + (self.w_freshness * freshness_score)
            + (self.w_quality * quality_val)
            - (self.p_spam * spam_penalty)
        )

        breakdown = {
            "bm25": round(bm25_val, 3),
            "title": round(title_score, 3),
            "phrase": round(phrase_score, 3),
            "pagerank": round(pagerank_score, 3),
            "freshness": round(freshness_score, 3),
            "quality": round(quality_val, 3),
            "spam_penalty": round(spam_penalty, 3),
        }

        return max(0.01, total_score), breakdown


ranker = RelevanceRanker()
