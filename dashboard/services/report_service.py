import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "dashboard" / "reports"
DATABASE_PATH = PROJECT_ROOT / "dashboard" / "reports.db"


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data_json TEXT NOT NULL
        )
    """)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(timestamp DESC)"
    )
    return connection


def _migrate_json_reports(connection: sqlite3.Connection) -> None:
    """Import legacy JSON reports once; preserve existing local history."""
    if not REPORTS_DIR.is_dir():
        return
    for path in REPORTS_DIR.glob("*.json"):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(report, dict) or not isinstance(report.get("data"), dict):
                continue
            report_id = str(report.get("id") or path.stem)
            report_type = str(report.get("type") or "unknown")
            timestamp = str(report.get("timestamp") or "")
            connection.execute(
                "INSERT OR IGNORE INTO reports(id, type, timestamp, data_json) VALUES (?, ?, ?, ?)",
                (report_id, report_type, timestamp, json.dumps(report["data"], ensure_ascii=False)),
            )
        except (OSError, json.JSONDecodeError, TypeError):
            continue


def save_report(report_type: str, report_data: dict[str, Any]) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    report_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    try:
        with _connect() as connection:
            _migrate_json_reports(connection)
            connection.execute(
                "INSERT INTO reports(id, type, timestamp, data_json) VALUES (?, ?, ?, ?)",
                (report_id, report_type, timestamp, json.dumps(report_data, ensure_ascii=False)),
            )
    except (sqlite3.Error, OSError, TypeError) as exc:
        raise RuntimeError(f"Failed to save report to SQLite: {exc}") from exc
    return {"id": report_id, "type": report_type, "timestamp": timestamp}


def list_reports(limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")
    with _connect() as connection:
        _migrate_json_reports(connection)
        rows = connection.execute(
            "SELECT id, type, timestamp, data_json FROM reports ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    reports = []
    for row in rows:
        try:
            data = json.loads(row["data_json"])
        except json.JSONDecodeError:
            data = {}
        reports.append({
            "id": row["id"],
            "type": row["type"],
            "timestamp": row["timestamp"],
            "summary": {
                "passed": data.get("passed", 0),
                "failed": data.get("failed", 0),
                "critical": data.get("severity_counts", {}).get("CRITICAL", 0),
                "high": data.get("severity_counts", {}).get("HIGH", 0),
            },
        })
    return reports


def get_report(report_id: str) -> dict[str, Any] | None:
    if (not report_id or len(report_id) > 64
            or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in report_id)):
        return None
    with _connect() as connection:
        _migrate_json_reports(connection)
        row = connection.execute(
            "SELECT id, type, timestamp, data_json FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()
    if row is None:
        return None
    try:
        data = json.loads(row["data_json"])
    except json.JSONDecodeError:
        return None
    return {"id": row["id"], "type": row["type"], "timestamp": row["timestamp"], "data": data}


def report_trends() -> dict[str, Any]:
    scans = [r for r in list_reports(200) if r["type"] == "checkov"]
    scans.reverse()
    trend = []
    previous: set[str] | None = None
    for scan in scans:
        detail = get_report(scan["id"]) or {}
        findings = (detail.get("data") or {}).get("results", [])
        current = {
            f"{item.get('check_id', 'unknown')}|{item.get('file_path', '')}|{item.get('resource', '')}"
            for item in findings if isinstance(item, dict)
        }
        trend.append({
            "id": scan["id"],
            "timestamp": scan["timestamp"],
            "type": scan["type"],
            "open_findings": len(current),
            "new_findings": len(current if previous is None else current - previous),
            "resolved_findings": 0 if previous is None else len(previous - current),
        })
        previous = current
    return {"scans": trend}
