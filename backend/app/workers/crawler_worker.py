"""
Standalone Distributed Crawler Worker Process
Pulls crawl jobs, fetches pages, updates database, and queues outgoing links.
"""
import asyncio
from app.crawler.crawler import crawler_instance
from app.monitoring.logger import logger
from app.storage.database import init_db


async def run_crawler_worker(concurrency: int = 10):
    """Entry point for standalone crawler worker process."""
    logger.info(f"Starting standalone crawler worker with concurrency={concurrency}...")
    await init_db()
    await crawler_instance.start(num_workers=concurrency)

    try:
        while True:
            await asyncio.sleep(5.0)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping crawler worker...")
        await crawler_instance.stop()


if __name__ == "__main__":
    asyncio.run(run_crawler_worker())
