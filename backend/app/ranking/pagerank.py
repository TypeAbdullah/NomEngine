"""
PageRank Graph Algorithm
Computes stationary probability distribution across the crawled web graph using power iteration.
"""
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from sqlalchemy import select, update
from app.config.settings import settings
from app.monitoring.logger import logger
from app.storage.database import async_session_factory
from app.storage.models import Document, PageLink


class PageRankCalculator:
    """Calculates PageRank scores for all crawled URLs."""

    def __init__(
        self,
        damping: float = settings.PAGERANK_DAMPING,
        max_iter: int = settings.PAGERANK_MAX_ITERATIONS,
        tolerance: float = settings.PAGERANK_TOLERANCE,
    ):
        self.damping = damping
        self.max_iter = max_iter
        self.tolerance = tolerance

    def compute(
        self,
        nodes: Set[str],
        edges: List[Tuple[str, str]],
    ) -> Dict[str, float]:
        """
        Computes PageRank given a set of URL nodes and (source, target) directed edges.
        """
        N = len(nodes)
        if N == 0:
            return {}

        # Outgoing edges per node: source -> list of targets
        out_links: Dict[str, List[str]] = defaultdict(list)
        # Ingoing edges per node: target -> list of sources
        in_links: Dict[str, List[str]] = defaultdict(list)

        for src, tgt in edges:
            if src in nodes and tgt in nodes and src != tgt:
                out_links[src].append(tgt)
                in_links[tgt].append(src)

        # Initialize uniform distribution
        ranks: Dict[str, float] = {node: 1.0 / N for node in nodes}
        base_score = (1.0 - self.damping) / N

        for iteration in range(self.max_iter):
            new_ranks: Dict[str, float] = {}
            # Handle dangling nodes (nodes with 0 out-links)
            dangling_sum = sum(ranks[node] for node in nodes if not out_links[node])
            dangling_contribution = self.damping * (dangling_sum / N)

            diff = 0.0
            for node in nodes:
                inbound_sum = sum(
                    ranks[src] / len(out_links[src])
                    for src in in_links[node]
                )
                rank = base_score + dangling_contribution + (self.damping * inbound_sum)
                new_ranks[node] = rank
                diff += abs(rank - ranks[node])

            ranks = new_ranks

            if diff < self.tolerance:
                logger.debug(f"PageRank converged at iteration {iteration + 1} with diff {diff:.8f}")
                break

        # Normalize PageRank values so average is 1.0
        avg_rank = sum(ranks.values()) / N if N > 0 else 1.0
        normalized_ranks = {node: rank / avg_rank for node, rank in ranks.items()}
        return normalized_ranks

    async def update_database_pagerank(self):
        """Pulls links from DB, computes PageRank, and updates Document records."""
        logger.info("Starting PageRank calculation from database link graph...")
        async with async_session_factory() as session:
            # 1. Fetch all indexed document URLs
            docs_res = await session.execute(select(Document.url))
            nodes = {u for (u,) in docs_res.all()}
            if not nodes:
                logger.warning("No documents found for PageRank calculation.")
                return

            # 2. Fetch all directed links
            links_res = await session.execute(select(PageLink.source_url, PageLink.target_url))
            edges = [(src, tgt) for src, tgt in links_res.all()]

            logger.info(f"Computing PageRank for {len(nodes)} pages and {len(edges)} link edges...")
            ranks = self.compute(nodes, edges)

            # 3. Batch update document page_rank values
            for url, pr in ranks.items():
                await session.execute(
                    update(Document)
                    .where(Document.url == url)
                    .values(page_rank=round(pr, 4))
                )
            await session.commit()

        logger.info("PageRank scores updated in database successfully.")


pagerank_calculator = PageRankCalculator()
