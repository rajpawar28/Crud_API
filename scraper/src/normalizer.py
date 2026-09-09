"""Normalization functions for cleaning raw book records."""

import re
from typing import Any, Dict, Optional
from urllib.parse import urljoin


def normalize_price(price_text: Optional[str]) -> Optional[float]:
    """Extract numeric float from price string like '£51.77' or 'Â£51.77'."""
    if not price_text:
        return None

    # Match numeric float pattern (digits, optional dot and decimal digits)
    match = re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", ""))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def normalize_url(raw_url: Optional[str], base_url: str = "https://books.toscrape.com/") -> Optional[str]:
    """Convert relative URL to canonical absolute HTTPS URL."""
    if not raw_url:
        return None

    absolute_url = urljoin(base_url, raw_url)
    if absolute_url.startswith("http://books.toscrape.com"):
        absolute_url = absolute_url.replace("http://", "https://", 1)
    return absolute_url


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """Trim leading/trailing whitespace and collapse multiple whitespace characters."""
    if text is None:
        return None
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw record dictionary into the standard schema dictionary."""
    normalized = dict(raw)

    # 1. Title
    if normalized.get("title"):
        normalized["title"] = normalize_whitespace(normalized["title"])

    # 2. Product URL & Source Page (guarantee absolute HTTPS URLs)
    if normalized.get("product_url"):
        normalized["product_url"] = normalize_url(normalized["product_url"])
    if normalized.get("source_page"):
        normalized["source_page"] = normalize_url(normalized["source_page"])

    # 3. Price normalization: compute price_gbp while retaining raw price_text
    price_text = normalized.get("price_text")
    if price_text:
        normalized["price_text"] = price_text.strip()
        normalized["price_gbp"] = normalize_price(price_text)
    else:
        normalized["price_gbp"] = None

    # 4. Availability
    if normalized.get("availability_text"):
        normalized["availability_text"] = normalize_whitespace(normalized["availability_text"])

    # 5. Rating
    if normalized.get("rating_text"):
        normalized["rating_text"] = normalized["rating_text"].strip()

    # 6. Description (normalize whitespace, preserve None if absent)
    if normalized.get("description") is not None:
        normalized["description"] = normalize_whitespace(normalized["description"])

    return normalized
