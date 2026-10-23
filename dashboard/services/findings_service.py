from __future__ import annotations

from collections import Counter
from typing import Any

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN")


def _severity(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("severity") or value.get("value")
    normalized = str(value or "UNKNOWN").strip().upper()
    return normalized if normalized in SEVERITIES else "UNKNOWN"


def build_findings_summary(scan: dict[str, Any]) -> dict[str, Any]:
    """Return normalized Checkov findings and counts without guessing missing severity."""
    if not scan.get("success"):
        return {"success": False, "error": scan.get("error", "Security scan failed"), "findings": [], "summary": {"total": 0, "by_severity": {s: 0 for s in SEVERITIES}}}
    findings = []
    for item in scan.get("results", []):
        if not isinstance(item, dict):
            continue
        findings.append({
            "id": str(item.get("check_id") or "UNKNOWN-CHECK"),
            "title": str(item.get("check_name") or "Unnamed security check"),
            "severity": _severity(item.get("severity")),
            "resource": str(item.get("resource") or "Unknown resource"),
            "file": str(item.get("file_path") or ""),
            "remediation": str(item.get("guideline") or "Review the Checkov guideline for this check."),
        })
    counts = Counter(item["severity"] for item in findings)
    return {"success": True, "target": scan.get("target", "main"), "summary": {"total": len(findings), "passed": int(scan.get("passed", 0) or 0), "failed": int(scan.get("failed", len(findings)) or 0), "by_severity": {s: counts.get(s, 0) for s in SEVERITIES}}, "findings": findings}
