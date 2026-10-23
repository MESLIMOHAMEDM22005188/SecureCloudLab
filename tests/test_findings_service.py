from dashboard.services.findings_service import build_findings_summary


def test_build_findings_summary_normalizes_severity_and_remediation():
    report = build_findings_summary({"success": True, "target": "main", "passed": 8, "failed": 1, "results": [{"check_id": "CKV_AWS_24", "check_name": "Ensure SSH access is restricted", "severity": {"severity": "HIGH"}, "resource": "aws_security_group.example", "file_path": "/terraform/security.tf", "guideline": "Restrict SSH to trusted CIDRs."}]})
    assert report["summary"]["total"] == 1
    assert report["summary"]["by_severity"]["HIGH"] == 1
    assert report["findings"][0]["id"] == "CKV_AWS_24"
    assert report["findings"][0]["remediation"] == "Restrict SSH to trusted CIDRs."


def test_build_findings_summary_handles_scan_failure():
    report = build_findings_summary({"success": False, "error": "Checkov unavailable"})
    assert report["success"] is False
    assert report["error"] == "Checkov unavailable"
    assert report["findings"] == []


def test_unknown_severity_is_not_misclassified():
    report = build_findings_summary({"success": True, "results": [{"check_id": "X", "severity": "urgent"}]})
    assert report["summary"]["by_severity"]["UNKNOWN"] == 1
