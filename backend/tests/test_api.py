import pytest
from httpx import AsyncClient, ASGITransport
from app.indexing.inverted_index import inverted_index
from app.indexing.text_processor import text_processor
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_index():
    inverted_index.clear()
    tokens = text_processor.tokenize_with_positions(
        "Python is a high-level programming language with easy syntax and rich libraries."
    )
    inverted_index.add_document(
        doc_id=1,
        tokens_with_positions=tokens,
        metadata={
            "id": 1,
            "url": "https://www.python.org",
            "domain": "python.org",
            "title": "Welcome to Python.org",
            "description": "The official home of the Python Programming Language.",
            "content": "Python is a high-level programming language with easy syntax and rich libraries.",
            "published_at": "2026-01-01T00:00:00",
            "page_rank": 2.5,
            "spam_score": 0.0,
            "quality_score": 1.5,
            "word_count": 12,
        },
    )


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_search_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/search?q=python")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "Welcome to Python.org" in data["results"][0]["title"]
        assert "<b>Python</b>" in data["results"][0]["snippet"]


@pytest.mark.asyncio
async def test_autocomplete_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/suggest?q=py")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert any("py" in s.lower() for s in data["suggestions"])
