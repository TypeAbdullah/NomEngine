import pytest
from app.crawler.deduplication import normalize_url, calculate_sha256, simhash_calculator


def test_url_normalization():
    # Lowercase hostname & strip default port
    assert normalize_url("HTTP://EXAMPLE.COM:80/path/") == "http://example.com/path"
    assert normalize_url("https://EXAMPLE.COM:443/test") == "https://example.com/test"

    # Strip fragments
    assert normalize_url("https://example.com/page#section1") == "https://example.com/page"

    # Strip tracking parameters & sort
    assert normalize_url("https://example.com/search?b=2&utm_source=twitter&a=1") == "https://example.com/search?a=1&b=2"


def test_sha256_exact_deduplication():
    text1 = "This is a document about Python web development."
    text2 = "This is a document about Python web development."
    text3 = "This is a different document."

    hash1 = calculate_sha256(text1)
    hash2 = calculate_sha256(text2)
    hash3 = calculate_sha256(text3)

    assert hash1 == hash2
    assert hash1 != hash3


def test_simhash_near_deduplication():
    text_orig = "Python is a powerful high-level object-oriented programming language designed for readability."
    text_near = "Python is a powerful high-level object-oriented programming language designed for code readability."
    text_diff = "Photosynthesis is the biological process used by plants to convert light energy into chemical energy."

    h_orig = simhash_calculator.calculate_simhash(text_orig)
    h_near = simhash_calculator.calculate_simhash(text_near)
    h_diff = simhash_calculator.calculate_simhash(text_diff)

    dist_near = simhash_calculator.hamming_distance(h_orig, h_near)
    dist_diff = simhash_calculator.hamming_distance(h_orig, h_diff)

    assert dist_near <= 5
    assert dist_diff > 10
    assert simhash_calculator.is_near_duplicate(h_orig, h_near, max_distance=5) is True
