"""
Advanced Search Query Parser
Parses search queries into an Abstract Syntax Tree (AST) supporting exact phrases, field filters, negations, and booleans.
"""
import re
from datetime import datetime
from typing import List, Optional, Set
from app.indexing.text_processor import text_processor


class ParsedQuery:
    """Structured representation of a parsed search query."""

    def __init__(self):
        self.raw_query: str = ""
        self.positive_terms: List[str] = []         # Stemmed terms to match
        self.raw_positive_terms: List[str] = []     # Unstemmed terms for exact/snippet
        self.negative_terms: List[str] = []         # Terms that must NOT appear (-word)
        self.exact_phrases: List[List[str]] = []    # Ordered stemmed phrase lists
        self.raw_exact_phrases: List[str] = []      # Raw phrase strings
        self.site_filter: Optional[str] = None      # site:example.com
        self.intitle_filter: Optional[str] = None   # intitle:word
        self.inurl_filter: Optional[str] = None     # inurl:api
        self.filetype_filter: Optional[str] = None  # filetype:pdf
        self.before_date: Optional[datetime] = None # before:2026-01-01
        self.after_date: Optional[datetime] = None  # after:2025-01-01
        self.is_boolean_or: bool = False            # term1 OR term2


class QueryParser:
    """Parses user input query strings into structured ParsedQuery objects."""

    def parse(self, query_str: str) -> ParsedQuery:
        pq = ParsedQuery()
        if not query_str:
            return pq

        pq.raw_query = query_str.strip()
        remaining = pq.raw_query

        # 1. Detect Boolean OR
        if " OR " in remaining:
            pq.is_boolean_or = True

        # 2. Extract Exact Phrases: "python web framework"
        phrase_matches = re.findall(r'"([^"]+)"', remaining)
        for phrase in phrase_matches:
            pq.raw_exact_phrases.append(phrase.strip())
            stemmed_phrase = text_processor.tokenize(phrase, remove_stopwords=False)
            if stemmed_phrase:
                pq.exact_phrases.append(stemmed_phrase)
                # Also include phrase terms in positive terms
                for t in stemmed_phrase:
                    if t not in pq.positive_terms:
                        pq.positive_terms.append(t)
        # Remove matched phrases from query string
        remaining = re.sub(r'"([^"]+)"', ' ', remaining)

        # 3. Extract Field Filters (site:, intitle:, inurl:, filetype:, before:, after:)
        tokens = remaining.split()
        unhandled_tokens = []

        for token in tokens:
            token_lower = token.lower()

            if token_lower.startswith("site:") and len(token) > 5:
                pq.site_filter = token[5:].strip().lower()
            elif token_lower.startswith("intitle:") and len(token) > 8:
                pq.intitle_filter = token[8:].strip().lower()
            elif token_lower.startswith("inurl:") and len(token) > 6:
                pq.inurl_filter = token[6:].strip().lower()
            elif token_lower.startswith("filetype:") and len(token) > 9:
                pq.filetype_filter = token[9:].strip().lower()
            elif token_lower.startswith("before:") and len(token) > 7:
                try:
                    pq.before_date = datetime.strptime(token[7:].strip(), "%Y-%m-%d")
                except ValueError:
                    pass
            elif token_lower.startswith("after:") and len(token) > 6:
                try:
                    pq.after_date = datetime.strptime(token[6:].strip(), "%Y-%m-%d")
                except ValueError:
                    pass
            elif token.startswith("-") and len(token) > 1:
                # Negated term: -javascript
                neg_raw = token[1:].strip()
                neg_stemmed = text_processor.tokenize(neg_raw)
                if neg_stemmed:
                    pq.negative_terms.extend(neg_stemmed)
            elif token_lower in ("and", "or"):
                continue  # Skip boolean keywords in term list
            else:
                unhandled_tokens.append(token)

        # 4. Process remaining positive terms
        remaining_text = " ".join(unhandled_tokens)
        raw_tokens = text_processor.extract_raw_tokens(remaining_text)
        stemmed_tokens = text_processor.tokenize(remaining_text, remove_stopwords=False)

        for raw_t in raw_tokens:
            if raw_t not in pq.raw_positive_terms:
                pq.raw_positive_terms.append(raw_t)

        for st_t in stemmed_tokens:
            if st_t not in pq.positive_terms:
                pq.positive_terms.append(st_t)

        return pq


query_parser = QueryParser()
