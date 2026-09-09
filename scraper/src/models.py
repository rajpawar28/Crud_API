"""Pydantic schemas for validated book records and run reporting."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BookRecord(BaseModel):
    """Validated schema for a scraped book record."""

    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute product URL")
    price_text: str = Field(..., min_length=1, description="Raw price text with currency")
    price_gbp: float = Field(..., ge=0.0, description="Normalized price in GBP")
    availability_text: str = Field(..., min_length=1, description="Raw stock availability string")
    rating_text: str = Field(..., min_length=1, description="Star rating word e.g. Three")
    description: Optional[str] = Field(default=None, description="Product description text or null")
    source_page: str = Field(..., description="Source catalogue page URL")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp of fetch")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v or not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"URL must be an absolute HTTP/HTTPS URL, got '{v}'")
        # Ensure canonical HTTPS
        if v.startswith("http://books.toscrape.com"):
            return v.replace("http://", "https://", 1)
        return v

    @field_validator("price_gbp")
    @classmethod
    def validate_positive_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price_gbp cannot be negative")
        return v

    model_config = {
        "extra": "ignore",
    }


class InvalidRecord(BaseModel):
    """Schema for recording invalid or failed records."""

    record: Dict[str, Any]
    error: str
