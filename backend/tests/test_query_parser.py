import pytest
from app.search.query_parser import query_parser


def test_basic_query_parsing():
    pq = query_parser.parse("python web framework")
    assert len(pq.positive_terms) == 3
    assert "python" in pq.positive_terms
    assert pq.exact_phrases == []
    assert pq.negative_terms == []


def test_exact_phrase_parsing():
    pq = query_parser.parse('"machine learning" tutorial')
    assert len(pq.raw_exact_phrases) == 1
    assert pq.raw_exact_phrases[0] == "machine learning"
    assert len(pq.exact_phrases) == 1
    assert "tutori" in pq.positive_terms or "tutorial" in pq.positive_terms


def test_negation_and_field_filters():
    pq = query_parser.parse("python -django site:python.org before:2026-01-01")
    assert "django" in pq.negative_terms
    assert pq.site_filter == "python.org"
    assert pq.before_date is not None
    assert pq.before_date.year == 2026


def test_technical_terms_preservation():
    pq = query_parser.parse("C++ Next.js Node.js C#")
    assert any("c++" in t.lower() for t in pq.raw_positive_terms)
    assert any("next.js" in t.lower() for t in pq.raw_positive_terms)
