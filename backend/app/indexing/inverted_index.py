"""
Positional Inverted Index Data Structure
Supports positional postings, phrase verification, document frequency lookups, and BM25 parameter calculations.
"""
import math
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


class PositionalPosting:
    """Posting entry storing term frequency and exact positions in a document."""

    __slots__ = ("doc_id", "term_freq", "positions")

    def __init__(self, doc_id: int, positions: List[int]):
        self.doc_id = doc_id
        self.term_freq = len(positions)
        self.positions = positions


class InvertedIndex:
    """
    High-performance Positional Inverted Index.
    term -> {doc_id: PositionalPosting}
    """

    def __init__(self):
        # term -> {doc_id: PositionalPosting}
        self.index: Dict[str, Dict[int, PositionalPosting]] = defaultdict(dict)
        # doc_id -> total word count in doc
        self.doc_lengths: Dict[int, int] = {}
        # doc_id -> cached metadata dictionary
        self.doc_metadata: Dict[int, dict] = {}
        self.total_docs: int = 0
        self.total_terms: int = 0

    @property
    def avg_doc_length(self) -> float:
        if self.total_docs == 0:
            return 1.0
        return sum(self.doc_lengths.values()) / self.total_docs

    def add_document(
        self,
        doc_id: int,
        tokens_with_positions: List[Tuple[str, int]],
        metadata: Optional[dict] = None,
    ):
        """Indexes a document with term positions and metadata."""
        if doc_id in self.doc_lengths:
            self.remove_document(doc_id)

        term_positions: Dict[str, List[int]] = defaultdict(list)
        for term, pos in tokens_with_positions:
            term_positions[term].append(pos)

        doc_len = len(tokens_with_positions)
        self.doc_lengths[doc_id] = doc_len
        self.total_docs += 1

        if metadata:
            self.doc_metadata[doc_id] = metadata

        for term, positions in term_positions.items():
            posting = PositionalPosting(doc_id=doc_id, positions=positions)
            self.index[term][doc_id] = posting

    def remove_document(self, doc_id: int):
        """Removes a document from all posting lists."""
        if doc_id not in self.doc_lengths:
            return

        del self.doc_lengths[doc_id]
        self.doc_metadata.pop(doc_id, None)
        self.total_docs -= 1

        terms_to_clean = []
        for term, postings_map in self.index.items():
            if doc_id in postings_map:
                del postings_map[doc_id]
                if not postings_map:
                    terms_to_clean.append(term)

        for term in terms_to_clean:
            del self.index[term]

    def get_postings(self, term: str) -> Dict[int, PositionalPosting]:
        """Returns the document postings map for a given term."""
        return self.index.get(term, {})

    def get_document_frequency(self, term: str) -> int:
        """Returns the number of documents containing the term (DF)."""
        return len(self.index.get(term, {}))

    def get_term_frequency(self, term: str, doc_id: int) -> int:
        """Returns how many times term appears in doc_id (TF)."""
        posting = self.index.get(term, {}).get(doc_id)
        return posting.term_freq if posting else 0

    def verify_phrase(self, terms: List[str], doc_id: int) -> bool:
        """
        Verifies if an ordered sequence of terms appears adjacently in doc_id.
        Example: terms = ["python", "web", "framework"]
        """
        if not terms:
            return False

        postings = [self.index.get(t, {}).get(doc_id) for t in terms]
        if any(p is None for p in postings):
            return False

        # Check for consecutive positions: pos[i] == pos[i-1] + 1
        first_positions = postings[0].positions
        for start_pos in first_positions:
            match = True
            for offset in range(1, len(terms)):
                expected_pos = start_pos + offset
                if expected_pos not in postings[offset].positions:
                    match = False
                    break
            if match:
                return True

        return False

    def count_phrase_occurrences(self, terms: List[str], doc_id: int) -> int:
        """Counts how many times an exact phrase appears in doc_id."""
        if not terms:
            return 0

        postings = [self.index.get(t, {}).get(doc_id) for t in terms]
        if any(p is None for p in postings):
            return 0

        count = 0
        first_positions = postings[0].positions
        for start_pos in first_positions:
            match = True
            for offset in range(1, len(terms)):
                if (start_pos + offset) not in postings[offset].positions:
                    match = False
                    break
            if match:
                count += 1
        return count

    def get_all_terms(self, prefix: str = "", limit: int = 10) -> List[str]:
        """Returns matching terms for autocomplete / search suggestions."""
        prefix_lower = prefix.lower()
        matches = [
            t for t in self.index.keys()
            if t.startswith(prefix_lower)
        ]
        # Sort by document frequency descending
        matches.sort(key=lambda t: len(self.index[t]), reverse=True)
        return matches[:limit]

    def clear(self):
        """Resets the inverted index."""
        self.index.clear()
        self.doc_lengths.clear()
        self.doc_metadata.clear()
        self.total_docs = 0


inverted_index = InvertedIndex()
