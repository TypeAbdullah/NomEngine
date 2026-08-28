"""
Command-Line Interface for NomEngine Search Engine
Provides CLI commands for crawling, indexing, reindexing, evaluating, and viewing stats.
"""
import asyncio
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from app.config.settings import settings
from app.crawler.crawler import crawler_instance
from app.evaluation.quality_eval import evaluator
from app.indexing.indexer import indexer
from app.indexing.inverted_index import inverted_index
from app.ranking.pagerank import pagerank_calculator
from app.storage.database import init_db

cli = typer.Typer(help="NomEngine Search Engine Command-Line Interface")
console = Console()


@cli.command("crawl")
def crawl_command(
    url: Optional[str] = typer.Argument(None, help="Single URL to crawl"),
    seed: Optional[str] = typer.Option(None, "--seed", "-s", help="Path to seed URLs text file"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Number of concurrent crawl workers"),
    max_docs: int = typer.Option(100, "--max-docs", "-m", help="Maximum documents to crawl"),
):
    """Start the web crawler on specified seed URLs or file."""
    seeds = []
    if url:
        seeds.append(url)
    if seed:
        try:
            with open(seed, "r") as f:
                seeds.extend([line.strip() for line in f if line.strip() and not line.startswith("#")])
        except Exception as e:
            console.print(f"[red]Failed to read seed file: {e}[/red]")
            raise typer.Exit(code=1)

    if not seeds:
        seeds = [
            "https://docs.python.org/3/",
            "https://www.python.org/",
            "https://www.djangoproject.com/",
        ]
        console.print("[yellow]No seed provided; using default standard seeds:[/yellow]")
        for s in seeds:
            console.print(f" - {s}")

    settings.CRAWLER_MAX_DOCUMENTS = max_docs

    async def _crawl():
        await init_db()
        console.print(f"[green]Starting crawler with {len(seeds)} seeds, concurrency={concurrency}...[/green]")
        await crawler_instance.start(seeds=seeds, num_workers=concurrency)
        while crawler_instance.is_running:
            await asyncio.sleep(2.0)

    try:
        asyncio.run(_crawl())
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping crawler...[/yellow]")
        asyncio.run(crawler_instance.stop())


@cli.command("index")
def index_command():
    """Process and index pending unindexed documents."""
    async def _index():
        await init_db()
        await indexer.load_index_from_db()
        indexed = await indexer.index_all_unindexed()
        console.print(f"[green]Indexed {indexed} documents. Total in index: {inverted_index.total_docs}[/green]")

    asyncio.run(_index())


@cli.command("reindex")
def reindex_command():
    """Perform a full re-indexing of all documents and recalculate PageRank."""
    async def _reindex():
        await init_db()
        console.print("[yellow]Rebuilding inverted index from database...[/yellow]")
        await indexer.load_index_from_db()
        console.print("[yellow]Calculating PageRank link graph...[/yellow]")
        await pagerank_calculator.update_database_pagerank()
        console.print(f"[green]Full re-indexing complete! {inverted_index.total_docs} documents ready.[/green]")

    asyncio.run(_reindex())


@cli.command("stats")
def stats_command():
    """Display current search engine statistics."""
    async def _stats():
        await init_db()
        await indexer.load_index_from_db()

        table = Table(title="NomEngine System Status")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Indexed Documents", str(inverted_index.total_docs))
        table.add_row("Unique Vocabulary Terms", str(len(inverted_index.index)))
        table.add_row("Average Document Length", f"{inverted_index.avg_doc_length:.1f} tokens")

        console.print(table)

    asyncio.run(_stats())


@cli.command("evaluate")
def evaluate_command(
    k: int = typer.Option(5, "--top-k", "-k", help="Evaluate top K results"),
):
    """Run Information Retrieval ranking evaluation (Precision@K, MRR, NDCG)."""
    async def _eval():
        await init_db()
        await indexer.load_index_from_db()
        console.print(f"[yellow]Running IR ranking evaluation against benchmark queries (K={k})...[/yellow]")
        metrics = await evaluator.run_evaluation(k=k)

        table = Table(title="Ranking Quality Evaluation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="green")

        for metric, score in metrics.items():
            table.add_row(metric, f"{score:.4f}")

        console.print(table)

    asyncio.run(_eval())


if __name__ == "__main__":
    cli()
