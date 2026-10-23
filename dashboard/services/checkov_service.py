import json
import shutil
import subprocess
import sysconfig
from pathlib import Path
from typing import Any


# SecureCloudLab project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TERRAFORM_DIR = PROJECT_ROOT / "terraform"
NEGATIVE_TEST_FILE = (
    PROJECT_ROOT / "tests" / "negative" / "security-group-open.tf"
)


def _find_checkov() -> str:
    """Locate the Checkov executable."""
    executable = shutil.which("checkov")

    if executable:
        return executable

    # Support Windows installations using pip --user
    scripts_dir = Path(sysconfig.get_path("scripts", "nt_user"))
    windows_executable = scripts_dir / "checkov.cmd"

    if windows_executable.exists():
        return str(windows_executable)

    raise FileNotFoundError(
        "Checkov was not found. Install it with: "
        "python -m pip install checkov"
    )


def run_checkov(
    target: str = "main",
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Run Checkov against the main Terraform configuration
    or the intentionally vulnerable negative test.

    Targets:
        - 'main': scan the main Terraform directory.
        - 'negative': verify that Checkov detects insecure configuration.
    """
    if target == "main":
        if not TERRAFORM_DIR.is_dir():
            return {
                "success": False,
                "error": f"Terraform directory not found: {TERRAFORM_DIR}",
            }

        command = [
            _find_checkov(),
            "--directory",
            str(TERRAFORM_DIR),
            "--framework",
            "terraform",
            "--output",
            "json",
        ]

    elif target == "negative":
        if not NEGATIVE_TEST_FILE.is_file():
            return {
                "success": False,
                "error": (
                    "Negative test file not found: "
                    f"{NEGATIVE_TEST_FILE}"
                ),
            }

        command = [
            _find_checkov(),
            "--file",
            str(NEGATIVE_TEST_FILE),
            "--framework",
            "terraform",
            "--output",
            "json",
        ]

    else:
        return {
            "success": False,
            "error": "Invalid target. Use 'main' or 'negative'.",
        }

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )

        output = result.stdout.strip()

        try:
            report = json.loads(output)
        except json.JSONDecodeError:
            return {
                "success": False,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": "Could not parse Checkov JSON report.",
            }

        summary = report.get("summary", {})
        results = report.get("results", {})

        failed_checks = results.get("failed_checks", [])
        passed_checks = results.get("passed_checks", [])

        failures = [
            {
                "check_id": check.get("check_id"),
                "check_name": check.get("check_name"),
                "file_path": check.get("file_path"),
                "resource": check.get("resource"),
                "guideline": check.get("guideline"),
            }
            for check in failed_checks
        ]

        return {
            "success": True,
            "target": target,
            "return_code": result.returncode,
            "passed": summary.get("passed", len(passed_checks)),
            "failed": summary.get("failed", len(failed_checks)),
            "skipped": summary.get("skipped", 0),
            "results": failures,
            "stderr": result.stderr,
        }

    except FileNotFoundError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Checkov timed out after {timeout} seconds.",
        }


def run_main_scan() -> dict[str, Any]:
    """Scan the main Terraform configuration."""
    return run_checkov(target="main")


def run_negative_test() -> dict[str, Any]:
    """Verify that Checkov detects vulnerabilities in the negative test."""
    return run_checkov(target="negative")