"""
Master Search Engine Pipeline
Coordinates query parsing, candidate retrieval, ranking, filters, snippet generation, and caching.
"""
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from app.cache.redis_cache import cache_service
from app.config.settings import settings
from app.indexing.inverted_index import inverted_index
from app.monitoring.logger import logger, log_event
from app.monitoring.metrics import SEARCH_REQUESTS_TOTAL, SEARCH_LATENCY_SECONDS
from app.ranking.ranker import ranker
from app.search.query_parser import query_parser, ParsedQuery
from app.search.snippets import snippet_generator
from app.storage.database import async_session_factory
from app.storage.models import SearchLog


class SearchResultItem:
    """Individual search result item data container."""

    def __init__(
        self,
        doc_id: int,
        title: str,
        url: str,
        display_url: str,
        description: str,
        snippet: str,
        score: float,
        published_at: Optional[str] = None,
        breakdown: Optional[Dict[str, float]] = None,
    ):
        self.doc_id = doc_id
        self.title = title
        self.url = url
        self.display_url = display_url
        self.description = description
        self.snippet = snippet
        self.score = round(score, 2)
        self.published_at = published_at
        self.breakdown = breakdown or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.doc_id,
            "title": self.title,
            "url": self.url,
            "display_url": self.display_url,
            "description": self.description,
            "snippet": self.snippet,
            "score": self.score,
            "published_at": self.published_at,
        }


class SearchResponse:
    """Complete search query response."""

    def __init__(
        self,
        query: str,
        total: int,
        page: int,
        limit: int,
        took_ms: float,
        results: List[SearchResultItem],
        filters: Optional[Dict[str, Any]] = None,
    ):
        self.query = query
        self.total = total
        self.page = page
        self.limit = limit
        self.took_ms = round(took_ms, 2)
        self.results = results
        self.filters = filters or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total": self.total,
            "page": self.page,
            "limit": self.limit,
            "took_ms": self.took_ms,
            "results": [r.to_dict() for r in self.results],
            "filters": self.filters,
        }


