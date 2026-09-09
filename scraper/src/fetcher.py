"""Polite HTTP fetcher with disk caching, rate limiting, and retry policies."""

import hashlib
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
import requests

from .config import (
    CACHE_BOOKS_DIR,
    CACHE_CATALOGUE_DIR,
    MIN_REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)


class FetchResult:
    def __init__(
        self,
        url: str,
        html: Optional[str],
        status_code: Optional[int],
        is_cache_hit: bool,
        fetched_at: str,
        error_message: Optional[str] = None,
        retries: int = 0,
    ):
        self.url = url
        self.html = html
        self.status_code = status_code
        self.is_cache_hit = is_cache_hit
        self.fetched_at = fetched_at
        self.error_message = error_message
        self.retries = retries

    @property
    def is_success(self) -> bool:
        return self.html is not None and self.status_code == 200


class PoliteFetcher:
    """Polite HTTP fetcher adhering to strict ethical scraping constraints."""

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        delay: float = MIN_REQUEST_DELAY_SECONDS,
        catalogue_cache_dir: Path = CACHE_CATALOGUE_DIR,
        books_cache_dir: Path = CACHE_BOOKS_DIR,
        enable_cache: bool = True,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.delay = delay
        self.catalogue_cache_dir = catalogue_cache_dir
        self.books_cache_dir = books_cache_dir
        self.enable_cache = enable_cache

        self.last_request_time: float = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        # Metrics
        self.pages_fetched_count: int = 0
        self.cache_hits_count: int = 0
        self.failed_pages_count: int = 0
        self.retries_count: int = 0

        # Ensure cache directories exist
        if self.enable_cache:
            self.catalogue_cache_dir.mkdir(parents=True, exist_ok=True)
            self.books_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str, is_catalogue: bool) -> Path:
        """Derive a deterministic, safe cache file path from a URL."""
        # Use URL hash + sanitized slug
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", url.split("/")[-2] if url.endswith("/index.html") else url.split("/")[-1])
        filename = f"{sanitized}_{url_hash}.html"
        target_dir = self.catalogue_cache_dir if is_catalogue else self.books_cache_dir
        return target_dir / filename

    def _wait_for_rate_limit(self) -> None:
        """Enforce minimum delay between real HTTP requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def fetch(self, url: str, is_catalogue: bool = False) -> FetchResult:
        """Fetch HTML content from cache or via polite network request."""
        cache_path = self._get_cache_path(url, is_catalogue=is_catalogue)

        # 1. Check disk cache
        if self.enable_cache and cache_path.exists():
            try:
                html = cache_path.read_text(encoding="utf-8")
                self.cache_hits_count += 1
                now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"CACHE HIT {url} (bytes={len(html)})")
                return FetchResult(
                    url=url,
                    html=html,
                    status_code=200,
                    is_cache_hit=True,
                    fetched_at=now_iso,
                )
            except Exception as e:
                # If cache reading fails, fallback to network
                print(f"Cache read error for {url}: {e}, falling back to network.")

        # 2. Perform network request with retry policy
        max_attempts = 2  # 1 initial attempt + max 1 retry for timeout/5xx
        attempt = 0
        retries_done = 0

        while attempt < max_attempts:
            attempt += 1
            self._wait_for_rate_limit()
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                self.pages_fetched_count += 1
                resp = self.session.get(url, timeout=self.timeout)
                status = resp.status_code

                if status == 200:
                    resp.encoding = resp.apparent_encoding or "utf-8"
                    html = resp.text
                    print(f"FETCH {url} status={status} bytes={len(html)}")
                    if self.enable_cache:
                        cache_path.write_text(html, encoding="utf-8")
                    return FetchResult(
                        url=url,
                        html=html,
                        status_code=status,
                        is_cache_hit=False,
                        fetched_at=now_iso,
                        retries=retries_done,
                    )

                # Do NOT retry 404 or 403
                if status in (403, 404):
                    print(f"FETCH {url} status={status} (Not retrying client error {status})")
                    self.failed_pages_count += 1
                    return FetchResult(
                        url=url,
                        html=None,
                        status_code=status,
                        is_cache_hit=False,
                        fetched_at=now_iso,
                        error_message=f"HTTP {status}",
                        retries=retries_done,
                    )

                # 5xx Server Error: retry once if attempt 1
                if status >= 500 and attempt < max_attempts:
                    print(f"FETCH {url} status={status} (Server error, retrying once...)")
                    retries_done += 1
                    self.retries_count += 1
                    time.sleep(1.0)
                    continue

                # Any other non-200 status
                print(f"FETCH {url} status={status} (Failed)")
                self.failed_pages_count += 1
                return FetchResult(
                    url=url,
                    html=None,
                    status_code=status,
                    is_cache_hit=False,
                    fetched_at=now_iso,
                    error_message=f"HTTP {status}",
                    retries=retries_done,
                )

            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt < max_attempts:
                    print(f"FETCH {url} error={type(e).__name__} (Network issue, retrying once...)")
                    retries_done += 1
                    self.retries_count += 1
                    time.sleep(1.0)
                    continue
                else:
                    print(f"FETCH {url} failed after retry: {e}")
                    self.failed_pages_count += 1
                    return FetchResult(
                        url=url,
                        html=None,
                        status_code=None,
                        is_cache_hit=False,
                        fetched_at=now_iso,
                        error_message=str(e),
                        retries=retries_done,
                    )
            except Exception as e:
                print(f"FETCH {url} unexpected error: {e}")
                self.failed_pages_count += 1
                return FetchResult(
                    url=url,
                    html=None,
                    status_code=None,
                    is_cache_hit=False,
                    fetched_at=now_iso,
                    error_message=str(e),
                    retries=retries_done,
                )

        self.failed_pages_count += 1
        return FetchResult(
            url=url,
            html=None,
            status_code=None,
            is_cache_hit=False,
            fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            error_message="Exceeded max attempts",
            retries=retries_done,
        )
