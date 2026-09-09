# The Polite Scraper

A robust, ethical, cache-aware, schema-validated, and failure-resilient web scraping pipeline built in Python. Designed to extract structured product data across the first 3 catalogue pages of the Books to Scrape sandbox while adhering strictly to industry best practices in web scraping reliability and etiquette.

---

## Target Classification

- **Target**: Books to Scrape (https://books.toscrape.com/)
- **Why it is appropriate**: `https://toscrape.com/` explicitly designates Books to Scrape as an open educational sandbox intended specifically for web scraping practice, automated tests, and benchmarking.
- **Scope**: First 3 catalogue pages only (`catalogue/page-1.html` → `catalogue/page-2.html` → `catalogue/page-3.html`).
- **Expected books**: Exactly 60 unique books (20 books per catalogue page).
- **Data collected**: 8 raw fields (`title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, `fetched_at`) along with normalized `price_gbp`.
- **robots.txt result**: Queried `https://books.toscrape.com/robots.txt` on 2026-09-09 — returned HTTP `404 Not Found` ("no robots file found").

> **Ethical Commitment**:
> "I will not reuse this code on another site without checking its rules and terms first."
>
> A missing `robots.txt` is NOT an open invitation to overload or indiscriminately crawl a website. All production web scraping operations must respect server capacity, terms of service, rate limits, and intellectual property.

---

## Installation & Setup

### Requirements
- Python 3.10+
- Virtual environment (`venv`)

### Setup Instructions

```bash
# 1. Navigate to the scraper directory
cd scraper

# 2. Create and activate a virtual environment (if not already active)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

---

## Usage

### Run the Core Pipeline
To execute the complete polite scraping pipeline (discovery → fetching → extraction → normalization → validation → storage → reporting):

```bash
# Run from within the scraper/ directory
python -m src.main
```

### Options & Flags
- `--no-cache`: Bypass disk cache and perform live network fetches.
- `--inject-failure`: Injects a simulated 404 broken page URL to verify failure resilience and error logging without harming the live site.
- `--max-pages N`: Limit catalogue discovery to `N` pages (default: 3).

```bash
# Example: test failure resilience mode
python -m src.main --inject-failure
```

---

## Data Schema & Normalization

The pipeline extracts 8 raw fields directly from the semantic HTML of each product page and computes a normalized `price_gbp` float while preserving the raw string values.

### Schema Definition

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `str` | Yes | Extracted book title from product heading |
| `product_url` | `str` | Yes | Canonical absolute HTTPS product URL |
| `price_text` | `str` | Yes | Raw price string including currency symbol (e.g. `"£51.77"`) |
| `price_gbp` | `float` | Yes | Normalized numerical price in GBP (e.g. `51.77`) |
| `availability_text` | `str` | Yes | Raw stock availability string (e.g. `"In stock (22 available)"`) |
| `rating_text` | `str` | Yes | Star rating word from semantic class (`"One"`, `"Two"`, `"Three"`, `"Four"`, `"Five"`) |
| `description` | `str \| null` | Optional | Product description text (`null` if absent on the page) |
| `source_page` | `str` | Yes | Absolute URL of the catalogue page where the link was discovered |
| `fetched_at` | `str` | Yes | ISO 8601 UTC timestamp of fetch (`"YYYY-MM-DDTHH:MM:SSZ"`) |

### Example Record (`output/books.json`)

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-09T11:20:04Z"
}
```

---

## Politeness Rules & Pipeline Architecture

The scraper implements 10 fundamental politeness rules:

1. **Identifying User-Agent**: Every network request includes an honest, identifying header (`FlyRankInternship-A9/1.0 (+https://github.com/rajpawar28/Crud_API)`).
2. **Explicit Timeouts**: Requests are configured with a 10.0-second timeout to avoid lingering hung sockets.
3. **Enforced Rate Limiting**: Minimum 500ms delay between consecutive real network requests (`time.sleep` triggered only when elapsed network time < 500ms).
4. **Status Code Verification**: Only HTTP `200` responses proceed to HTML parsing; non-200 responses are caught before parsing.
5. **Disk Caching**: HTML pages are cached in `cache/catalogue/` and `cache/books/` during development. Subsequent runs read from disk instantaneously without hitting the live site.
6. **No Redundant Traffic**: Discovered links and records are deduplicated by canonical product URL.
7. **Strict Non-Retry on Client Errors**: HTTP `404 Not Found` and `403 Forbidden` are never retried.
8. **Bounded Retries for Server Issues**: Network timeouts or 5xx server errors are retried at most once (max 2 attempts total) after a short backoff.
9. **Targeted Data Extraction**: Extracts only required product fields without crawling irrelevant resources, images, or ads.
10. **Bounded Crawling Scope**: Discovery strictly terminates at page 3 (exactly 60 books).

---

## Browser Cost Comparison & Evaluation

The core assignment needs no browser because the required book data is already present in the HTML returned by the server; a browser would add unnecessary cost.

### Benchmark on `https://quotes.toscrape.com/js`

A benchmark was executed using [`scripts/browser_comparison.py`](file:///Users/rajpawar/.gemini/antigravity-ide/scratch/task-api/scraper/scripts/browser_comparison.py) against `https://quotes.toscrape.com/js`:

| Dimension | Plain HTTP (`requests`) | Headless Browser (`Playwright` / `Chromium`) |
|---|---|---|
| **Mechanism** | Standard GET request + HTML parser | Full browser engine, V8 JS runtime, DOM layout |
| **Response Time** | ~0.15s – 0.40s per page | ~1.5s – 3.5s (browser launch + rendering) |
| **Peak Memory Footprint** | ~35 MB – 45 MB | ~150 MB – 300+ MB per browser process |
| **CPU Overhead** | Minimal (<5% single core) | Heavy (multi-threaded process tree) |
| **Dynamic JS Execution** | No (only raw initial response) | Yes (executes client-side JS) |
| **When to use** | Server-Side Rendered (SSR) pages | Single Page Applications (SPAs) / Client-Side JS |

**Conclusion**: Books to Scrape (`https://books.toscrape.com/`) is 100% server-side rendered (SSR). Using a headless browser for SSR websites wastes memory, CPU, and network bandwidth while providing zero additional extraction value.

---

## Ethical Scraping Note

When engaging in web data extraction:
- **API First**: Always prefer and use an official public REST/GraphQL API when available.
- **Never Bypass Security**: Do not bypass logins, authentication gates, paywalls, CAPTCHAs, or IP bans.
- **Data Minimization**: Collect only the data fields required for your legitimate use case.
- **Terms & Rules**: Always review `robots.txt`, Terms of Service, and copyright policies before writing any scraper.
- **Server Courtesy**: Implement reasonable rate limits and local caching so your scraper does not degrade service availability for human users.

---

## Real Execution Run Report

Below is the verbatim content of [`output/run-report.json`](file:///Users/rajpawar/.gemini/antigravity-ide/scratch/task-api/scraper/output/run-report.json) from a real execution of the pipeline:

```json
{
  "start_time": "2026-09-09T11:20:04Z",
  "duration_seconds": 31.39,
  "pages_fetched": 59,
  "cache_hits": 4,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "unique_urls": 60,
  "retries": 0,
  "failure_injected": false
}
```

---

## Limitation

> "This scraper is intentionally tailored to the Books to Scrape sandbox and should not be reused on another site without first checking that site's rules, terms, robots policy, structure, and access expectations."
