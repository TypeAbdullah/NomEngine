"""
FastAPI Router for Search, Autocomplete, Image/News Search, Stats, and Admin Operations
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from app.api.schemas import (
    AdminStatsResponse,
    CrawlSeedRequest,
    DocumentDetailSchema,
    ImageResultItemSchema,
    ImageSearchResponseSchema,
    NewsResultItemSchema,
    NewsSearchResponseSchema,
    RankingWeightsUpdate,
    SearchResponseSchema,
    SuggestionResponseSchema,
)
from app.api.security import verify_admin_key
from app.cache.redis_cache import cache_service
from app.config.settings import settings
from app.crawler.crawler import crawler_instance
from app.crawler.frontier import frontier
from app.indexing.indexer import indexer
from app.indexing.inverted_index import inverted_index
from app.monitoring.logger import logger
from app.monitoring.metrics import get_metrics_payload
from app.ranking.pagerank import pagerank_calculator
from app.ranking.ranker import ranker
from app.search.engine import search_engine
from app.storage.database import async_session_factory
from app.storage.models import (
    CrawlQueueItem,
    Document,
    ImageDocument,
    NewsArticle,
    PageLink,
    SearchLog,
)

router = APIRouter()


# ---------------------------------------------------------
# Search & Public Endpoints
# ---------------------------------------------------------

@router.get("/search", response_model=SearchResponseSchema)
async def search_endpoint(
    q: str = Query(..., min_length=1, max_length=500, description="Search query string"),
    page: int = Query(default=1, ge=1, le=100),
    limit: int = Query(default=10, ge=1, le=100),
    safe_search: bool = Query(default=True),
):
    """
    Main Search Endpoint:
    Returns ranked search results, highlighted dynamic snippets, total counts, and took_ms latency.
    """
    response = await search_engine.search(
        query_str=q,
        page=page,
        limit=limit,
        safe_search=safe_search,
    )
    return response.to_dict()


@router.get("/suggest", response_model=SuggestionResponseSchema)
async def suggest_endpoint(
    q: str = Query(..., min_length=1, max_length=100, description="Query prefix"),
    limit: int = Query(default=8, ge=1, le=20),
):
    """
    Search Autocomplete & Query Suggestions:
    Returns instant matching queries and indexed terms cached in Redis/memory.
    """
    prefix = q.strip().lower()
    cache_key = f"suggest:{prefix}:{limit}"

    cached = await cache_service.get_json(cache_key, cache_type="suggest")
    if cached:
        return {"query": q, "suggestions": cached}

    # 1. Fetch matching terms from inverted index
    index_terms = inverted_index.get_all_terms(prefix=prefix, limit=limit)

    # 2. Fetch matching past popular queries from SearchLog
    popular_queries: List[str] = []
    try:
        async with async_session_factory() as session:
            q_res = await session.execute(
                select(SearchLog.query)
                .where(SearchLog.normalized_query.startswith(prefix))
                .group_by(SearchLog.normalized_query, SearchLog.query)
                .order_by(func.count(SearchLog.id).desc())
                .limit(limit)
            )
            popular_queries = [row[0] for row in q_res.all()]
    except Exception:
        pass

    # Merge and deduplicate
    combined = list(dict.fromkeys(popular_queries + index_terms))[:limit]

    await cache_service.set_json(cache_key, combined, ttl=settings.CACHE_TTL_SUGGEST)
    return {"query": q, "suggestions": combined}


@router.get("/images", response_model=ImageSearchResponseSchema)
async def search_images(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Image Search tab endpoint."""
    async with async_session_factory() as session:
        query_pattern = f"%{q.strip()}%"
        result = await session.execute(
            select(ImageDocument)
            .where(
                (ImageDocument.alt_text.ilike(query_pattern))
                | (ImageDocument.title.ilike(query_pattern))
                | (ImageDocument.surrounding_text.ilike(query_pattern))
            )
            .limit(limit)
        )
        images = result.scalars().all()
        return {
            "query": q,
            "total": len(images),
            "results": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "page_url": img.page_url,
                    "alt_text": img.alt_text,
                    "title": img.title,
                    "width": img.width,
                    "height": img.height,
                }
                for img in images
            ],
        }


@router.get("/news", response_model=NewsSearchResponseSchema)
async def search_news(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=10, ge=1, le=30),
):
    """News Search tab endpoint sorted by freshness."""
    async with async_session_factory() as session:
        query_pattern = f"%{q.strip()}%"
        result = await session.execute(
            select(NewsArticle, Document)
            .join(Document, NewsArticle.doc_id == Document.id)
            .where(
                (NewsArticle.headline.ilike(query_pattern))
                | (Document.content.ilike(query_pattern))
            )
            .order_by(NewsArticle.published_date.desc())
            .limit(limit)
        )
        items = result.all()

        return {
            "query": q,
            "total": len(items),
            "results": [
                {
                    "id": news.id,
                    "headline": news.headline,
                    "url": doc.url,
                    "publisher": news.publisher,
                    "author": news.author,
                    "published_date": news.published_date.isoformat() if news.published_date else None,
                    "snippet": doc.description or doc.content[:200],
                }
                for news, doc in items
            ],
        }


