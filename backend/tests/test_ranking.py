import pytest
from app.indexing.inverted_index import InvertedIndex
from app.indexing.text_processor import text_processor
from app.ranking.bm25 import bm25_scorer
from app.ranking.pagerank import pagerank_calculator
from app.ranking.ranker import ranker


def test_bm25_relevance_scoring():
    index = InvertedIndex()
    doc1 = text_processor.tokenize_with_positions("Python language documentation tutorial and guides")
    doc2 = text_processor.tokenize_with_positions("Rust programming language syntax and features")

    index.add_document(1, doc1, {"title": "Python Docs", "url": "https://python.org"})
    index.add_document(2, doc2, {"title": "Rust Docs", "url": "https://rust-lang.org"})

    score1 = bm25_scorer.score(["python"], 1, index)
    score2 = bm25_scorer.score(["python"], 2, index)

    assert score1 > 0
    assert score2 == 0
    assert score1 > score2


def test_pagerank_computation():
    nodes = {"https://a.com", "https://b.com", "https://c.com"}
    # A -> B, A -> C, B -> C, C -> A
    edges = [
        ("https://a.com", "https://b.com"),
        ("https://a.com", "https://c.com"),
        ("https://b.com", "https://c.com"),
        ("https://c.com", "https://a.com"),
    ]

    ranks = pagerank_calculator.compute(nodes, edges)

    assert len(ranks) == 3
    # Node C has 2 inbound links (from A and B) so it should have the highest PageRank
    assert ranks["https://c.com"] > ranks["https://b.com"]
