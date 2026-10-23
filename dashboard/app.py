from html import escape
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
from dashboard.services.findings_service import normalize_findings, severity_counts
from dashboard.services.report_service import (
    save_report,
    list_reports,
    get_report,
    report_trends,
)

app = FastAPI(title="SecureCloudLab", version="2.0.0")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SecureCloudLab", "storage": "sqlite"}


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


def _run_and_save_scan(scan_type: str, runner) -> dict[str, Any]:
    report = runner()
    # Keep execution failures visible in history instead of silently losing evidence.
    if report.get("success"):
        findings = normalize_findings(report)
        report["results"] = findings
        report["severity_counts"] = severity_counts(findings)
    saved = save_report(scan_type, report)
    report["report_id"] = saved["id"]
    return report


@app.post("/api/checkov/scan")
def checkov_scan():
    return _run_and_save_scan("checkov", run_main_scan)


@app.post("/api/checkov/negative-test")
def checkov_negative_test():
    return _run_and_save_scan("negative-test", run_negative_test)


@app.get("/api/findings")
def findings(
    severity: list[str] | None = Query(default=None, description="Repeat parameter for multiple severities"),
    search: str | None = Query(default=None, max_length=200),
    report_id: str | None = Query(default=None, max_length=64),
):
    """Return normalized findings from the latest scan or a selected report."""
    if report_id:
        report = get_report(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        data = report.get("data", {})
    else:
        reports = [item for item in list_reports(200) if item["type"] == "checkov"]
        data = get_report(reports[0]["id"]).get("data", {}) if reports else {}
    items = normalize_findings(data)
    wanted = {value.upper() for value in (severity or [])}
    if wanted:
        items = [item for item in items if item["severity"] in wanted]
    if search:
        needle = search.casefold()
        items = [item for item in items if needle in " ".join(
            str(item.get(key, "")) for key in
            ("check_id", "check_name", "file_path", "resource", "remediation")
        ).casefold()]
    return {"count": len(items), "severity_counts": severity_counts(items), "findings": items}


@app.get("/api/reports")
def reports_history(limit: int = Query(default=50, ge=1, le=500)):
    return {"reports": list_reports(limit)}


@app.get("/api/reports/trends")
def reports_trends():
    return report_trends()


@app.get("/api/reports/{report_id}")
def report_details(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/reports/{report_id}/export.json")
def export_json(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return JSONResponse(
        content=report,
        headers={"Content-Disposition": f'attachment; filename="securecloudlab-{report_id}.json"'},
    )


@app.get("/api/reports/{report_id}/export.html", response_class=HTMLResponse)
def export_html(report_id: str):
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    data = report.get("data", {})
    items = normalize_findings(data)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value or ''))}</td>" for value in (
            item["severity"], item["check_id"], item["check_name"],
            item["file_path"], item["resource"], item["remediation"],
        )) + "</tr>"
        for item in items
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SecureCloudLab report {escape(report_id)}</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 20px;color:#172033}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd3df;padding:9px;text-align:left;vertical-align:top}}th{{background:#eef2f8}}.note{{padding:12px;background:#fff4d6}}</style>
</head><body><h1>SecureCloudLab security report</h1>
<p>Report: {escape(report_id)} · Type: {escape(str(report.get("type", "")))} · Timestamp: {escape(str(report.get("timestamp", "")))}</p>
<p class="note">These findings come from static Terraform analysis. They do not prove that a vulnerable resource is deployed in AWS.</p>
<p>Passed checks: {int(data.get("passed", 0) or 0)} · Failed checks: {int(data.get("failed", len(items)) or 0)} · Findings shown: {len(items)}</p>
<table><thead><tr><th>Severity</th><th>Check ID</th><th>Control</th><th>File</th><th>Resource</th><th>Remediation</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    return HTMLResponse(
        content=document,
        headers={"Content-Disposition": f'attachment; filename="securecloudlab-{report_id}.html"'},
    )
