"""
Main FastAPI Application Entry Point for NomEngine
Configures CORS, lifespan initialization, Swagger docs, Prometheus metrics, and routes.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.cache.redis_cache import cache_service
from app.config.settings import settings
from app.crawler.crawler import crawler_instance
from app.indexing.indexer import indexer
from app.monitoring.logger import logger
from app.monitoring.metrics import get_metrics_payload
from app.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycles."""
    logger.info(f"Initializing {settings.APP_NAME} v{settings.APP_VERSION}...")
    # 1. Initialize DB schema
    await init_db()
    # 2. Connect Cache
    await cache_service.connect()
    # 3. Load Inverted Index into memory
    await indexer.load_index_from_db()
    # 4. Auto-index any pending documents
    await indexer.index_all_unindexed()

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    await crawler_instance.stop()
    await cache_service.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-grade web search engine built from scratch in Python.",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    payload, content_type = get_metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.get("/")
async def root():
    """Root redirect / information endpoint."""
    return {
        "engine": settings.APP_NAME,
        "status": "online",
        "docs": f"{settings.API_PREFIX}/docs",
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
