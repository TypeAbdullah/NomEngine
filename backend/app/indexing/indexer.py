"""
Batch Indexer Pipeline
Processes unindexed documents from the database, builds posting lists, and synchronizes the inverted index.
"""
import asyncio
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update
from app.config.settings import settings
from app.indexing.inverted_index import inverted_index
from app.indexing.text_processor import text_processor
from app.monitoring.logger import logger
from app.monitoring.metrics import PAGES_INDEXED_TOTAL
from app.storage.database import async_session_factory
from app.storage.models import Document, Posting, TermStat


class BatchIndexer:
    """Orchestrates document indexing into the inverted index."""

    def __init__(self):
        self._lock = asyncio.Lock()

    async def index_all_unindexed(self, batch_size: int = 100) -> int:
        """Indexes all pending documents in batches."""
        total_indexed = 0
        while True:
            indexed_count = await self.index_next_batch(batch_size=batch_size)
            if indexed_count == 0:
                break
            total_indexed += indexed_count

        logger.info(f"Batch indexing finished: {total_indexed} documents indexed.")
        return total_indexed

    async def index_next_batch(self, batch_size: int = 100) -> int:
        """Pulls and indexes one batch of unindexed documents."""
        async with self._lock:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Document)
                    .where(Document.is_indexed == False)
                    .order_by(Document.id.asc())
                    .limit(batch_size)
                )
                docs = result.scalars().all()
                if not docs:
                    return 0

                for doc in docs:
                    # Combine title (weighted higher in text) + description + body content
                    combined_text = f"{doc.title} {doc.title} {doc.description} {doc.content}"
                    tokens_with_pos = text_processor.tokenize_with_positions(combined_text)

                    metadata = {
                        "id": doc.id,
                        "url": doc.url,
                        "domain": doc.domain,
                        "title": doc.title,
                        "description": doc.description,
                        "content": doc.content,
                        "published_at": doc.first_seen.isoformat() if doc.first_seen else None,
                        "page_rank": doc.page_rank or 1.0,
                        "spam_score": doc.spam_score or 0.0,
                        "quality_score": doc.quality_score or 1.0,
                        "word_count": doc.word_count,
                        "simhash": doc.simhash,
                    }

                    # Add to in-memory positional inverted index
                    inverted_index.add_document(
                        doc_id=doc.id,
                        tokens_with_positions=tokens_with_pos,
                        metadata=metadata,
                    )

                    doc.is_indexed = True
                    PAGES_INDEXED_TOTAL.inc()

                await session.commit()
                return len(docs)

    async def load_index_from_db(self):
        """Rebuilds the in-memory inverted index from existing documents in the database."""
        logger.info("Loading inverted index from database documents...")
        inverted_index.clear()
        async with async_session_factory() as session:
            result = await session.execute(
                select(Document).order_by(Document.id.asc())
            )
            docs = result.scalars().all()
            for doc in docs:
                combined_text = f"{doc.title} {doc.title} {doc.description} {doc.content}"
                tokens_with_pos = text_processor.tokenize_with_positions(combined_text)
                metadata = {
                    "id": doc.id,
                    "url": doc.url,
                    "domain": doc.domain,
                    "title": doc.title,
                    "description": doc.description,
                    "content": doc.content,
                    "published_at": doc.first_seen.isoformat() if doc.first_seen else None,
                    "page_rank": doc.page_rank or 1.0,
                    "spam_score": doc.spam_score or 0.0,
                    "quality_score": doc.quality_score or 1.0,
                    "word_count": doc.word_count,
                    "simhash": doc.simhash,
                }
                inverted_index.add_document(
                    doc_id=doc.id,
                    tokens_with_positions=tokens_with_pos,
                    metadata=metadata,
                )
        logger.info(f"Loaded {inverted_index.total_docs} documents into Inverted Index.")


indexer = BatchIndexer()
