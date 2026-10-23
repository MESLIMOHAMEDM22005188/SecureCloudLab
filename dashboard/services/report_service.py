import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


# SecureCloudLab project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "dashboard" / "reports"


def ensure_reports_directory() -> None:
    """Create the reports directory if it does not exist."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_report(
    report_type: str,
    report_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Save a security scan report as a JSON file.

    Args:
        report_type: Type of scan, such as 'checkov', 'terraform',
                     or 'negative-test'.
        report_data: Results returned by the scan service.

    Returns:
        A dictionary containing the saved report metadata.
    """
    ensure_reports_directory()

    timestamp = datetime.now(timezone.utc)
    report_id = f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"

    report = {
        "id": report_id,
        "type": report_type,
        "timestamp": timestamp.isoformat(),
        "data": report_data,
    }

    report_path = REPORTS_DIR / f"{report_id}.json"

    try:
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Failed to save report: {exc}") from exc

    return {
        "id": report_id,
        "type": report_type,
        "timestamp": report["timestamp"],
        "file": report_path.name,
    }


def list_reports(limit: int = 50) -> list[dict[str, Any]]:
    """
    Return the most recent reports, newest first.

    Args:
        limit: Maximum number of reports to return.
    """
    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    ensure_reports_directory()
    reports = []

    for report_path in REPORTS_DIR.glob("*.json"):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))

            reports.append({
                "id": report.get("id", report_path.stem),
                "type": report.get("type", "unknown"),
                "timestamp": report.get("timestamp"),
                "file": report_path.name,
            })

        except (OSError, json.JSONDecodeError):
            # Ignore unreadable or invalid report files.
            continue

    reports.sort(
        key=lambda item: item.get("timestamp") or "",
        reverse=True,
    )

    return reports[:limit]


def get_report(report_id: str) -> dict[str, Any] | None:
    """
    Retrieve a report by its ID.

    Returns None if the report does not exist or is invalid.
    """
    # Restrict IDs to prevent path traversal.
    if (
        not report_id
        or len(report_id) > 64
        or any(char not in "abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in report_id)
    ):
        return None

    report_path = REPORTS_DIR / f"{report_id}.json"

    if not report_path.is_file():
        return None

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    return report if isinstance(report, dict) else None


def delete_report(report_id: str) -> bool:
    """
    Delete a report by its ID.

    Returns True if the report was deleted, otherwise False.
    """
    if get_report(report_id) is None:
        return False

    report_path = REPORTS_DIR / f"{report_id}.json"

    try:
        report_path.unlink()
        return True
    except OSError:
        return False