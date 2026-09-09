"""Unit tests for URL resolution and canonicalization."""

from urllib.parse import urljoin
from scraper.src.normalizer import normalize_url


def test_relative_to_absolute_url():
    """Verify relative book link is correctly resolved to full HTTPS URL."""
    base_page = "https://books.toscrape.com/catalogue/page-1.html"
    relative_link = "a-light-in-the-attic_1000/index.html"
    absolute = urljoin(base_page, relative_link)
    assert absolute == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_parent_relative_link_resolution():
    """Verify ../ relative link resolves correctly."""
    base_page = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
    relative_link = "../../../its-only-the-himalayas_981/index.html"
    absolute = urljoin(base_page, relative_link)
    assert absolute == "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"


def test_normalize_url_https_enforcement():
    """Verify HTTP URLs are upgraded to HTTPS for books.toscrape.com."""
    http_url = "http://books.toscrape.com/catalogue/book_1/index.html"
    assert normalize_url(http_url) == "https://books.toscrape.com/catalogue/book_1/index.html"
