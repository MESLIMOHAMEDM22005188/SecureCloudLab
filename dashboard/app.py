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
