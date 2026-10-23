
import pytest

from dashboard.services.findings_service import (
    SEVERITIES,
    classify_severity,
    normalize_findings,
    recommendation_for,
    severity_counts,
)


def test_normalize_checkov_finding():
    report = {
        "results": [
            {
                "check_id": "CKV_AWS_24",
                "check_name": (
                    "Ensure no security groups allow ingress "
                    "from 0.0.0.0/0 to port 22"
                ),
                "severity": "HIGH",
                "file_path": "terraform/security.tf",
                "resource": "aws_security_group.example",
                "guideline": "https://example.test/check",
            }
        ]
    }

    findings = normalize_findings(report)

    assert len(findings) == 1

    finding = findings[0]
    assert finding["check_id"] == "CKV_AWS_24"
    assert finding["severity"] == "HIGH"
    assert finding["severity_source"] == "checkov"
    assert finding["file_path"] == "terraform/security.tf"
    assert finding["resource"] == "aws_security_group.example"
    assert finding["guideline"] == "https://example.test/check"
    assert "Restrict SSH" in finding["remediation"]
    assert finding["deployment_confirmed"] is False


def test_normalize_legacy_checkov_report():
    report = {
        "results": {
            "failed_checks": [
                {"check_id": "CKV_TEST_1"}
            ]
        }
    }

    findings = normalize_findings(report)

    assert len(findings) == 1
    assert findings[0]["check_id"] == "CKV_TEST_1"
    assert findings[0]["check_name"] == "Unnamed security check"
    assert findings[0]["severity"] == "MEDIUM"
    assert findings[0]["severity_source"] == "heuristic"
    assert findings[0]["file_path"] == "Unknown"
    assert findings[0]["resource"] == "Unknown"


def test_checkov_severity_takes_precedence():
    report = {
        "results": [
            {
                "check_id": "CKV_AWS_24",
                "check_name": "Public SSH access",
                "severity": "LOW",
            }
        ]
    }

    findings = normalize_findings(report)

    assert findings[0]["severity"] == "LOW"
    assert findings[0]["severity_source"] == "checkov"


def test_invalid_checkov_severity_becomes_unknown():
    report = {
        "results": [
            {
                "check_id": "CKV_TEST_1",
                "severity": "EXTREME",
            }
        ]
    }

    findings = normalize_findings(report)

    assert findings[0]["severity"] == "UNKNOWN"
    assert findings[0]["severity_source"] == "checkov"


@pytest.mark.parametrize(
    ("check_id", "check_name", "expected"),
    [
        ("CKV_AWS_24", "Security group SSH", "HIGH"),
        ("CKV_TEST_1", "Encryption at rest", "MEDIUM"),
        ("CKV_TEST_2", "Generic configuration check", "MEDIUM"),
    ],
)
def test_classify_severity(check_id, check_name, expected):
    severity, source = classify_severity(check_id, check_name)

    assert severity == expected
    assert source == "heuristic"


def test_s3_finding_has_specific_remediation():
    recommendation = recommendation_for(
        "CKV_AWS_20",
        "S3 bucket public access",
    )

    assert "S3" in recommendation
    assert "Block Public Access" in recommendation


def test_unknown_finding_has_fallback_remediation():
    recommendation = recommendation_for(
        "CKV_CUSTOM_999",
        "Custom security check",
    )

    assert "Checkov guideline" in recommendation
    assert "Terraform resource" in recommendation


def test_severity_counts_includes_zeroes():
    findings = [
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "LOW"},
    ]

    counts = severity_counts(findings)

    assert counts["HIGH"] == 2
    assert counts["LOW"] == 1
    assert counts["CRITICAL"] == 0
    assert counts["MEDIUM"] == 0
    assert counts["INFO"] == 0
    assert counts["UNKNOWN"] == 0
    assert set(counts.keys()) == set(SEVERITIES)


@pytest.mark.parametrize(
    "report",
    [
        {},
        {"results": None},
        {"results": "invalid"},
        {"results": {"failed_checks": "invalid"}},
    ],
)
def test_normalize_handles_invalid_report_shapes(report):
    assert normalize_findings(report) == []


def test_normalize_skips_non_dictionary_entries():
    report = {
        "results": [
            None,
            "invalid",
            123,
            {"check_id": "CKV_TEST_1"},
        ]
    }

    findings = normalize_findings(report)

    assert len(findings) == 1
    assert findings[0]["check_id"] == "CKV_TEST_1"


def test_severity_counts_handles_empty_findings():
    counts = severity_counts([])

    assert all(count == 0 for count in counts.values())
