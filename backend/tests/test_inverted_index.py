import pytest
from app.indexing.inverted_index import InvertedIndex
from app.indexing.text_processor import text_processor


def test_inverted_index_insertion_and_lookup():
    index = InvertedIndex()
    tokens1 = text_processor.tokenize_with_positions("Python is a dynamic programming language")
    tokens2 = text_processor.tokenize_with_positions("Dynamic web applications with Python and FastAPI")

    index.add_document(1, tokens1, {"title": "Doc 1", "url": "https://example.com/1"})
    index.add_document(2, tokens2, {"title": "Doc 2", "url": "https://example.com/2"})

    assert index.total_docs == 2
    assert index.get_document_frequency("python") == 2
    assert index.get_term_frequency("python", 1) == 1
    assert index.get_term_frequency("python", 2) == 1


def test_phrase_verification():
    index = InvertedIndex()
    # Sentence with "fast web framework" at consecutive positions
    text = "Building a fast web framework in Python"
    tokens = text_processor.tokenize_with_positions(text)
    index.add_document(1, tokens)

    # Valid contiguous phrase
    phrase_terms = [term for term, _ in text_processor.tokenize_with_positions("fast web framework")]
    assert index.verify_phrase(phrase_terms, 1) is True

    # Non-contiguous phrase
    non_phrase_terms = [term for term, _ in text_processor.tokenize_with_positions("fast framework")]
    assert index.verify_phrase(non_phrase_terms, 1) is False
