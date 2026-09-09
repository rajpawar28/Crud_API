"""Configuration parameters and paths for the scraper."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_CATALOGUE_DIR = CACHE_DIR / "catalogue"
CACHE_BOOKS_DIR = CACHE_DIR / "books"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_BOOKS_FILE = OUTPUT_DIR / "books.json"
OUTPUT_ERRORS_FILE = OUTPUT_DIR / "errors.json"
OUTPUT_REPORT_FILE = OUTPUT_DIR / "run-report.json"

# Web Scraping Configuration
BASE_URL = "https://books.toscrape.com/"
CATALOGUE_START_URL = "https://books.toscrape.com/catalogue/page-1.html"
ROBOTS_TXT_URL = "https://books.toscrape.com/robots.txt"

# Politeness Settings
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/rajpawar28/Crud_API)"
REQUEST_TIMEOUT_SECONDS = 10.0
MIN_REQUEST_DELAY_SECONDS = 0.5  # 500ms delay between real requests

# Limits
MAX_CATALOGUE_PAGES = 3
EXPECTED_UNIQUE_BOOKS = 60
