"""
URL Frontier with Priority Queues and Per-Domain Politeness Queues
Manages discovery, scheduling, and rate-limiting for crawling millions of URLs.
"""
import asyncio
import heapq
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse
from sqlalchemy import select, update
from app.config.settings import settings
from app.crawler.deduplication import normalize_url
from app.monitoring.logger import logger
from app.monitoring.metrics import CRAWLER_QUEUE_SIZE
from app.storage.database import async_session_factory
from app.storage.models import CrawlQueueItem, Document


@dataclass(order=True)
class FrontierTask:
    """Prioritized queue item for the URL frontier."""
    priority: int  # Negated for max-heap behavior in heapq
    discovered_at: float
    url: str = field(compare=False)
    domain: str = field(compare=False)
    depth: int = field(compare=False)
    referrer: Optional[str] = field(default=None, compare=False)
    retry_count: int = field(default=0, compare=False)


class URLFrontier:
    """
    Two-level frontier:
    1. Priority Queues (Global priority ordering)
    2. Per-Host Queues (Polite round-robin dispatching)
    """

    def __init__(self):
        self._heap: List[FrontierTask] = []
        self._seen_urls: Set[str] = set()
        self._active_domain_requests: Dict[str, int] = defaultdict(int)
        self._domain_queues: Dict[str, List[FrontierTask]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Loads pending URLs from the database on startup."""
        if self._initialized:
            return

        async with self._lock:
            async with async_session_factory() as session:
                # Load seen URLs
                doc_urls = await session.execute(select(Document.url))
                for (u,) in doc_urls.all():
                    self._seen_urls.add(u)

                # Load pending queue items
                pending_items = await session.execute(
                    select(CrawlQueueItem).where(CrawlQueueItem.status == "pending")
                )
                for item in pending_items.scalars().all():
                    self._seen_urls.add(item.url)
                    task = FrontierTask(
                        priority=-item.priority,  # Max-heap
                        discovered_at=item.discovered_at.timestamp(),
                        url=item.url,
                        domain=item.domain,
                        depth=item.depth,
                        referrer=item.referrer_url,
                        retry_count=item.retry_count,
                    )
                    heapq.heappush(self._heap, task)

            self._initialized = True
            CRAWLER_QUEUE_SIZE.set(len(self._heap))
            logger.info(f"Frontier initialized with {len(self._heap)} queued URLs and {len(self._seen_urls)} seen URLs.")

    async def add_url(
        self,
        url: str,
        priority: int = 50,
        depth: int = 0,
        referrer: Optional[str] = None,
        persist: bool = True,
    ) -> bool:
        """
        Adds a new URL to the frontier if it hasn't been crawled or queued.
        """
        normalized = normalize_url(url)
        if not normalized:
            return False

        parsed = urlparse(normalized)
        domain = parsed.netloc.lower()
        if not domain:
            return False

        if depth > settings.CRAWLER_MAX_PAGE_DEPTH:
            return False

        # Domain restrictions
        if settings.CRAWLER_ALLOWED_DOMAINS and domain not in settings.CRAWLER_ALLOWED_DOMAINS:
            return False
        if domain in settings.CRAWLER_DISALLOWED_DOMAINS:
            return False

        async with self._lock:
            if normalized in self._seen_urls:
                return False

            self._seen_urls.add(normalized)

            task = FrontierTask(
                priority=-priority,
                discovered_at=time.time(),
                url=normalized,
                domain=domain,
                depth=depth,
                referrer=referrer,
            )
            heapq.heappush(self._heap, task)
            CRAWLER_QUEUE_SIZE.set(len(self._heap))

        if persist:
            try:
                async with async_session_factory() as session:
                    queue_entry = CrawlQueueItem(
                        url=normalized,
                        domain=domain,
                        priority=priority,
                        depth=depth,
                        status="pending",
                        referrer_url=referrer,
                    )
                    session.add(queue_entry)
                    await session.commit()
            except Exception as e:
                logger.debug(f"Failed to persist queue item {normalized}: {e}")

        return True

    async def add_seeds(self, seeds: List[str], priority: int = 100):
        """Adds a batch of seed URLs with top priority."""
        for seed in seeds:
            await self.add_url(seed, priority=priority, depth=0, persist=True)

    async def get_next_url(self) -> Optional[FrontierTask]:
        """
        Pulls the next eligible URL obeying per-domain concurrency limits.
        """
        async with self._lock:
            if not self._heap:
                return None

            stashed: List[FrontierTask] = []
            selected_task: Optional[FrontierTask] = None

            while self._heap:
                task = heapq.heappop(self._heap)
                # Check domain concurrency limit
                if (
                    self._active_domain_requests[task.domain]
                    < settings.CRAWLER_MAX_REQUESTS_PER_DOMAIN
                ):
                    selected_task = task
                    self._active_domain_requests[task.domain] += 1
                    break
                else:
                    # Domain is currently saturated, hold task for now
                    stashed.append(task)

            # Return stashed tasks back to heap
            for task in stashed:
                heapq.heappush(self._heap, task)

            CRAWLER_QUEUE_SIZE.set(len(self._heap))
            return selected_task

    async def release_domain(self, domain: str):
        """Decrements active request count for a domain."""
        async with self._lock:
            if self._active_domain_requests[domain] > 0:
                self._active_domain_requests[domain] -= 1

    async def mark_completed(self, url: str):
        """Marks queue item as completed in database."""
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(CrawlQueueItem)
                    .where(CrawlQueueItem.url == url)
                    .values(status="completed", last_attempt=datetime.utcnow())
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"Error marking completed for {url}: {e}")

    async def mark_failed(self, url: str, error: str):
        """Marks queue item as failed with error log."""
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(CrawlQueueItem)
                    .where(CrawlQueueItem.url == url)
                    .values(
                        status="failed",
                        error_message=error,
                        last_attempt=datetime.utcnow(),
                    )
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"Error marking failed for {url}: {e}")

    @property
    def queue_size(self) -> int:
        return len(self._heap)


frontier = URLFrontier()
