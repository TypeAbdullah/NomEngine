from app.monitoring.logger import logger, log_event
from app.monitoring.metrics import (
    CRAWL_REQUESTS_TOTAL,
    CRAWL_ERRORS_TOTAL,
    PAGES_INDEXED_TOTAL,
    CRAWLER_QUEUE_SIZE,
    SEARCH_REQUESTS_TOTAL,
    SEARCH_LATENCY_SECONDS,
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    get_metrics_payload,
)

__all__ = [
    "logger",
    "log_event",
    "CRAWL_REQUESTS_TOTAL",
    "CRAWL_ERRORS_TOTAL",
    "PAGES_INDEXED_TOTAL",
    "CRAWLER_QUEUE_SIZE",
    "SEARCH_REQUESTS_TOTAL",
    "SEARCH_LATENCY_SECONDS",
    "CACHE_HITS_TOTAL",
    "CACHE_MISSES_TOTAL",
    "get_metrics_payload",
]
