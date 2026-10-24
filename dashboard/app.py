import csv
import io
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dashboard.services.terraform_service import (
    check_format,
    initialize,
    validate,
    plan,
)
from dashboard.services.checkov_service import (
    run_main_scan,
    run_negative_test,
)
from dashboard.services.findings_service import (
    normalize_findings,
    severity_counts,
)
from dashboard.services.report_service import (
    save_scan,
    list_scans,
    get_scan,
    get_trends,
    compare_scans,
    init_db,
)


# ==================================================
# Application configuration
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="SecureCloudLab",
    description="Infrastructure security scanning and reporting API.",
    version="1.0.0",
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Make CSS, JavaScript and other static assets accessible.
if STATIC_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

# Initialize the scan-history database.
init_db()


# ==================================================
# HTML pages
# ==================================================

def render_page(request: Request, template_name: str) -> HTMLResponse:
    """Render an HTML template with the current request."""
    template_path = TEMPLATES_DIR / template_name

    if not template_path.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"HTML template not found: {template_name}",
        )

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={},
    )


@app.get("/", response_class=HTMLResponse, name="dashboard_home")
def dashboard_home(request: Request):
    return render_page(request, "index.html")


@app.get("/infrastructure", response_class=HTMLResponse)
def infrastructure_page(request: Request):
    return render_page(request, "infrastructure.html")


@app.get("/topology", response_class=HTMLResponse)
def topology_page(request: Request):
    return render_page(request, "topology.html")


@app.get("/security", response_class=HTMLResponse)
def security_page(request: Request):
    return render_page(request, "security.html")


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return render_page(request, "history.html")


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return render_page(request, "settings.html")


# ==================================================
# Terraform API
# ==================================================

@app.get("/api/terraform/fmt")
def terraform_format_check():
    return check_format()


@app.post("/api/terraform/init")
def terraform_init():
    return initialize()


@app.post("/api/terraform/validate")
def terraform_validate():
    return validate()


@app.post("/api/terraform/plan")
def terraform_plan():
    return plan()


# ==================================================
# Checkov scans and report persistence
# ==================================================

def persist_checkov_report(report: dict[str, Any], target: str) -> int:
    """Normalize and save a Checkov result in the scan database."""
    findings = normalize_findings(report)

    scan_id = save_scan(
        findings=findings,
        target=target,
        status="completed" if report.get("success", False) else "failed",
        severity_counts=severity_counts(findings),
    )

    return scan_id


@app.post("/api/checkov/scan")
def checkov_scan():
    report = run_main_scan()
    scan_id = persist_checkov_report(report, "checkov")

    return {
        **report,
        "scan_id": scan_id,
    }


@app.post("/api/checkov/negative-test")
def checkov_negative_test():
    report = run_negative_test()
    scan_id = persist_checkov_report(report, "negative-test")

    return {
        **report,
        "scan_id": scan_id,
    }


# ==================================================
# Report history compatibility endpoints
# ==================================================

@app.get("/api/reports")
def reports_history(
        limit: int = Query(default=20, ge=1, le=200),
):
    return {
        "reports": list_scans(limit=limit),
    }


@app.get("/api/reports/{report_id}")
def report_details(report_id: int):
    report = get_scan(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report


# ==================================================
# Scan history and trends
# ==================================================

@app.get("/api/history")
def api_scan_history(
        limit: int = Query(default=20, ge=1, le=200),
):
    """List recent scans."""
    return {
        "scans": list_scans(limit=limit),
    }


@app.get("/api/trends")
def api_scan_trends(
        limit: int = Query(default=30, ge=1, le=200),
):
    """Return scan summaries."""
    return {
        "scans": get_trends(limit=limit),
    }


# ==================================================
# Security findings
# ==================================================

@app.get("/api/findings")
def api_findings(
        scan_id: int | None = Query(default=None, ge=1),
        severity: str | None = Query(default=None),
):
    """Return findings, optionally filtered by severity."""

    if scan_id is None:
        history = list_scans(limit=1)

        if not history:
            return {
                "scan_id": None,
                "findings": [],
                "total": 0,
            }

        scan_id = history[0]["id"]

    scan = get_scan(scan_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    findings = scan.get("findings", [])

    if severity is not None:
        severity_filter = severity.strip().upper()

        allowed_severities = {
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
            "INFO",
            "UNKNOWN",
        }

        if severity_filter not in allowed_severities:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid severity. Expected one of: "
                    f"{', '.join(sorted(allowed_severities))}"
                ),
            )

        findings = [
            finding
            for finding in findings
            if str(finding.get("severity", "UNKNOWN")).upper()
               == severity_filter
        ]

    return {
        "scan_id": scan_id,
        "total": len(findings),
        "findings": findings,
    }


# ==================================================
# Scan details and comparison
# ==================================================

@app.get("/api/scans/{scan_id}")
def api_scan_detail(scan_id: int):
    """Return one scan and its findings."""
    scan = get_scan(scan_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    return scan


@app.get("/api/scans/{old_scan_id}/compare/{new_scan_id}")
def api_compare_scans(old_scan_id: int, new_scan_id: int):
    """Compare two scans."""
    comparison = compare_scans(old_scan_id, new_scan_id)

    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail="One or both scans were not found",
        )

    return comparison


# ==================================================
# Scan exports
# ==================================================

@app.get("/api/export/{scan_id}.json")
def api_export_json(scan_id: int):
    """Export a scan as a JSON file."""
    scan = get_scan(scan_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    content = json.dumps(
        scan,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="scan-{scan_id}.json"'
            ),
        },
    )


@app.get("/api/export/{scan_id}.csv")
def api_export_csv(scan_id: int):
    """Export scan findings as a CSV file."""
    scan = get_scan(scan_id)

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    output = io.StringIO(newline="")

    fieldnames = [
        "check_id",
        "check_name",
        "severity",
        "severity_source",
        "file_path",
        "resource",
        "guideline",
        "remediation",
        "source",
        "deployment_confirmed",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )

    writer.writeheader()

    findings = scan.get("findings", [])
    writer.writerows(
        finding
        for finding in findings
        if isinstance(finding, dict)
    )

    # UTF-8 BOM helps spreadsheet software display accented characters.
    csv_content = "\ufeff" + output.getvalue()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="scan-{scan_id}.csv"'
            ),
        },
    )
