"""Execution summary reporter for generating output/run-report.json."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .config import OUTPUT_DIR, OUTPUT_REPORT_FILE


class RunReportData(BaseModel):
    """Schema for run-report.json."""

    start_time: str
    duration_seconds: float
    pages_fetched: int
    cache_hits: int
    valid_records: int
    invalid_records: int
    failed_pages: int
    catalogue_pages: int
    discovered_urls: int
    unique_urls: int
    retries: int = 0
    failure_injected: bool = False


def generate_run_report(
    report_data: Dict[str, Any],
    output_path: Path = OUTPUT_REPORT_FILE,
) -> Dict[str, Any]:
    """Validate and write the run report to output/run-report.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    validated = RunReportData(**report_data)
    data = validated.model_dump()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data
