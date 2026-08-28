from app.crawler.crawler import crawler_instance, Crawler
from app.crawler.frontier import frontier, URLFrontier
from app.crawler.fetcher import fetcher, AsyncFetcher
from app.crawler.robots import robots_manager, RobotsManager
from app.crawler.parser import extractor, HTMLContentExtractor, ParsedPage
from app.crawler.deduplication import normalize_url, calculate_sha256, simhash_calculator, SimHash

__all__ = [
    "crawler_instance",
    "Crawler",
    "frontier",
    "URLFrontier",
    "fetcher",
    "AsyncFetcher",
    "robots_manager",
    "RobotsManager",
    "extractor",
    "HTMLContentExtractor",
    "ParsedPage",
    "normalize_url",
    "calculate_sha256",
    "simhash_calculator",
    "SimHash",
]