class SearchEngine:
    """High-throughput custom search engine."""

    async def search(
        self,
        query_str: str,
        page: int = 1,
        limit: int = 10,
        safe_search: bool = True,
    ) -> SearchResponse:
        """Executes full search pipeline for a given query."""
        start_time = time.perf_counter()
        SEARCH_REQUESTS_TOTAL.inc()

        # Cache key lookup
        cache_key = f"search:{query_str.strip().lower()}:p{page}:l{limit}"
        cached_data = await cache_service.get_json(cache_key, cache_type="search")
        if cached_data:
            cached_data["took_ms"] = round((time.perf_counter() - start_time) * 1000.0, 2)
            results = [
                SearchResultItem(
                    doc_id=item["id"],
                    title=item["title"],
                    url=item["url"],
                    display_url=item["display_url"],
                    description=item["description"],
                    snippet=item["snippet"],
                    score=item["score"],
                    published_at=item.get("published_at"),
                )
                for item in cached_data["results"]
            ]
            return SearchResponse(
                query=cached_data["query"],
                total=cached_data["total"],
                page=cached_data["page"],
                limit=cached_data["limit"],
                took_ms=cached_data["took_ms"],
                results=results,
                filters=cached_data.get("filters", {}),
            )

        # 1. Parse Query into AST
        parsed: ParsedQuery = query_parser.parse(query_str)
        if not parsed.positive_terms and not parsed.raw_positive_terms:
            return SearchResponse(query=query_str, total=0, page=page, limit=limit, took_ms=0.0, results=[])

        # 2. Candidate Document Retrieval
        candidate_doc_ids: Set[int] = set()

        if parsed.is_boolean_or:
            # Boolean OR: Union of candidate postings
            for term in parsed.positive_terms:
                candidate_doc_ids.update(inverted_index.get_postings(term).keys())
        else:
            # Boolean AND / Standard: Union candidates then score, or intersect
            all_term_postings = [
                set(inverted_index.get_postings(term).keys())
                for term in parsed.positive_terms
                if inverted_index.get_postings(term)
            ]
            if all_term_postings:
                # Require document to match at least one term (graded relevance)
                for p_set in all_term_postings:
                    candidate_doc_ids.update(p_set)

        # 3. Apply Filters and Exclusions
        filtered_doc_ids: List[int] = []

        for doc_id in candidate_doc_ids:
            metadata = inverted_index.doc_metadata.get(doc_id)
            if not metadata:
                continue

            # Check Negation (-word)
            if parsed.negative_terms:
                has_neg = any(
                    inverted_index.get_term_frequency(neg_t, doc_id) > 0
                    for neg_t in parsed.negative_terms
                )
                if has_neg:
                    continue

            # Check site: filter
            if parsed.site_filter:
                doc_domain = metadata.get("domain", "").lower()
                if parsed.site_filter not in doc_domain:
                    continue

            # Check intitle: filter
            if parsed.intitle_filter:
                doc_title = metadata.get("title", "").lower()
                if parsed.intitle_filter not in doc_title:
                    continue

            # Check inurl: filter
            if parsed.inurl_filter:
                doc_url = metadata.get("url", "").lower()
                if parsed.inurl_filter not in doc_url:
                    continue

            # Check Date filters
            pub_date_str = metadata.get("published_at")
            if pub_date_str and (parsed.before_date or parsed.after_date):
                try:
                    pub_dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if parsed.before_date and pub_dt > parsed.before_date:
                        continue
                    if parsed.after_date and pub_dt < parsed.after_date:
                        continue
                except Exception:
                    pass

            # SafeSearch filter: reject high spam score
            if safe_search and metadata.get("spam_score", 0.0) > 0.7:
                continue

            filtered_doc_ids.append(doc_id)

        # 4. Multi-Factor Scoring and Ranking
        scored_candidates: List[tuple[int, float, Dict[str, float]]] = []
        for doc_id in filtered_doc_ids:
            score, breakdown = ranker.score_document(
                query_terms=parsed.positive_terms,
                phrase_groups=parsed.exact_phrases,
                doc_id=doc_id,
                index=inverted_index,
            )
            scored_candidates.append((doc_id, score, breakdown))

        # Sort by final score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        total_matches = len(scored_candidates)

        # 5. Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_candidates = scored_candidates[start_idx:end_idx]

        # 6. Snippet Generation
        results: List[SearchResultItem] = []
        all_highlight_terms = parsed.raw_positive_terms or parsed.positive_terms

        for doc_id, score, breakdown in paged_candidates:
            meta = inverted_index.doc_metadata.get(doc_id, {})
            url = meta.get("url", "")
            domain = meta.get("domain", "")
            title = meta.get("title") or url
            desc = meta.get("description") or ""
            content = meta.get("content") or desc

            snippet = snippet_generator.generate_snippet(
                text=content or desc,
                query_terms=all_highlight_terms,
                exact_phrases=parsed.raw_exact_phrases,
            )

            # Clean display URL (e.g. example.com > path)
            display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

            results.append(
                SearchResultItem(
                    doc_id=doc_id,
                    title=title,
                    url=url,
                    display_url=display_url,
                    description=desc,
                    snippet=snippet,
                    score=score,
                    published_at=meta.get("published_at"),
                    breakdown=breakdown,
                )
            )

        latency_s = time.perf_counter() - start_time
        took_ms = latency_s * 1000.0
        SEARCH_LATENCY_SECONDS.observe(latency_s)

        response = SearchResponse(
            query=query_str,
            total=total_matches,
            page=page,
            limit=limit,
            took_ms=took_ms,
            results=results,
            filters={
                "site": parsed.site_filter,
                "intitle": parsed.intitle_filter,
                "inurl": parsed.inurl_filter,
                "exact_phrases": parsed.raw_exact_phrases,
            },
        )

        # Save to Cache
        await cache_service.set_json(
            cache_key, response.to_dict(), ttl=settings.CACHE_TTL_SEARCH
        )

        # Record Search Log in background
        asyncio.create_task(self._log_search(query_str, total_matches, took_ms))

        return response

    async def _log_search(self, query: str, results_count: int, latency_ms: float):
        """Asynchronously persists search query telemetry."""
        try:
            async with async_session_factory() as session:
                log_entry = SearchLog(
                    query=query,
                    normalized_query=query.strip().lower(),
                    results_count=results_count,
                    latency_ms=latency_ms,
                )
                session.add(log_entry)
                await session.commit()
        except Exception:
            pass


search_engine = SearchEngine()
