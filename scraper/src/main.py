"""Main CLI entrypoint for The Polite Scraper pipeline."""

import argparse
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import (
    BASE_URL,
    CATALOGUE_START_URL,
    MAX_CATALOGUE_PAGES,
    OUTPUT_BOOKS_FILE,
    OUTPUT_ERRORS_FILE,
    OUTPUT_REPORT_FILE,
)
from .fetcher import PoliteFetcher
from .models import BookRecord, InvalidRecord
from .normalizer import normalize_record
from .parser import discover_books_on_catalogue, extract_book_details, extract_next_page_url
from .reporter import generate_run_report
from .storage import save_books_json, save_errors_json
from .validator import validate_book_record


def run_pipeline(
    inject_failure: bool = False,
    enable_cache: bool = True,
    max_pages: int = MAX_CATALOGUE_PAGES,
) -> Dict[str, Any]:
    """Execute the complete polite scraping pipeline."""
    start_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_perf = time.perf_counter()

    print("=" * 60)
    print("THE POLITE SCRAPER - Starting Pipeline")
    print(f"Target: {BASE_URL}")
    print(f"Catalogue start: {CATALOGUE_START_URL}")
    print(f"Max catalogue pages: {max_pages}")
    print(f"Inject failure test mode: {inject_failure}")
    print(f"Cache enabled: {enable_cache}")
    print("=" * 60)

    fetcher = PoliteFetcher(enable_cache=enable_cache)

    # 1. Discover catalogue pages and extract book URLs
    current_page_url: Optional[str] = CATALOGUE_START_URL
    catalogue_pages_visited = 0
    discovered_urls: List[str] = []
    page_source_map: Dict[str, str] = {}  # book_url -> source_catalogue_page

    while current_page_url and catalogue_pages_visited < max_pages:
        catalogue_pages_visited += 1
        print(f"\n[Catalogue Page {catalogue_pages_visited}/{max_pages}] {current_page_url}")
        res = fetcher.fetch(current_page_url, is_catalogue=True)

        if not res.is_success:
            print(f"ERROR: Failed to fetch catalogue page {current_page_url} (status={res.status_code})")
            break

        page_books = discover_books_on_catalogue(res.html or "", current_page_url)
        for b_url in page_books:
            discovered_urls.append(b_url)
            if b_url not in page_source_map:
                page_source_map[b_url] = current_page_url

        # Follow pagination
        current_page_url = extract_next_page_url(res.html or "", current_page_url)

    # Deduplicate canonical product URLs while preserving discovery order
    unique_urls = list(dict.fromkeys(discovered_urls))

    print("\n--- Discovery Checkpoint ---")
    print(f"catalogue_pages={catalogue_pages_visited}")
    print(f"discovered={len(discovered_urls)}")
    print(f"unique_urls={len(unique_urls)}")
    print("----------------------------\n")

    # If --inject-failure is specified, replace the first URL with a non-existent fake URL
    detail_urls_to_process = list(unique_urls)
    if inject_failure:
        fake_url = "https://books.toscrape.com/catalogue/this-page-does-not-exist/index.html"
        print(f"[TEST INJECTION] Replacing first book URL with fake URL for broken page test:\n -> {fake_url}\n")
        if detail_urls_to_process:
            detail_urls_to_process[0] = fake_url
            page_source_map[fake_url] = CATALOGUE_START_URL

    # 2. Fetch detail pages, extract raw fields, normalize, validate
    valid_records: List[BookRecord] = []
    invalid_records: List[InvalidRecord] = []
    failed_pages_count = 0

    print(f"Visiting {len(detail_urls_to_process)} book detail pages...")
    for idx, book_url in enumerate(detail_urls_to_process, 1):
        source_page = page_source_map.get(book_url, CATALOGUE_START_URL)
        book_res = fetcher.fetch(book_url, is_catalogue=False)

        # Handle page failure gracefully (survive 1 or more broken pages)
        if not book_res.is_success:
            failed_pages_count += 1
            err_msg = f"Failed to fetch detail page: HTTP {book_res.status_code} ({book_res.error_message})"
            print(f"[{idx}/{len(detail_urls_to_process)}] SKIPPED (Broken Page): {book_url} - {err_msg}")
            invalid_records.append(
                InvalidRecord(
                    record={"product_url": book_url, "source_page": source_page},
                    error=err_msg,
                )
            )
            continue

        # Extract 8 raw fields
        raw_fields = extract_book_details(
            html=book_res.html or "",
            product_url=book_url,
            source_page=source_page,
            fetched_at=book_res.fetched_at,
        )

        # Normalize fields
        normalized = normalize_record(raw_fields)

        # Validate with Pydantic
        is_valid, record_obj, error_str = validate_book_record(normalized)
        if is_valid:
            valid_records.append(record_obj)
        else:
            invalid_records.append(record_obj)
            print(f"[{idx}/{len(detail_urls_to_process)}] VALIDATION FAILED for {book_url}: {error_str}")

    # 3. Store records idempotently
    saved_books_count = save_books_json(valid_records, OUTPUT_BOOKS_FILE)
    saved_errors_count = save_errors_json(invalid_records, OUTPUT_ERRORS_FILE)

    duration = round(time.perf_counter() - start_perf, 2)

    # 4. Generate run report
    report_dict = {
        "start_time": start_time_iso,
        "duration_seconds": duration,
        "pages_fetched": fetcher.pages_fetched_count,
        "cache_hits": fetcher.cache_hits_count,
        "valid_records": saved_books_count,
        "invalid_records": saved_errors_count,
        "failed_pages": failed_pages_count,
        "catalogue_pages": catalogue_pages_visited,
        "discovered_urls": len(discovered_urls),
        "unique_urls": len(unique_urls),
        "retries": fetcher.retries_count,
        "failure_injected": inject_failure,
    }

    generate_run_report(report_dict, OUTPUT_REPORT_FILE)

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Duration:          {duration}s")
    print(f"Pages Fetched:     {fetcher.pages_fetched_count}")
    print(f"Cache Hits:        {fetcher.cache_hits_count}")
    print(f"Valid Books:       {saved_books_count}")
    print(f"Invalid Records:   {saved_errors_count}")
    print(f"Failed Pages:      {failed_pages_count}")
    print(f"Books JSON:        {OUTPUT_BOOKS_FILE}")
    print(f"Errors JSON:       {OUTPUT_ERRORS_FILE}")
    print(f"Run Report JSON:   {OUTPUT_REPORT_FILE}")
    print("=" * 60 + "\n")

    return report_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="The Polite Scraper - Books to Scrape")
    parser.add_argument(
        "--inject-failure",
        action="store_true",
        help="Inject a fake broken page URL to test failure survival and error reporting.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable disk caching and perform live HTTP requests.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=MAX_CATALOGUE_PAGES,
        help="Number of catalogue pages to scrape (default: 3).",
    )
    args = parser.parse_args()

    run_pipeline(
        inject_failure=args.inject_failure,
        enable_cache=not args.no_cache,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()
