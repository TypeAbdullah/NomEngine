"""
Asynchronous HTTP Web Page Fetcher
Implements connection pooling, SSRF protection, size caps, retries, compression, and conditional requests.
"""
import asyncio
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import httpx
from app.api.security import validate_crawl_url
from app.config.settings import settings
from app.monitoring.logger import logger, log_event
from app.monitoring.metrics import CRAWL_REQUESTS_TOTAL, CRAWL_ERRORS_TOTAL, CRAWL_LATENCY_SECONDS


class FetchResponse:
    """Encapsulates the HTTP response data."""

    def __init__(
        self,
        url: str,
        status_code: int,
        content: str = "",
        content_type: str = "",
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.content_type = content_type
        self.etag = etag
        self.last_modified = last_modified
        self.latency_ms = latency_ms
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.status_code == 200 and not self.error


class AsyncFetcher:
    """High-throughput async HTTP client with safety guards."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def get_client(self) -> httpx.AsyncClient:
        """Returns or creates the shared async httpx client."""
        if self.client is None or self.client.is_closed:
            limits = httpx.Limits(
                max_connections=settings.CRAWLER_MAX_CONCURRENT_REQUESTS,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            )
            self.client = httpx.AsyncClient(
                headers=self._headers,
                timeout=httpx.Timeout(settings.CRAWLER_REQUEST_TIMEOUT, connect=5.0),
                follow_redirects=True,
                max_redirects=5,
                limits=limits,
                verify=False,  # Permissive for broad web crawling
            )
        return self.client

    async def close(self):
        """Closes the underlying client session."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None

    async def fetch(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> FetchResponse:
        """
        Safely fetches a web page with SSRF validation, size limiting, retries, and conditional headers.
        """
        domain = urlparse(url).netloc.lower()

        # 1. SSRF and Domain Security Validation
        if not validate_crawl_url(url):
            CRAWL_ERRORS_TOTAL.labels(error_type="ssrf_blocked", domain=domain).inc()
            return FetchResponse(url=url, status_code=403, error="SSRF_BLOCKED")

        client = await self.get_client()

        # Setup conditional request headers if available
        headers = dict(self._headers)
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        retries = 0
        backoff = settings.CRAWLER_RETRY_BACKOFF_FACTOR

        while retries <= settings.CRAWLER_MAX_RETRIES:
            start_time = time.perf_counter()
            try:
                response = await client.get(url, headers=headers)
                latency_s = time.perf_counter() - start_time
                latency_ms = latency_s * 1000.0
                CRAWL_LATENCY_SECONDS.labels(domain=domain).observe(latency_s)

                # Handle 304 Not Modified
                if response.status_code == 304:
                    CRAWL_REQUESTS_TOTAL.labels(status="304", domain=domain).inc()
                    return FetchResponse(
                        url=str(response.url),
                        status_code=304,
                        latency_ms=latency_ms,
                    )

                # Validate Content-Type
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")):
                    CRAWL_REQUESTS_TOTAL.labels(status="skipped_content_type", domain=domain).inc()
                    return FetchResponse(
                        url=str(response.url),
                        status_code=response.status_code,
                        content_type=content_type,
                        error=f"UNSUPPORTED_MIME_TYPE: {content_type}",
                        latency_ms=latency_ms,
                    )

                # Validate content length
                if len(response.content) > settings.CRAWLER_MAX_RESPONSE_SIZE:
                    CRAWL_ERRORS_TOTAL.labels(error_type="oversized", domain=domain).inc()
                    return FetchResponse(
                        url=str(response.url),
                        status_code=response.status_code,
                        error=f"PAGE_OVERSIZED_EXCEEDS_{settings.CRAWLER_MAX_RESPONSE_SIZE}_BYTES",
                        latency_ms=latency_ms,
                    )

                text_content = response.text

                CRAWL_REQUESTS_TOTAL.labels(
                    status=str(response.status_code), domain=domain
                ).inc()

                log_event(
                    "crawl_completed",
                    url=url,
                    status=response.status_code,
                    latency_ms=round(latency_ms, 2),
                    bytes=len(response.content),
                )

                return FetchResponse(
                    url=str(response.url),
                    status_code=response.status_code,
                    content=text_content,
                    content_type=content_type,
                    etag=response.headers.get("ETag"),
                    last_modified=response.headers.get("Last-Modified"),
                    latency_ms=latency_ms,
                )

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout) as e:
                retries += 1
                if retries > settings.CRAWLER_MAX_RETRIES:
                    CRAWL_ERRORS_TOTAL.labels(error_type="timeout_or_connect", domain=domain).inc()
                    return FetchResponse(
                        url=url,
                        status_code=0,
                        latency_ms=(time.perf_counter() - start_time) * 1000.0,
                        error=f"NETWORK_ERROR: {str(e)}",
                    )
                await asyncio.sleep(backoff ** retries)

            except Exception as e:
                CRAWL_ERRORS_TOTAL.labels(error_type="unknown_exception", domain=domain).inc()
                logger.warning(f"Fetch error for {url}: {e}")
                return FetchResponse(
                    url=url,
                    status_code=0,
                    error=f"FETCH_EXCEPTION: {str(e)}",
                )

        return FetchResponse(url=url, status_code=0, error="MAX_RETRIES_EXCEEDED")


fetcher = AsyncFetcher()
