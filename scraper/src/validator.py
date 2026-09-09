"""Validation layer utilizing Pydantic to ensure schema integrity."""

from typing import Any, Dict, List, Tuple
from pydantic import ValidationError

from .models import BookRecord, InvalidRecord


def validate_book_record(data: Dict[str, Any]) -> Tuple[bool, Any, str]:
    """Validate a single normalized dictionary against BookRecord schema.

    Returns:
        (is_valid, record_or_invalid_record, error_message)
    """
    try:
        record = BookRecord(**data)
        return True, record, ""
    except ValidationError as e:
        error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        invalid = InvalidRecord(record=data, error=error_msg)
        return False, invalid, error_msg
    except Exception as e:
        invalid = InvalidRecord(record=data, error=str(e))
        return False, invalid, str(e)
