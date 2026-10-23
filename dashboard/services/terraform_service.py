import shutil
import subprocess
from pathlib import Path
from typing import Any


# SecureCloudLab project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TERRAFORM_DIR = PROJECT_ROOT / "terraform"


def _find_terraform() -> str:
    """Locate the Terraform executable."""
    executable = shutil.which("terraform")

    if executable:
        return executable

    raise FileNotFoundError(
        "Terraform was not found. Install Terraform and add it to PATH."
    )


def _run_command(
    args: list[str],
    timeout: int = 120,
) -> dict[str, Any]:
    """Run an approved Terraform command and capture its output."""
    try:
        terraform = _find_terraform()

        result = subprocess.run(
            [terraform, *args],
            cwd=str(TERRAFORM_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )

        return {
            "success": result.returncode == 0,
            "command": ["terraform", *args],
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except FileNotFoundError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Terraform command timed out after {timeout} seconds.",
        }


def _check_terraform_directory() -> dict[str, Any] | None:
    """Ensure the Terraform directory exists."""
    if not TERRAFORM_DIR.is_dir():
        return {
            "success": False,
            "error": f"Terraform directory not found: {TERRAFORM_DIR}",
        }

    if not any(TERRAFORM_DIR.glob("*.tf")):
        return {
            "success": False,
            "error": f"No Terraform configuration files found in {TERRAFORM_DIR}",
        }

    return None


def check_format() -> dict[str, Any]:
    """Check Terraform formatting without modifying files."""
    error = _check_terraform_directory()
    if error:
        return error

    return _run_command(["fmt", "-check", "-recursive", str(TERRAFORM_DIR)])


def format_code() -> dict[str, Any]:
    """Format Terraform files in place."""
    error = _check_terraform_directory()
    if error:
        return error

    return _run_command(["fmt", "-recursive", str(TERRAFORM_DIR)])


def initialize() -> dict[str, Any]:
    """Initialize Terraform without configuring a backend."""
    error = _check_terraform_directory()
    if error:
        return error

    return _run_command(
        ["-chdir=" + str(TERRAFORM_DIR), "init", "-backend=false", "-input=false"],
        timeout=180,
    )


def validate() -> dict[str, Any]:
    """Validate Terraform configuration syntax and internal consistency."""
    error = _check_terraform_directory()
    if error:
        return error

    init_result = initialize()

    if not init_result.get("success"):
        return {
            "success": False,
            "step": "init",
            "details": init_result,
        }

    return _run_command(
        ["-chdir=" + str(TERRAFORM_DIR), "validate", "-no-color"],
        timeout=120,
    )


def plan() -> dict[str, Any]:
    """
    Generate a Terraform execution plan without applying changes.

    Uses a local, non-configured backend and disables interactive input.
    """
    error = _check_terraform_directory()
    if error:
        return error

    init_result = initialize()

    if not init_result.get("success"):
        return {
            "success": False,
            "step": "init",
            "details": init_result,
        }

    return _run_command(
        [
            "-chdir=" + str(TERRAFORM_DIR),
            "plan",
            "-input=false",
            "-no-color",
            "-lock=false",
            "-refresh=false",
        ],
        timeout=180,
    )