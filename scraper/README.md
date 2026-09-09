# The Polite Scraper

A reliable, polite, cache-aware, schema-validated, and failure-resilient web scraping pipeline built in Python. Designed to extract book details across the first 3 catalogue pages of the Books to Scrape sandbox while strictly adhering to ethical web scraping best practices.

---

## Target Classification

- **Target**: Books to Scrape (https://books.toscrape.com/)
- **Why it is appropriate**: `https://toscrape.com/` explicitly designates Books to Scrape as an open educational sandbox intended specifically for web scraping practice and benchmarking.
- **Scope**: First 3 catalogue pages only (`catalogue/page-1.html` → `catalogue/page-2.html` → `catalogue/page-3.html`).
- **Expected books**: Exactly 60 unique books (20 items per catalogue page).
- **Data collected**: 8 raw fields (`title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, `fetched_at`) along with normalized `price_gbp`.
- **robots.txt result**: Checked `https://books.toscrape.com/robots.txt` on 2026-09-09 — returned HTTP `404 Not Found` ("no robots file found").

> **Ethical Commitment**:
> "I will not reuse this code on another site without checking its rules and terms first."
>
> A missing `robots.txt` file is not an implicit carte blanche to overload or scrape an arbitrary target. All web scraping operations must respect server capacity, terms of service, rate limits, and copyright.
