"""
Intelligent Crawl Scheduler
Dynamically computes next re-crawl intervals based on historical update patterns and change frequencies.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, update
from app.crawler.frontier import frontier
from app.monitoring.logger import logger
from app.storage.database import async_session_factory
from app.storage.models import Document


class CrawlScheduler:
    """Calculates dynamic re-crawl intervals for indexed web pages."""

    def calculate_next_crawl(
        self,
        crawl_count: int,
        content_changed: bool,
        quality_score: float,
    ) -> datetime:
        """
        Dynamically adjusts crawl frequency:
        - Rapidly changing / high-quality pages -> frequent crawl (hours)
        - Static / low-change pages -> exponential backoff (days/weeks)
        """
        now = datetime.utcnow()

        if content_changed:
            # Frequently updated page: crawl in 6 hours
            hours = 6
        elif crawl_count == 1:
            hours = 24
        elif crawl_count <= 5:
            hours = 72  # 3 days
        else:
            # Evergreen content: crawl in 7 days
            hours = 168

        # High quality bonus: crawl 30% faster
        if quality_score > 1.2:
            hours = max(4, int(hours * 0.7))

        return now + timedelta(hours=hours)

    async def schedule_due_recrawls(self):
        """Scans database for documents due for re-crawling and re-enqueues them."""
        now = datetime.utcnow()
        async with async_session_factory() as session:
            result = await session.execute(
                select(Document)
                .where(Document.next_crawl <= now)
                .limit(200)
            )
            due_docs = result.scalars().all()

            for doc in due_docs:
                prio = int(min(90, max(20, doc.page_rank * 20)))
                await frontier.add_url(
                    url=doc.url,
                    priority=prio,
                    depth=0,
                    persist=False,
                )
                doc.next_crawl = now + timedelta(days=3)

            await session.commit()
            if due_docs:
                logger.info(f"Scheduler re-enqueued {len(due_docs)} due URLs for re-crawling.")


scheduler_instance = CrawlScheduler()


async def run_scheduler(interval_seconds: float = 60.0):
    """Background scheduler loop."""
    logger.info("Starting Crawl Scheduler background loop...")
    while True:
        try:
            await scheduler_instance.schedule_due_recrawls()
            await asyncio.sleep(interval_seconds)
        except (KeyboardInterrupt, asyncio.CancelledError):
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(interval_seconds)
