
"""SQLite persistence and comparison for Checkov scan reports."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "scans.db"
DB_PATH = Path(os.getenv("SECURECLOUDLAB_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the scan history schema if it does not exist."""
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                total_findings INTEGER NOT NULL,
                severity_counts TEXT NOT NULL,
                findings_json TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_scanned_at
            ON scans(scanned_at)
        """)


def save_scan(
    findings: list[dict[str, Any]],
    target: str = "terraform",
    status: str = "completed",
    severity_counts: dict[str, int] | None = None,
) -> int:
    """Persist a scan and return its database ID."""
    from dashboard.services.findings_service import severity_counts as count_severities

    counts = severity_counts or count_severities(findings)
    scanned_at = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO scans (
                scanned_at, target, status, total_findings,
                severity_counts, findings_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                scanned_at,
                target,
                status,
                len(findings),
                json.dumps(counts),
                json.dumps(findings),
            ),
        )
        return int(cursor.lastrowid)


def list_scans(limit: int = 20) -> list[dict[str, Any]]:
    """Return the newest scan summaries."""
    limit = max(1, min(limit, 200))
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, scanned_at, target, status, total_findings,
                   severity_counts
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["severity_counts"] = json.loads(item["severity_counts"])
        result.append(item)
    return result


def get_scan(scan_id: int) -> dict[str, Any] | None:
    """Return one scan with its complete findings."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM scans WHERE id = ?",
            (scan_id,),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["severity_counts"] = json.loads(result["severity_counts"])
    result["findings"] = json.loads(result.pop("findings_json"))
    return result


def get_trends(limit: int = 30) -> list[dict[str, Any]]:
    """Return chronological scan counts for trend visualizations."""
    scans = list_scans(limit)
    return list(reversed(scans))


def compare_scans(old_scan_id: int, new_scan_id: int) -> dict[str, Any] | None:
    """Compare findings using check ID, file path and resource as identity."""
    old_scan = get_scan(old_scan_id)
    new_scan = get_scan(new_scan_id)

    if old_scan is None or new_scan is None:
        return None

    def identity(finding: dict[str, Any]) -> tuple[str, str, str]:
        return (
            str(finding.get("check_id", "UNKNOWN")),
            str(finding.get("file_path", "Unknown")),
            str(finding.get("resource", "Unknown")),
        )

    old_findings = {identity(f): f for f in old_scan["findings"]}
    new_findings = {identity(f): f for f in new_scan["findings"]}

    resolved = [
        old_findings[key] for key in old_findings.keys() - new_findings.keys()
    ]
    introduced = [
        new_findings[key] for key in new_findings.keys() - old_findings.keys()
    ]
    unchanged = [
        new_findings[key] for key in old_findings.keys() & new_findings.keys()
    ]

    return {
        "old_scan_id": old_scan_id,
        "new_scan_id": new_scan_id,
        "resolved_count": len(resolved),
        "introduced_count": len(introduced),
        "unchanged_count": len(unchanged),
        "resolved": resolved,
        "introduced": introduced,
        "unchanged": unchanged,
    }
