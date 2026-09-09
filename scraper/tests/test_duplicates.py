"""Unit tests verifying deduplication and idempotency behavior."""

import tempfile
from pathlib import Path
from scraper.src.models import BookRecord
from scraper.src.storage import save_books_json


def test_duplicate_records_deduplicated_by_product_url():
    """Verify writing duplicate records produces a single unique canonical entry in JSON."""
    rec1 = BookRecord(
        title="Book One",
        product_url="https://books.toscrape.com/catalogue/book-one/index.html",
        price_text="£10.00",
        price_gbp=10.00,
        availability_text="In stock",
        rating_text="Three",
        description="First description",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-09-09T10:00:00Z",
    )

    rec2 = BookRecord(
        title="Book One Updated",
        product_url="https://books.toscrape.com/catalogue/book-one/index.html",
        price_text="£10.00",
        price_gbp=10.00,
        availability_text="In stock",
        rating_text="Three",
        description="Second description",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-09-09T10:05:00Z",
    )

    rec3 = BookRecord(
        title="Book Two",
        product_url="https://books.toscrape.com/catalogue/book-two/index.html",
        price_text="£20.00",
        price_gbp=20.00,
        availability_text="In stock",
        rating_text="Five",
        description=None,
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-09-09T10:00:00Z",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "test_books.json"
        # Pass 3 records containing 1 duplicate URL
        count = save_books_json([rec1, rec2, rec3], output_path=tmp_file)
        assert count == 2
