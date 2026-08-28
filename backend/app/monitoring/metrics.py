"""
Prometheus Metrics Module
Exposes standardized metrics for crawling, indexing, searches, latency, and caches.
"""
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Custom Registry
REGISTRY = CollectorRegistry()

# Crawl Metrics
CRAWL_REQUESTS_TOTAL = Counter(
    "crawl_requests_total",
    "Total HTTP crawl requests made",
    ["status", "domain"],
    registry=REGISTRY,
)

CRAWL_ERRORS_TOTAL = Counter(
    "crawl_errors_total",
    "Total crawl failures by error type",
    ["error_type", "domain"],
    registry=REGISTRY,
)

PAGES_INDEXED_TOTAL = Counter(
    "pages_indexed_total",
    "Total unique documents indexed",
    registry=REGISTRY,
)

CRAWLER_QUEUE_SIZE = Gauge(
    "crawler_queue_size",
    "Current number of URLs waiting in frontier queue",
    registry=REGISTRY,
)

CRAWL_LATENCY_SECONDS = Histogram(
    "crawl_latency_seconds",
    "Time spent fetching web pages",
    ["domain"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# Search Metrics
SEARCH_REQUESTS_TOTAL = Counter(
    "search_requests_total",
    "Total search queries processed",
    registry=REGISTRY,
)

SEARCH_LATENCY_SECONDS = Histogram(
    "search_latency_seconds",
    "Search execution latency in seconds",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total cache hit count",
    ["cache_type"],
    registry=REGISTRY,
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total cache miss count",
    ["cache_type"],
    registry=REGISTRY,
)

ACTIVE_WORKERS = Gauge(
    "active_workers",
    "Active background workers",
    ["worker_type"],
    registry=REGISTRY,
)


def get_metrics_payload() -> tuple[bytes, str]:
    """Returns the formatted Prometheus metrics body and content type."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
