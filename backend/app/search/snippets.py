"""
Dynamic Passage and Snippet Generator
Extracts the highest-relevance window containing matched query terms and applies highlight markup.
"""
import re
from typing import List, Set


class SnippetGenerator:
    """Generates relevant highlighted snippet passages from document text."""

    def __init__(self, target_length: int = 240):
        self.target_length = target_length

    def generate_snippet(
        self,
        text: str,
        query_terms: List[str],
        exact_phrases: List[str] | None = None,
    ) -> str:
        """
        Extracts a concise, relevant passage surrounding matched query terms.
        """
        if not text:
            return ""

        clean_text = re.sub(r"\s+", " ", text).strip()
        if len(clean_text) <= self.target_length:
            return self.highlight(clean_text, query_terms, exact_phrases)

        sentences = re.split(r"(?<=[.!?])\s+", clean_text)
        if not sentences:
            sentences = [clean_text]

        # Score sentences by term matches
        best_sentence_idx = 0
        best_score = -1.0
        terms_set = {t.lower() for t in query_terms if len(t) > 1}

        for idx, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            match_count = sum(1 for term in terms_set if term in sentence_lower)
            if exact_phrases:
                for phrase in exact_phrases:
                    if phrase.lower() in sentence_lower:
                        match_count += 3

            score = match_count / (len(sentence) ** 0.3) if len(sentence) > 0 else 0
            if score > best_score:
                best_score = score
                best_sentence_idx = idx

        # Assemble passage window around best sentence
        passage_parts = [sentences[best_sentence_idx]]
        curr_len = len(sentences[best_sentence_idx])

        # Add subsequent sentences if room permits
        next_idx = best_sentence_idx + 1
        while next_idx < len(sentences) and curr_len + len(sentences[next_idx]) < self.target_length:
            passage_parts.append(sentences[next_idx])
            curr_len += len(sentences[next_idx])
            next_idx += 1

        passage = " ".join(passage_parts)

        # Prepend/append ellipsis if truncated
        prefix = "... " if best_sentence_idx > 0 else ""
        suffix = " ..." if next_idx < len(sentences) else ""
        full_snippet = f"{prefix}{passage}{suffix}"

        return self.highlight(full_snippet, query_terms, exact_phrases)

    def highlight(
        self,
        text: str,
        query_terms: List[str],
        exact_phrases: List[str] | None = None,
    ) -> str:
        """Highlights matching query terms with <b>...</b> tags."""
        highlighted = text

        # 1. Highlight exact phrases first
        if exact_phrases:
            for phrase in exact_phrases:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                highlighted = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", highlighted)

        # 2. Highlight individual positive terms
        for term in query_terms:
            if len(term) <= 1:
                continue
            pattern = re.compile(rf"\b({re.escape(term)})\b", re.IGNORECASE)
            highlighted = pattern.sub(r"<b>\1</b>", highlighted)

        return highlighted


snippet_generator = SnippetGenerator()
