"""
Pydantic Schemas for API Requests and Responses
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResultItemSchema(BaseModel):
    id: int
    title: str
    url: str
    display_url: str
    description: Optional[str] = ""
    snippet: str
    score: float
    published_at: Optional[str] = None


class SearchResponseSchema(BaseModel):
    query: str
    total: int
    page: int
    limit: int
    took_ms: float
    results: List[SearchResultItemSchema]
    filters: Optional[Dict[str, Any]] = None


class SuggestionResponseSchema(BaseModel):
    query: str
    suggestions: List[str]


class ImageResultItemSchema(BaseModel):
    id: int
    image_url: str
    page_url: str
    alt_text: Optional[str] = ""
    title: Optional[str] = ""
    width: Optional[int] = None
    height: Optional[int] = None


class ImageSearchResponseSchema(BaseModel):
    query: str
    total: int
    results: List[ImageResultItemSchema]


class NewsResultItemSchema(BaseModel):
    id: int
    headline: str
    url: str
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    snippet: str


class NewsSearchResponseSchema(BaseModel):
    query: str
    total: int
    results: List[NewsResultItemSchema]


class DocumentDetailSchema(BaseModel):
    id: int
    url: str
    canonical_url: Optional[str] = None
    domain: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: str
    language: Optional[str] = None
    word_count: int
    page_rank: float
    spam_score: float
    quality_score: float
    first_seen: Optional[datetime] = None
    last_crawled: Optional[datetime] = None


class AdminStatsResponse(BaseModel):
    pages_indexed: int
    pages_crawled: int
    frontier_queue_size: int
    failed_urls_count: int
    total_links_graph: int
    unique_terms_in_index: int
    searches_recorded: int
    crawler_is_running: bool
    crawler_is_paused: bool
    top_domains: List[Dict[str, Any]]
    recent_searches: List[str]


class CrawlSeedRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1, description="List of seed URLs to crawl")
    priority: int = Field(default=100, ge=1, le=100)
    concurrency: int = Field(default=5, ge=1, le=50)


class RankingWeightsUpdate(BaseModel):
    w_bm25: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    w_title: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    w_phrase: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    w_pagerank: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    w_freshness: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    w_quality: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    p_spam: Optional[float] = Field(default=None, ge=0.0, le=2.0)
