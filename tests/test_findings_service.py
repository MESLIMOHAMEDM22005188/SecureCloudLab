from dashboard.services.findings_service import normalize_findings, severity_counts


def test_normalize_checkov_findings_includes_remediation_and_context():
    report = {
        "results": [{
            "check_id": "CKV_AWS_24",
            "check_name": "Ensure no security groups allow ingress from 0.0.0.0/0 to port 22",
            "severity": "HIGH",
            "file_path": "/terraform/security.tf",
            "resource": "aws_security_group.example",
            "guideline": "https://example.test/check",
        }]
    }

    findings = normalize_findings(report)

    assert len(findings) == 1
    assert findings[0]["check_id"] == "CKV_AWS_24"
    assert findings[0]["severity"] == "HIGH"
    assert "Restrict SSH" in findings[0]["remediation"]
    assert findings[0]["deployment_confirmed"] is False


def test_normalize_handles_legacy_checkov_shape_and_missing_fields():
    findings = normalize_findings({
        "results": {"failed_checks": [{"check_id": "CKV_TEST_1"}]}
    })

    assert findings[0]["check_id"] == "CKV_TEST_1"
    assert findings[0]["severity"] == "UNKNOWN"
    assert findings[0]["file_path"] == "Unknown"


def test_severity_counts_includes_zeroes():
    counts = severity_counts([
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "LOW"},
    ])

    assert counts["HIGH"] == 2
    assert counts["LOW"] == 1
    assert counts["CRITICAL"] == 0
