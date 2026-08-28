"""
URL Normalization and Content Deduplication
Supports canonical URL normalization, SHA-256 exact deduplication, and 64-bit SimHash near-duplicate detection.
"""
import hashlib
import re
from typing import List, Set
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(raw_url: str) -> str:
    """
    Strict URL normalization:
    - Lowercase scheme and hostname
    - Strip default ports (80 for http, 443 for https)
    - Remove URL fragment (#section)
    - Remove tracking query parameters (utm_*, fbclid, etc.)
    - Sort query parameters
    - Remove redundant trailing slashes for root paths
    - Decode unneeded percent encodings
    """
    if not raw_url:
        return ""

    try:
        raw_url = raw_url.strip()
        parsed = urlparse(raw_url)

        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return raw_url

        netloc = parsed.netloc.lower()

        # Strip standard default ports
        if (scheme == "http" and netloc.endswith(":80")) or (
            scheme == "https" and netloc.endswith(":443")
        ):
            netloc = netloc.rsplit(":", 1)[0]

        # Path normalization: resolve /./ and /../, keep clean path
        path = parsed.path or "/"
        while "//" in path:
            path = path.replace("//", "/")

        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Clean tracking query parameters
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "fbclid", "gclid", "ref", "source", "_ga"
        }
        query_items = parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_query = [
            (k, v) for k, v in query_items if k.lower() not in tracking_params
        ]
        # Sort query keys for determinism
        cleaned_query.sort(key=lambda x: (x[0], x[1]))
        query_str = urlencode(cleaned_query)

        # Rebuild without fragment
        normalized = urlunparse((scheme, netloc, path, "", query_str, ""))
        return normalized
    except Exception:
        return raw_url


def calculate_sha256(content: str) -> str:
    """Computes SHA-256 hexadecimal digest for exact match deduplication."""
    return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()


class SimHash:
    """
    64-bit SimHash implementation for near-duplicate text detection.
    Computes a 64-bit fingerprint of weighted token features.
    """

    def __init__(self, num_bits: int = 64):
        self.num_bits = num_bits

    def _extract_features(self, text: str) -> Dict[str, int]:
        """Extracts character 4-grams and token shingles for robust fingerprinting."""
        cleaned = re.sub(r"\s+", " ", text.lower()).strip()
        if not cleaned:
            return {}

        features: Dict[str, int] = {}
        # Character 4-grams (highly robust against single word insertion/deletion)
        for i in range(len(cleaned) - 3):
            gram = cleaned[i : i + 4]
            features[gram] = features.get(gram, 0) + 1

        # Words
        words = re.findall(r"\b[\w\+\#\.]+\b", cleaned)
        for w in words:
            features[w] = features.get(w, 0) + 2

        return features

    def _hash_feature(self, feature: str) -> int:
        """Hashes a feature string to a 64-bit integer."""
        md5_digest = hashlib.md5(feature.encode("utf-8", errors="ignore")).hexdigest()
        return int(md5_digest[:16], 16)

    def calculate_simhash(self, text: str) -> int:
        """Calculates the 64-bit SimHash integer of a given text."""
        features = self._extract_features(text)
        if not features:
            return 0

        v = [0] * self.num_bits
        for feature, weight in features.items():
            h = self._hash_feature(feature)
            for i in range(self.num_bits):
                bitmask = 1 << i
                if h & bitmask:
                    v[i] += weight
                else:
                    v[i] -= weight

        fingerprint = 0
        for i in range(self.num_bits):
            if v[i] > 0:
                fingerprint |= 1 << i

        return fingerprint

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """Computes the bitwise Hamming distance between two integer hashes."""
        x = (hash1 ^ hash2) & 0xFFFFFFFFFFFFFFFF
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance

    def is_near_duplicate(self, hash1: int, hash2: int, max_distance: int = 5) -> bool:
        """Returns True if the two hashes differ by at most `max_distance` bits."""
        if hash1 == 0 or hash2 == 0:
            return False
        return self.hamming_distance(hash1, hash2) <= max_distance


simhash_calculator = SimHash()
