"""Unit tests for price, whitespace, and record normalization."""

from scraper.src.normalizer import normalize_price, normalize_record, normalize_whitespace


def test_normalize_price_valid():
    """Verify price string with pound symbol converts to float."""
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("Â£51.77") == 51.77
    assert normalize_price("£0.99") == 0.99
    assert normalize_price("12.50") == 12.50


def test_normalize_price_invalid():
    """Verify invalid or empty price string returns None."""
    assert normalize_price(None) is None
    assert normalize_price("") is None
    assert normalize_price("Free") is None
    assert normalize_price("N/A") is None


def test_normalize_whitespace():
    """Verify whitespace trimming and multiple space collapsing."""
    assert normalize_whitespace("  hello   world  ") == "hello world"
    assert normalize_whitespace("\n\t Messy \t text \n") == "Messy text"
    assert normalize_whitespace(None) is None
    assert normalize_whitespace("   ") is None


def test_normalize_record_preserves_raw_and_adds_gbp():
    """Verify normalization retains price_text and generates price_gbp."""
    raw = {
        "title": "  A Great Book  ",
        "product_url": "catalogue/book_1/index.html",
        "price_text": "£25.00",
        "availability_text": " In stock (10 available) ",
        "rating_text": "Five",
        "description": "  A cool description.  ",
        "source_page": "catalogue/page-1.html",
        "fetched_at": "2026-09-09T10:00:00Z",
    }
    normalized = normalize_record(raw)
    assert normalized["title"] == "A Great Book"
    assert normalized["price_text"] == "£25.00"
    assert normalized["price_gbp"] == 25.00
    assert normalized["product_url"] == "https://books.toscrape.com/catalogue/book_1/index.html"
    assert normalized["source_page"] == "https://books.toscrape.com/catalogue/page-1.html"
    assert normalized["description"] == "A cool description."
