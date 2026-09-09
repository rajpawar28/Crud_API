"""File storage operations for saving validated books and errors idempotently."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from .config import OUTPUT_BOOKS_FILE, OUTPUT_DIR, OUTPUT_ERRORS_FILE
from .models import BookRecord, InvalidRecord


def save_books_json(
    records: List[Union[BookRecord, Dict[str, Any]]],
    output_path: Path = OUTPUT_BOOKS_FILE,
) -> int:
    """Save validated book records to JSON file with deduplication by product_url.

    Returns:
        Number of unique records written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Deduplicate records by canonical product_url
    deduped_map: Dict[str, Dict[str, Any]] = {}
    for item in records:
        if isinstance(item, BookRecord):
            data = item.model_dump()
        else:
            data = dict(item)

        url = data.get("product_url")
        if url:
            deduped_map[url] = data

    unique_records = list(deduped_map.values())

    # Write formatted JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_records, f, indent=2, ensure_ascii=False)

    return len(unique_records)


def save_errors_json(
    errors: List[Union[InvalidRecord, Dict[str, Any]]],
    output_path: Path = OUTPUT_ERRORS_FILE,
) -> int:
    """Save invalid records and errors to errors.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    error_data: List[Dict[str, Any]] = []
    for item in errors:
        if isinstance(item, InvalidRecord):
            error_data.append(item.model_dump())
        else:
            error_data.append(dict(item))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(error_data, f, indent=2, ensure_ascii=False)

    return len(error_data)
