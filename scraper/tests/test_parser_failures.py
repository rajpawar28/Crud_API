"""Unit tests for malformed HTML tolerance and validation error handling."""

from pathlib import Path
from scraper.src.models import BookRecord
from scraper.src.normalizer import normalize_record
from scraper.src.parser import extract_book_details
from scraper.src.validator import validate_book_record

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_malformed_html_does_not_crash_parser():
    """Verify parser gracefully handles incomplete/broken HTML without throwing unhandled exceptions."""
    malformed_html = (FIXTURES_DIR / "malformed.html").read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/broken-page/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"
    fetched_at = "2026-09-09T10:00:00Z"

    details = extract_book_details(
        html=malformed_html,
        product_url=product_url,
        source_page=source_page,
        fetched_at=fetched_at,
    )

    # Parser extracts what is present and sets missing fields to None
    assert details["product_url"] == product_url
    assert "Incomplete Document" in details["title"]
    assert details["price_text"] == "invalid price text"


def test_extra_whitespace_fixture_normalization():
    """Verify extra whitespace fixture is properly normalized."""
    whitespace_html = (FIXTURES_DIR / "extra_whitespace.html").read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/messy-book/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"
    fetched_at = "2026-09-09T10:00:00Z"

    details = extract_book_details(
        html=whitespace_html,
        product_url=product_url,
        source_page=source_page,
        fetched_at=fetched_at,
    )
    normalized = normalize_record(details)

    assert normalized["title"] == "Messy Title With Spaces"
    assert normalized["price_text"] == "£34.50"
    assert normalized["price_gbp"] == 34.50
    assert normalized["availability_text"] == "In stock (12 available)"
    assert normalized["rating_text"] == "Two"
    assert "This description has multiple lines and erratic spaces." in normalized["description"]


def test_validation_rejects_missing_title():
    """Verify validator rejects records missing required fields."""
    invalid_data = {
        "title": "",  # Empty title
        "product_url": "https://books.toscrape.com/catalogue/book/index.html",
        "price_text": "£10.00",
        "price_gbp": 10.00,
        "availability_text": "In stock",
        "rating_text": "Five",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-09-09T10:00:00Z",
    }
    is_valid, invalid_obj, err = validate_book_record(invalid_data)
    assert not is_valid
    assert "title" in err


def test_validation_rejects_negative_price():
    """Verify validator rejects records with negative price."""
    invalid_data = {
        "title": "Negative Price Book",
        "product_url": "https://books.toscrape.com/catalogue/book/index.html",
        "price_text": "£-5.00",
        "price_gbp": -5.00,
        "availability_text": "In stock",
        "rating_text": "Five",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-09-09T10:00:00Z",
    }
    is_valid, invalid_obj, err = validate_book_record(invalid_data)
    assert not is_valid
    assert "price_gbp" in err
