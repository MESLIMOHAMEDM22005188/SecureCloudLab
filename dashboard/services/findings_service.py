from typing import Any

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN")

_REMEDIATION_RULES = (
    (("CKV_AWS_20", "CKV_AWS_21", "CKV_AWS_53", "CKV_AWS_54", "S3"), "Review S3 bucket public-access settings, block public access, and use least-privilege bucket policies."),
    (("CKV_AWS_24", "CKV_AWS_25", "SSH", "PORT 22"), "Restrict SSH to an approved administrator CIDR, prefer a managed access path such as AWS Systems Manager, and remove public ingress."),
    (("CKV_AWS_8", "ENCRYPT", "KMS"), "Enable encryption at rest and use an appropriately managed KMS key where required."),
    (("CKV_AWS_18", "CKV_AWS_ CloudTrail", "CLOUDTRAIL"), "Enable auditable CloudTrail logging, protect log storage, and validate log-file integrity."),
    (("IAM", "POLICY", "WILDCARD"), "Replace wildcard permissions with actions and resources required by the workload; review trust relationships."),
)


def classify_severity(check_id: str, check_name: str) -> tuple[str, str]:
    """Use Checkov-provided severity when present; otherwise label a transparent heuristic."""
    text = f"{check_id} {check_name}".upper()
    if any(token in text for token in ("0.0.0.0/0", "PUBLIC SSH", "PORT 22", "CKV_AWS_24", "PUBLICLY ACCESSIBLE")):
        return "HIGH", "heuristic"
    if any(token in text for token in ("ENCRYPT", "MFA", "LOGGING", "CLOUDTRAIL", "AUDIT")):
        return "MEDIUM", "heuristic"
    return "MEDIUM", "heuristic"


def recommendation_for(check_id: str, check_name: str) -> str:
    text = f"{check_id} {check_name}".upper()
    for tokens, recommendation in _REMEDIATION_RULES:
        if any(token in text for token in tokens):
            return recommendation
    return "Review the Checkov guideline and affected Terraform resource; apply the smallest least-privilege change, then rerun the scan."


def normalize_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Checkov findings while tolerating old and partial report shapes."""
    raw = report.get("results", [])
    if isinstance(raw, dict):
        raw = raw.get("failed_checks", [])
    if not isinstance(raw, list):
        return []
    findings = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("check_id") or "UNKNOWN")
        check_name = str(item.get("check_name") or item.get("name") or "Unnamed security check")
        severity = str(item.get("severity") or "UNKNOWN").upper()
        if severity not in SEVERITIES:
            severity = "UNKNOWN"
        findings.append({
            "check_id": check_id,
            "check_name": check_name,
            "severity": severity,\n            "severity_source": severity_source,
            "file_path": str(item.get("file_path") or item.get("file") or "Unknown"),
            "resource": str(item.get("resource") or "Unknown"),
            "guideline": item.get("guideline"),
            "remediation": recommendation_for(check_id, check_name),
            "source": "Terraform static analysis (Checkov)",
            "deployment_confirmed": False,
        })
    return findings


def severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    return {severity: sum(1 for finding in findings if finding.get("severity") == severity)
            for severity in SEVERITIES}
