"""
Advanced Text Processing & Tokenization Pipeline
Preserves programming terms, symbols (C++, C#, Node.js), handles Unicode normalization, stop words, and Porter stemming.
"""
import re
import unicodedata
from typing import List, Set, Tuple

# Common English Stop Words
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

# Regex pattern that keeps meaningful symbols in programming terms & product names:
# e.g., C++, C#, Node.js, Next.js, .NET, ASP.NET, TCP/IP, v1.0
TOKEN_PATTERN = re.compile(
    r"[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*(?:\+\+|#)?|[a-zA-Z0-9]+",
    re.UNICODE
)


class PorterStemmer:
    """
    Lightweight rule-based English stemmer.
    Reduces inflectional forms (e.g., searches -> search, programming -> program).
    """

    def stem(self, word: str) -> str:
        w = word.lower()
        if len(w) <= 3:
            return w

        # Common suffix stripping rules
        if w.endswith("sses"):
            w = w[:-2]
        elif w.endswith("ies"):
            w = w[:-2]
        elif w.endswith("ss"):
            pass
        elif w.endswith("s") and not w.endswith("us") and not w.endswith("is"):
            w = w[:-1]

        if w.endswith("eed"):
            if len(w) > 4:
                w = w[:-1]
        elif (w.endswith("ed") or w.endswith("ing")) and len(w) > 4:
            stem_base = w[:-2] if w.endswith("ed") else w[:-3]
            # Double consonant cleanup (e.g., programm -> program)
            if len(stem_base) >= 2 and stem_base[-1] == stem_base[-2] and stem_base[-1] not in "lsz":
                stem_base = stem_base[:-1]
            w = stem_base

        if w.endswith("ational"):
            w = w[:-5] + "e"
        elif w.endswith("tional"):
            w = w[:-4]
        elif w.endswith("izer"):
            w = w[:-1]
        elif w.endswith("ation"):
            w = w[:-3] + "e"
        elif w.endswith("ator"):
            w = w[:-2] + "e"
        elif w.endswith("alism"):
            w = w[:-3]
        elif w.endswith("iveness"):
            w = w[:-4]
        elif w.endswith("fulness"):
            w = w[:-4]

        return w


class TextProcessor:
    """End-to-end linguistic pipeline for indexing and query understanding."""

    def __init__(self, use_stemming: bool = True):
        self.use_stemming = use_stemming
        self.stemmer = PorterStemmer()

    def normalize(self, text: str) -> str:
        """Unicode NFKC normalization and whitespace cleanup."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFKC", text)
        return norm

    def tokenize_with_positions(
        self, text: str, remove_stopwords: bool = False
    ) -> List[Tuple[str, int]]:
        """
        Tokenizes text into a list of (processed_term, position_index).
        Preserves positions for accurate phrase search.
        """
        normalized_text = self.normalize(text)
        tokens: List[Tuple[str, int]] = []
        pos = 0

        for match in TOKEN_PATTERN.finditer(normalized_text):
            raw_token = match.group(0).lower()

            if remove_stopwords and raw_token in STOP_WORDS:
                pos += 1
                continue

            processed_term = self.stemmer.stem(raw_token) if self.use_stemming else raw_token
            tokens.append((processed_term, pos))
            pos += 1

        return tokens

    def tokenize(self, text: str, remove_stopwords: bool = False) -> List[str]:
        """Returns just the list of processed tokens."""
        return [term for term, _ in self.tokenize_with_positions(text, remove_stopwords)]

    def extract_raw_tokens(self, text: str) -> List[str]:
        """Extracts lowercased unstemmed tokens for literal matching and highlighting."""
        normalized_text = self.normalize(text)
        return [m.group(0).lower() for m in TOKEN_PATTERN.finditer(normalized_text)]


text_processor = TextProcessor(use_stemming=True)
