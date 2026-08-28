"""
SQLAlchemy Data Models for NomEngine
Defines schemas for Documents, CrawlQueue, InvertedIndex postings, Link Graph, Images, News, and SearchLogs.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.storage.database import Base


class Document(Base):
    """Core document model for indexed web pages."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    canonical_url = Column(String(2048), nullable=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    
    title = Column(String(1024), nullable=True, default="")
    description = Column(Text, nullable=True, default="")
    content = Column(Text, nullable=False, default="")  # Clean searchable text
    raw_html = Column(Text, nullable=True)             # Optional raw storage
    
    language = Column(String(16), nullable=True, default="en", index=True)
    mime_type = Column(String(64), nullable=True, default="text/html")
    status_code = Column(Integer, nullable=False, default=200)
    word_count = Column(Integer, nullable=False, default=0)
    
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    simhash = Column(BigInteger, nullable=False, default=0)         # 64-bit SimHash
    
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_crawled = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_modified = Column(DateTime, nullable=True)
    next_crawl = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    crawl_count = Column(Integer, nullable=False, default=1)
    
    page_rank = Column(Float, nullable=False, default=1.0, index=True)
    spam_score = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=False, default=1.0)
    is_indexed = Column(Boolean, nullable=False, default=False, index=True)

    # Relationships
    images = relationship("ImageDocument", back_populates="document", cascade="all, delete-orphan")
    news_meta = relationship("NewsArticle", back_populates="document", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_doc_domain_indexed", "domain", "is_indexed"),
        Index("idx_doc_next_crawl", "next_crawl"),
    )


class CrawlQueueItem(Base):
    """Frontier crawl queue tracking URLs to be processed."""
    __tablename__ = "crawl_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=50, index=True)  # 1-100
    depth = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, in_progress, completed, failed
    
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_attempt = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    referrer_url = Column(String(2048), nullable=True)

    __table_args__ = (
        Index("idx_queue_status_prio", "status", "priority", "discovered_at"),
        Index("idx_queue_domain_status", "domain", "status"),
    )


class PageLink(Base):
    """Link graph for calculating PageRank and anchor text matching."""
    __tablename__ = "page_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(2048), nullable=False, index=True)
    target_url = Column(String(2048), nullable=False, index=True)
    anchor_text = Column(String(512), nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source_url", "target_url", name="uq_source_target_link"),
        Index("idx_link_target", "target_url"),
    )


class Posting(Base):
    """Persistent inverted index posting record."""
    __tablename__ = "postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(128), nullable=False, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    term_frequency = Column(Integer, nullable=False, default=1)
    positions = Column(Text, nullable=False, default="[]")  # JSON-encoded int array

    __table_args__ = (
        UniqueConstraint("term", "doc_id", name="uq_term_doc"),
        Index("idx_posting_term_doc", "term", "doc_id"),
    )


class TermStat(Base):
    """Corpus-level term statistics for fast IDF calculations."""
    __tablename__ = "term_stats"

    term = Column(String(128), primary_key=True)
    doc_frequency = Column(Integer, nullable=False, default=1)
    total_occurrences = Column(Integer, nullable=False, default=1)


class ImageDocument(Base):
    """Extracted image assets for Image Search."""
    __tablename__ = "image_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(2048), nullable=False, index=True)
    page_url = Column(String(2048), nullable=False)
    alt_text = Column(String(1024), nullable=True, default="")
    title = Column(String(512), nullable=True, default="")
    mime_type = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    surrounding_text = Column(Text, nullable=True)

    document = relationship("Document", back_populates="images")


class NewsArticle(Base):
    """Extracted news articles for News Search."""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    headline = Column(String(1024), nullable=False)
    publisher = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    published_date = Column(DateTime, nullable=True, index=True)
    modified_date = Column(DateTime, nullable=True)
    category = Column(String(128), nullable=True)

    document = relationship("Document", back_populates="news_meta")


class SearchLog(Base):
    """Anonymized search query logs for analytics, popular terms, and autocomplete."""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(512), nullable=False, index=True)
    normalized_query = Column(String(512), nullable=False, index=True)
    results_count = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
