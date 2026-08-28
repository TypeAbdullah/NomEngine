"""
Background Indexer Worker
Periodically scans for unindexed documents, builds positional posting lists, and updates inverted index.
"""
import asyncio
from app.indexing.indexer import indexer
from app.monitoring.logger import logger
from app.ranking.pagerank import pagerank_calculator
from app.storage.database import init_db


async def run_indexer_worker(poll_interval: float = 3.0):
    """Entry point for standalone indexing worker process."""
    logger.info("Starting background indexer worker...")
    await init_db()
    await indexer.load_index_from_db()

    iteration = 0
    while True:
        try:
            indexed = await indexer.index_all_unindexed(batch_size=100)
            iteration += 1

            # Recalculate PageRank every 20 iterations if new documents were indexed
            if indexed > 0 and iteration % 20 == 0:
                logger.info("Triggering periodic PageRank recalculation...")
                await pagerank_calculator.update_database_pagerank()

            await asyncio.sleep(poll_interval)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Stopping indexer worker...")
            break
        except Exception as e:
            logger.error(f"Indexer worker error: {e}")
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_indexer_worker())
