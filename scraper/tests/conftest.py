"""Pytest configuration ensuring proper import paths for both root and scraper tests."""

import sys
from pathlib import Path

# Add project root and scraper directory to sys.path
SCRAPER_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SCRAPER_DIR.parent

for path in (ROOT_DIR, SCRAPER_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
