"""
Global Application Configuration
Supports environment variables and defaults for all subsystems.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    APP_NAME: str = "NomEngine"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "nomengine-super-secret-key-change-in-production"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./nomengine.db"
    # For Postgres: "postgresql+asyncpg://postgres:postgres@localhost:5432/nomengine"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis Cache & Queues
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    CACHE_TTL_SEARCH: int = 3600       # 1 hour
    CACHE_TTL_SUGGEST: int = 86400     # 24 hours
    CACHE_TTL_ROBOTS: int = 86400      # 24 hours

    # Crawler Settings
    CRAWLER_USER_AGENT: str = "NomEngineBot/1.0 (+https://nomengine.local/bot; search-crawler@nomengine.local)"
    CRAWLER_MAX_CONCURRENT_REQUESTS: int = 50
    CRAWLER_MAX_REQUESTS_PER_DOMAIN: int = 2
    CRAWLER_CRAWL_DELAY_DEFAULT: float = 1.0  # seconds
    CRAWLER_MAX_PAGE_DEPTH: int = 5
    CRAWLER_MAX_RESPONSE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    CRAWLER_REQUEST_TIMEOUT: float = 10.0  # seconds
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_RETRY_BACKOFF_FACTOR: float = 1.5
    CRAWLER_RESPECT_ROBOTS_TXT: bool = True
    CRAWLER_MAX_DOCUMENTS: int = 10000
    CRAWLER_ALLOWED_DOMAINS: List[str] = []  # Empty means all domains allowed
    CRAWLER_DISALLOWED_DOMAINS: List[str] = []

    # Security & SSRF
    SSRF_PROTECTION_ENABLED: bool = True
    BLOCKED_IP_NETWORKS: List[str] = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.169.254/32",
        "0.0.0.0/8",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    ]

    # Deduplication
    SIMHASH_BITS: int = 64
    SIMHASH_HAMMING_THRESHOLD: int = 3  # Near-duplicate threshold

    # Indexer Settings
    INDEX_BATCH_SIZE: int = 100
    INDEX_STORAGE_PATH: str = "./index_data"

    # Ranking Weights
    WEIGHT_BM25: float = 0.40
    WEIGHT_TITLE: float = 0.25
    WEIGHT_PHRASE: float = 0.15
    WEIGHT_ANCHOR: float = 0.10
    WEIGHT_PAGERANK: float = 0.10
    WEIGHT_FRESHNESS: float = 0.05
    WEIGHT_QUALITY: float = 0.05
    PENALTY_SPAM: float = 0.50
    PENALTY_DUPLICATE: float = 0.80

    # PageRank Settings
    PAGERANK_DAMPING: float = 0.85
    PAGERANK_MAX_ITERATIONS: int = 50
    PAGERANK_TOLERANCE: float = 1e-6

    # Evaluation
    EVAL_TOP_K: int = 10


settings = Settings()
