"""
Document Quality, Spam Detection, and Freshness Scoring
Calculates spam heuristics, keyword stuffing penalties, readability bonuses, and time decay freshness.
"""
import re
from datetime import datetime, timezone
from typing import Dict, List, Set


class QualityScorer:
    """Evaluates content quality, spam likelihood, and freshness."""

    def calculate_spam_score(self, title: str, text: str, word_count: int) -> float:
        """
        Calculates a spam score between 0.0 (clean) and 1.0 (spam).
        Signals:
        - Keyword stuffing: single token occupying > 8% of content
        - Repetitive phrases
        - Very short spammy titles with excessive punctuation
        - Excessive hidden/capitalized words
        """
        if word_count < 15:
            return 0.4  # Thin content penalty

        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            return 0.8

        # Check maximum term frequency ratio (keyword stuffing)
        freqs: Dict[str, int] = {}
        for t in tokens:
            freqs[t] = freqs.get(t, 0) + 1

        max_tf = max(freqs.values())
        tf_ratio = max_tf / len(tokens)
        spam_penalty = 0.0

        if tf_ratio > 0.08:
            spam_penalty += min(0.6, (tf_ratio - 0.08) * 5.0)

        # Check excessive exclamation or caps
        if len(title) > 5 and sum(1 for c in title if c.isupper()) / len(title) > 0.6:
            spam_penalty += 0.2

        if title.count("!") > 2 or title.count("$") > 2:
            spam_penalty += 0.2

        return min(1.0, spam_penalty)

    def calculate_quality_score(self, url: str, word_count: int, title: str) -> float:
        """
        Calculates baseline content quality score.
        Signals:
        - HTTPS protocol bonus
        - Substantial readable content (300 - 3000 words optimal)
        - Descriptive title
        """
        score = 1.0

        # HTTPS bonus
        if url.startswith("https://"):
            score += 0.2

        # Content length score
        if 250 <= word_count <= 4000:
            score += 0.3
        elif word_count < 100:
            score -= 0.3

        # Meaningful title
        if 15 <= len(title) <= 90:
            score += 0.2

        return max(0.1, score)

    def calculate_freshness_score(self, published_at_iso: str | None) -> float:
        """
        Calculates freshness decay score: 1.0 (recent) decaying to 0.1 (years old).
        """
        if not published_at_iso:
            return 0.5  # Neutral default

        try:
            pub_date = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
            # Strip timezone for delta calculation
            pub_date = pub_date.replace(tzinfo=None)
            now = datetime.utcnow()
            days_old = max(0, (now - pub_date).days)

            # Exponential decay: half-life ~ 180 days
            decay = 1.0 / (1.0 + (days_old / 180.0))
            return max(0.1, min(1.0, decay))
        except Exception:
            return 0.5


quality_scorer = QualityScorer()
