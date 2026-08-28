"""
Master Crawler Orchestrator
Coordinates URL dispatching, fetching, robots.txt compliance, content extraction, deduplication, and database persistence.
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update
from app.config.settings import settings
from app.crawler.deduplication import calculate_sha256, simhash_calculator
from app.crawler.fetcher import fetcher
from app.crawler.frontier import frontier, FrontierTask
from app.crawler.parser import extractor, ParsedPage
from app.crawler.robots import robots_manager
from app.monitoring.logger import logger, log_event
from app.storage.database import async_session_factory
from app.storage.models import Document, ImageDocument, NewsArticle, PageLink


class Crawler:
    """Production-grade asynchronous web crawler."""

    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self._workers: List[asyncio.Task] = []
        self._crawled_count = 0
        self._lock = asyncio.Lock()

    async def start(self, seeds: Optional[List[str]] = None, num_workers: int = 5):
        """Starts the crawling engine with the specified worker concurrency."""
        if self.is_running:
            logger.warning("Crawler is already running.")
            return

        self.is_running = True
        self.is_paused = False
        await frontier.initialize()

        if seeds:
            await frontier.add_seeds(seeds)

        logger.info(f"Starting {num_workers} crawler workers...")
        self._workers = [
            asyncio.create_task(self._worker_loop(worker_id=i))
            for i in range(num_workers)
        ]

    async def pause(self):
        """Pauses worker pulling."""
        self.is_paused = True
        logger.info("Crawler paused.")

    async def resume(self):
        """Resumes worker pulling."""
        self.is_paused = False
        logger.info("Crawler resumed.")

    async def stop(self):
        """Gracefully stops all crawler workers."""
        self.is_running = False
        self.is_paused = False
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        await fetcher.close()
        logger.info("Crawler stopped.")

    async def _worker_loop(self, worker_id: int):
        """Individual crawler worker pulling and processing URLs."""
        logger.debug(f"Crawler worker {worker_id} started.")
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(1.0)
                    continue

                if self._crawled_count >= settings.CRAWLER_MAX_DOCUMENTS:
                    logger.info("Crawler reached configured max document limit.")
                    break

                task = await frontier.get_next_url()
                if not task:
                    await asyncio.sleep(0.5)
                    continue

                await self._process_task(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered unexpected error: {e}")
                await asyncio.sleep(1.0)

    async def _process_task(self, task: FrontierTask):
        """Fetches, parses, deduplicates, and stores a web page."""
        url = task.url
        domain = task.domain

        try:
            # 1. Robots.txt check
            if not await robots_manager.is_allowed(url):
                logger.info(f"Robots.txt disallowed: {url}")
                await frontier.mark_failed(url, "ROBOTS_TXT_DISALLOWED")
                return

            # 2. Wait polite crawl delay
            await robots_manager.wait_polite(domain)

            # 3. Fetch web page
            response = await fetcher.fetch(url)
            if not response.is_success:
                logger.debug(f"Fetch failed for {url}: {response.error}")
                await frontier.mark_failed(url, response.error or f"HTTP_{response.status_code}")
                return

            # 4. Parse HTML and extract content
            parsed: ParsedPage = extractor.parse(response.content, url)
            if parsed.noindex:
                logger.info(f"Page specifies noindex meta: {url}")
                await frontier.mark_completed(url)
                return

            # 5. Content Deduplication
            content_hash = calculate_sha256(parsed.main_text or parsed.title)
            simhash_val = str(simhash_calculator.calculate_simhash(parsed.main_text or parsed.title))

            # 6. Database Storage & Update
            target_url = parsed.canonical_url or url
            async with async_session_factory() as session:
                # Check for existing document
                existing = await session.execute(
                    select(Document).where(Document.url == target_url)
                )
                doc = existing.scalar_one_or_none()

                if doc:
                    # Update existing document
                    doc.title = parsed.title or doc.title
                    doc.description = parsed.description or doc.description
                    doc.content = parsed.main_text
                    doc.content_hash = content_hash
                    doc.simhash = simhash_val
                    doc.word_count = parsed.word_count
                    doc.language = parsed.language
                    doc.last_crawled = datetime.utcnow()
                    doc.crawl_count += 1
                    doc.is_indexed = False  # Mark for re-indexing
                else:
                    # Create new document
                    doc = Document(
                        url=target_url,
                        canonical_url=parsed.canonical_url,
                        domain=domain,
                        title=parsed.title or target_url,
                        description=parsed.description,
                        content=parsed.main_text,
                        language=parsed.language,
                        mime_type=response.content_type,
                        status_code=response.status_code,
                        word_count=parsed.word_count,
                        content_hash=content_hash,
                        simhash=simhash_val,
                        first_seen=datetime.utcnow(),
                        last_crawled=datetime.utcnow(),
                        is_indexed=False,
                    )
                    session.add(doc)
                    await session.flush()  # Acquire doc.id

                # Save Extracted Images
                for img_data in parsed.images[:15]:  # Limit top 15 images per page
                    img_doc = ImageDocument(
                        doc_id=doc.id,
                        image_url=img_data["image_url"],
                        page_url=target_url,
                        alt_text=img_data["alt_text"],
                        title=img_data["title"],
                        width=img_data["width"],
                        height=img_data["height"],
                        surrounding_text=img_data["surrounding_text"],
                    )
                    session.add(img_doc)

                # Save News Article Metadata
                if parsed.is_news and parsed.news_headline:
                    news_entry = NewsArticle(
                        doc_id=doc.id,
                        headline=parsed.news_headline,
                        publisher=parsed.news_publisher,
                        author=parsed.author,
                        published_date=parsed.published_date or datetime.utcnow(),
                    )
                    session.add(news_entry)

                # Save Page Links for PageRank & Anchor text (deduplicated per page)
                saved_targets = set()
                for target_link, anchor in parsed.links:
                    if target_link in saved_targets:
                        continue
                    saved_targets.add(target_link)
                    try:
                        link_entry = PageLink(
                            source_url=target_url,
                            target_url=target_link,
                            anchor_text=anchor[:500],
                        )
                        session.add(link_entry)
                    except Exception:
                        pass

                await session.commit()

            # 7. Discover and Queue Outgoing Links
            if task.depth + 1 <= settings.CRAWLER_MAX_PAGE_DEPTH:
                for target_link, _ in parsed.links:
                    # Slightly higher priority for internal domain links
                    prio = 60 if domain in target_link else 40
                    await frontier.add_url(
                        url=target_link,
                        priority=prio,
                        depth=task.depth + 1,
                        referrer=url,
                    )

            # 8. Mark completed
            await frontier.mark_completed(url)
            async with self._lock:
                self._crawled_count += 1

            log_event(
                "page_crawled_and_stored",
                url=url,
                title=parsed.title[:60],
                word_count=parsed.word_count,
                links_discovered=len(parsed.links),
            )

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            await frontier.mark_failed(url, str(e))
        finally:
            await frontier.release_domain(domain)


crawler_instance = Crawler()
