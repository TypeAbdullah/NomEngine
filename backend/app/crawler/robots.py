"""
Asynchronous robots.txt Parser & Politeness Manager
Handles User-Agent directives, crawl-delay, sitemap discovery, and caching.
"""
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from app.cache.redis_cache import cache_service
from app.config.settings import settings
from app.monitoring.logger import logger


class RobotsManager:
    """Manages robots.txt checking, parsing, caching, and rate limiting."""

    def __init__(self):
        self._parsers: Dict[str, Tuple[RobotFileParser, List[str], float, float]] = {}
        # domain -> (parser, sitemaps, crawl_delay, last_fetched_timestamp)
        self._domain_last_request: Dict[str, float] = {}
        self._domain_locks: Dict[str, asyncio.Lock] = {}

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    async def fetch_robots_txt(self, domain_url: str) -> Tuple[RobotFileParser, List[str], float]:
        """Fetches and parses robots.txt for a root domain."""
        parsed = urlparse(domain_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        domain = netloc.lower()

        # Check in-memory cache first
        if domain in self._parsers:
            parser, sitemaps, crawl_delay, fetched_at = self._parsers[domain]
            if time.time() - fetched_at < settings.CACHE_TTL_ROBOTS:
                return parser, sitemaps, crawl_delay

        robots_url = f"{scheme}://{domain}/robots.txt"
        rp = RobotFileParser()
        sitemaps: List[str] = []
        crawl_delay: float = settings.CRAWLER_CRAWL_DELAY_DEFAULT

        try:
            async with httpx.AsyncClient(
                timeout=5.0,
                headers={"User-Agent": settings.CRAWLER_USER_AGENT},
                follow_redirects=True,
            ) as client:
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    rp.parse(lines)

                    for line in lines:
                        line_clean = line.strip()
                        if line_clean.lower().startswith("sitemap:"):
                            sitemap_url = line_clean.split(":", 1)[1].strip()
                            if sitemap_url:
                                sitemaps.append(sitemap_url)
                        elif line_clean.lower().startswith("crawl-delay:"):
                            try:
                                delay_val = float(line_clean.split(":", 1)[1].strip())
                                crawl_delay = max(delay_val, settings.CRAWLER_CRAWL_DELAY_DEFAULT)
                            except ValueError:
                                pass
                elif resp.status_code in (401, 403):
                    # Disallow all if unauthorized/forbidden
                    rp.disallow_all = True
                else:
                    # 404 or other: allow all
                    rp.allow_all = True
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt for {domain} ({e}); defaulting to allow all.")
            rp.allow_all = True

        self._parsers[domain] = (rp, sitemaps, crawl_delay, time.time())
        return rp, sitemaps, crawl_delay

    async def is_allowed(self, url: str) -> bool:
        """Determines if a URL is allowed to be crawled according to robots.txt."""
        if not settings.CRAWLER_RESPECT_ROBOTS_TXT:
            return True

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            return False

        # Domain restrictions check
        if settings.CRAWLER_ALLOWED_DOMAINS and domain not in settings.CRAWLER_ALLOWED_DOMAINS:
            return False
        if domain in settings.CRAWLER_DISALLOWED_DOMAINS:
            return False

        rp, _, _ = await self.fetch_robots_txt(url)
        return rp.can_fetch(settings.CRAWLER_USER_AGENT, url)

    async def wait_polite(self, domain: str):
        """Enforces polite per-domain crawl delays."""
        lock = self._get_domain_lock(domain)
        async with lock:
            last_req = self._domain_last_request.get(domain, 0.0)
            _, _, crawl_delay = self._parsers.get(domain, (None, None, settings.CRAWLER_CRAWL_DELAY_DEFAULT, 0))
            elapsed = time.time() - last_req
            if elapsed < crawl_delay:
                await asyncio.sleep(crawl_delay - elapsed)
            self._domain_last_request[domain] = time.time()


robots_manager = RobotsManager()
