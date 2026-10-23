from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

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
from dashboard.services.report_service import (
    save_report,
    list_reports,
    get_report,
)

app = FastAPI(title="SecureCloudLab")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


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


@app.post("/api/checkov/scan")
def checkov_scan():
    report = run_main_scan()
    save_report("checkov", report)
    return report


@app.post("/api/checkov/negative-test")
def checkov_negative_test():
    report = run_negative_test()
    save_report("negative-test", report)
    return report


@app.get("/api/reports")
def reports_history():
    return {"reports": list_reports()}


@app.get("/api/reports/{report_id}")
def report_details(report_id: str):
    report = get_report(report_id)

    if report is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")

    return report

import csv
import io

from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from dashboard.services.report_service import (
    compare_scans,
    get_scan,
    get_trends,
    init_db,
    list_scans,
)

# Initialize the local scan-history database.
init_db()


@app.get("/api/history")
def api_scan_history(limit: int = Query(default=20, ge=1, le=200)):
    """List recent scans."""
    return {"scans": list_scans(limit)}


@app.get("/api/trends")
def api_scan_trends(limit: int = Query(default=30, ge=1, le=200)):
    """Return scan summaries in chronological order."""
    return {"scans": get_trends(limit)}


@app.get("/api/findings")
def api_findings(
    scan_id: int | None = Query(default=None, ge=1),
    severity: str | None = Query(default=None),
):
    """Return findings from a scan, with an optional severity filter."""
    if scan_id is None:
        history = list_scans(limit=1)
        if not history:
            return {"scan_id": None, "findings": [], "total": 0}
        scan_id = history[0]["id"]

    scan = get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    findings = scan["findings"]

    if severity:
        severity_filter = severity.upper()
        allowed = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"}
        if severity_filter not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity. Expected one of: {sorted(allowed)}",
            )
        findings = [
            finding
            for finding in findings
            if finding.get("severity") == severity_filter
        ]

    return {
        "scan_id": scan_id,
        "total": len(findings),
        "findings": findings,
    }


@app.get("/api/scans/{scan_id}")
def api_scan_detail(scan_id: int):
    """Return one scan and its findings."""
    scan = get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
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


@app.get("/api/export/{scan_id}.json")
def api_export_json(scan_id: int):
    """Export a scan as JSON."""
    scan = get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    content = json.dumps(scan, indent=2, ensure_ascii=False)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="scan-{scan_id}.json"'
        },
    )


@app.get("/api/export/{scan_id}.csv")
def api_export_csv(scan_id: int):
    """Export scan findings as CSV."""
    scan = get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    output = io.StringIO()
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

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(scan["findings"])

    content = output.getvalue()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="scan-{scan_id}.csv"'
        },
    )
