"""Unit tests verifying missing descriptions are safely parsed as None."""

from pathlib import Path
from scraper.src.parser import extract_book_details

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "missing_description.html"


def test_missing_description_parsed_as_none():
    """Verify parser returns description=None when description paragraph is absent."""
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/test-book/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"
    fetched_at = "2026-09-09T10:00:00Z"

    details = extract_book_details(
        html=html,
        product_url=product_url,
        source_page=source_page,
        fetched_at=fetched_at,
    )

    assert details["title"] == "Book Without Description"
    assert details["price_text"] == "£19.99"
    assert details["availability_text"] == "In stock (5 available)"
    assert details["rating_text"] == "Four"
    assert details["description"] is None
    assert details["product_url"] == product_url
    assert details["source_page"] == source_page
    assert details["fetched_at"] == fetched_at
