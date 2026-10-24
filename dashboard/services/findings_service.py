"""Utilities for normalizing and counting security findings."""

from typing import Any


SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")


def normalize_findings(data: Any) -> list[dict[str, Any]]:
    """Normalize Checkov reports or existing finding lists."""

    if isinstance(data, list):
        raw_findings = data

    elif isinstance(data, dict):
        results = data.get("results", {})

        if isinstance(results, dict):
            raw_findings = results.get("failed_checks", [])
        elif isinstance(results, list):
            raw_findings = results
        else:
            raw_findings = []

        if not raw_findings:
            for key in ("findings", "issues", "checks"):
                candidate = data.get(key)
                if isinstance(candidate, list):
                    raw_findings = candidate
                    break

    else:
        return []

    normalized = []

    for item in raw_findings:
        if not isinstance(item, dict):
            continue

        finding = dict(item)

        severity = str(
            finding.get("severity")
            or finding.get("risk_level")
            or "INFO"
        ).upper()

        if severity not in SEVERITIES:
            severity = "INFO"

        finding["severity"] = severity
        finding["title"] = (
                finding.get("title")
                or finding.get("check_name")
                or finding.get("check_id")
                or "Security finding"
        )
        finding["resource"] = (
                finding.get("resource")
                or finding.get("resource_name")
                or finding.get("file_path")
                or "Unknown resource"
        )
        finding["description"] = (
                finding.get("description")
                or finding.get("message")
                or finding.get("guideline")
                or ""
        )

        normalized.append(finding)

    return normalized


def severity_counts(findings: Any) -> dict[str, int]:
    """Count findings by severity."""

    normalized = normalize_findings(findings)

    counts = {severity: 0 for severity in SEVERITIES}

    for finding in normalized:
        severity = finding.get("severity", "INFO")
        counts[severity] += 1

    counts["TOTAL"] = len(normalized)

    return counts