@router.get("/document/{doc_id}", response_model=DocumentDetailSchema)
async def get_document(doc_id: int):
    """Retrieves full cached document metadata by ID."""
    meta = inverted_index.doc_metadata.get(doc_id)
    if meta:
        return {
            "id": doc_id,
            "url": meta["url"],
            "canonical_url": meta.get("canonical_url"),
            "domain": meta["domain"],
            "title": meta.get("title"),
            "description": meta.get("description"),
            "content": meta.get("content", ""),
            "language": meta.get("language", "en"),
            "word_count": meta.get("word_count", 0),
            "page_rank": meta.get("page_rank", 1.0),
            "spam_score": meta.get("spam_score", 0.0),
            "quality_score": meta.get("quality_score", 1.0),
            "first_seen": None,
            "last_crawled": None,
        }

    async with async_session_factory() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc


@router.get("/stats", response_model=AdminStatsResponse)
async def stats_endpoint():
    """System & Indexing Statistics for Admin Dashboard."""
    async with async_session_factory() as session:
        pages_crawled = await session.scalar(select(func.count(Document.id))) or 0
        pages_indexed = inverted_index.total_docs
        frontier_queue_size = frontier.queue_size
        failed_count = await session.scalar(
            select(func.count(CrawlQueueItem.id)).where(CrawlQueueItem.status == "failed")
        ) or 0
        total_links = await session.scalar(select(func.count(PageLink.id))) or 0
        searches_count = await session.scalar(select(func.count(SearchLog.id))) or 0

        # Top domains
        top_dom_res = await session.execute(
            select(Document.domain, func.count(Document.id).label("cnt"))
            .group_by(Document.domain)
            .order_by(func.count(Document.id).desc())
            .limit(5)
        )
        top_domains = [{"domain": d, "count": c} for d, c in top_dom_res.all()]

        # Recent searches
        recent_res = await session.execute(
            select(SearchLog.query).order_by(SearchLog.timestamp.desc()).limit(10)
        )
        recent_searches = [r[0] for r in recent_res.all()]

        return {
            "pages_indexed": pages_indexed,
            "pages_crawled": pages_crawled,
            "frontier_queue_size": frontier_queue_size,
            "failed_urls_count": failed_count,
            "total_links_graph": total_links,
            "unique_terms_in_index": len(inverted_index.index),
            "searches_recorded": searches_count,
            "crawler_is_running": crawler_instance.is_running,
            "crawler_is_paused": crawler_instance.is_paused,
            "top_domains": top_domains,
            "recent_searches": recent_searches,
        }


@router.get("/health")
async def healthcheck():
    """Service health and liveness probe."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "crawler_running": crawler_instance.is_running,
        "indexed_docs": inverted_index.total_docs,
    }


# ---------------------------------------------------------
# Admin Control Endpoints
# ---------------------------------------------------------

@router.get("/admin/crawler/activity")
async def get_crawler_activity():
    """Returns live streaming crawl events and real-time process activity."""
    return {
        "is_running": crawler_instance.is_running,
        "is_paused": crawler_instance.is_paused,
        "queue_size": frontier.queue_size,
        "activity": crawler_instance.recent_activity[:50],
    }


@router.post("/admin/crawl", dependencies=[Depends(verify_admin_key)])
async def trigger_crawl(payload: CrawlSeedRequest):
    """Adds seed URLs and starts the crawler."""
    await crawler_instance.start(seeds=payload.urls, num_workers=payload.concurrency)
    return {
        "message": f"Crawler started with {len(payload.urls)} seed URLs and {payload.concurrency} workers.",
        "seeds": payload.urls,
    }


@router.post("/admin/pause", dependencies=[Depends(verify_admin_key)])
async def pause_crawler():
    """Pauses the crawler."""
    await crawler_instance.pause()
    return {"message": "Crawler paused."}


@router.post("/admin/resume", dependencies=[Depends(verify_admin_key)])
async def resume_crawler():
    """Resumes the crawler."""
    await crawler_instance.resume()
    return {"message": "Crawler resumed."}


@router.post("/admin/reindex", dependencies=[Depends(verify_admin_key)])
async def trigger_reindex():
    """Forces a full re-index of all database documents."""
    await indexer.load_index_from_db()
    indexed_count = await indexer.index_all_unindexed()
    return {
        "message": "Reindexing completed successfully.",
        "total_indexed": inverted_index.total_docs,
    }


@router.post("/admin/pagerank", dependencies=[Depends(verify_admin_key)])
async def compute_pagerank():
    """Recomputes PageRank across the entire crawled link graph."""
    await pagerank_calculator.update_database_pagerank()
    return {"message": "PageRank recalculation completed."}


@router.get("/admin/ranking-weights", dependencies=[Depends(verify_admin_key)])
async def get_ranking_weights():
    """Returns current ranking weights."""
    return {
        "w_bm25": ranker.w_bm25,
        "w_title": ranker.w_title,
        "w_phrase": ranker.w_phrase,
        "w_pagerank": ranker.w_pagerank,
        "w_freshness": ranker.w_freshness,
        "w_quality": ranker.w_quality,
        "p_spam": ranker.p_spam,
    }


@router.post("/admin/ranking-weights", dependencies=[Depends(verify_admin_key)])
async def update_ranking_weights(weights: RankingWeightsUpdate, dependencies=[Depends(verify_admin_key)]):
    """Updates ranking weights in real time."""
    ranker.update_weights(
        w_bm25=weights.w_bm25,
        w_title=weights.w_title,
        w_phrase=weights.w_phrase,
        w_pagerank=weights.w_pagerank,
        w_freshness=weights.w_freshness,
        w_quality=weights.w_quality,
        p_spam=weights.p_spam,
    )
    return {"message": "Ranking weights updated successfully.", "weights": weights.model_dump(exclude_none=True)}
