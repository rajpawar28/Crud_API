"""HTML parsing routines for catalogue discovery and book detail extraction using BeautifulSoup."""

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def discover_books_on_catalogue(html: str, page_url: str) -> List[str]:
    """Find and return all absolute book URLs from a catalogue page HTML."""
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    book_urls: List[str] = []

    # Target specific product pod container
    for pod in soup.select("article.product_pod"):
        link_tag = pod.select_one("h3 a")
        if link_tag and link_tag.get("href"):
            raw_href = link_tag["href"]
            # Convert relative URL to canonical absolute URL
            absolute_url = urljoin(page_url, raw_href)
            book_urls.append(absolute_url)

    return book_urls


def extract_next_page_url(html: str, current_url: str) -> Optional[str]:
    """Find the next page pagination URL if present on the catalogue page."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    next_tag = soup.select_one("li.next a")
    if next_tag and next_tag.get("href"):
        return urljoin(current_url, next_tag["href"])

    return None


def extract_book_details(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> Dict[str, Any]:
    """Extract the required 8 raw fields from a book detail page HTML."""
    if not html:
        return {
            "title": None,
            "product_url": product_url,
            "price_text": None,
            "availability_text": None,
            "rating_text": None,
            "description": None,
            "source_page": source_page,
            "fetched_at": fetched_at,
        }

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title (product information / title)
    title_tag = soup.select_one(".product_main h1")
    if not title_tag:
        title_tag = soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # 2. Price (product price section)
    price_tag = soup.select_one(".product_main .price_color")
    if not price_tag:
        price_tag = soup.select_one(".price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else None

    # 3. Availability (stock availability section)
    avail_tag = soup.select_one(".product_main .availability")
    if not avail_tag:
        avail_tag = soup.select_one(".availability")
    availability_text = " ".join(avail_tag.get_text().split()) if avail_tag else None

    # 4. Rating (star-rating semantic class)
    rating_tag = soup.select_one(".product_main .star-rating")
    if not rating_tag:
        rating_tag = soup.select_one(".star-rating")
    rating_text = None
    if rating_tag:
        classes = rating_tag.get("class", [])
        for cls in classes:
            if cls != "star-rating":
                rating_text = cls
                break

    # 5. Description (product description paragraph following #product_description)
    desc_header = soup.select_one("#product_description")
    description = None
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            raw_desc = desc_p.get_text(strip=True)
            description = raw_desc if raw_desc else None

    # Return exactly the 8 raw fields
    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
