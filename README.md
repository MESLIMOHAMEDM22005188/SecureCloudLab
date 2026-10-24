# SecureCloudLab

**SecureCloudLab** is a cloud-security learning and portfolio project combining an AWS infrastructure baseline built with Terraform and a local FastAPI dashboard for infrastructure validation, Infrastructure as Code (IaC) security scanning, and scan-report review.

> **Project status:** This is a learning project, not a production-ready AWS landing zone. Security checks help identify risks but cannot guarantee that an environment is secure.

## Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Run the dashboard](#run-the-dashboard)
- [Terraform verification](#terraform-verification)
- [Continuous integration](#continuous-integration)
- [Security design](#security-design)
- [Cost considerations](#cost-considerations)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)

## Overview

SecureCloudLab explores secure cloud infrastructure design, Terraform workflows, automated IaC scanning, and cloud monitoring. It has two main components:

1. **Terraform infrastructure** — declares AWS networking, identity, logging, and monitoring resources.
2. **Local security dashboard** — a FastAPI web application that runs supported Terraform and Checkov operations and presents results and saved reports.

## Features

### AWS infrastructure baseline

The Terraform configuration includes:

- A configurable IPv4 Virtual Private Cloud (VPC).
- Two public and two private subnets across two Availability Zones.
- An Internet Gateway and public route table.
- Private subnets without a default Internet route or NAT Gateway.
- Separate network ACLs for public and private subnets.
- A restrictive baseline security group with no ingress or egress rules; it is not attached to a workload by default.
- VPC Flow Logs delivered to CloudWatch Logs with 30-day retention.
- A dedicated EC2 workload IAM role with no permissions attached by default.
- A multi-region CloudTrail trail for management events.
- An S3 audit bucket with public access blocked, versioning, SSE-S3 encryption, and log-file validation.
- AWS Config recording and managed compliance rules.
- GuardDuty findings routed through EventBridge to an SNS topic.
- Common tags for project, environment, owner, and Terraform management.

Default VPC CIDR: `10.0.0.0/16`.

| Subnet | Default CIDR |
| --- | --- |
| Public subnet 1 | `10.0.1.0/24` |
| Public subnet 2 | `10.0.2.0/24` |
| Private subnet 1 | `10.0.11.0/24` |
| Private subnet 2 | `10.0.12.0/24` |

### Local web dashboard

The dashboard includes pages for:

- **Dashboard** — entry point for Terraform operations, scans, and recent reports.
- **Infrastructure** — infrastructure-related checks and operations.
- **Network Topology** — network topology view.
- **Security Analysis** — IaC scan results and security findings.
- **Scan History** — previously saved scan reports.
- **Settings** — dashboard settings.

The application also implements API endpoints for Terraform operations, Checkov scans, report history, findings, trends, scan details and comparisons, and report exports. Available operations depend on the current implementation and installed tools.

### Security automation

GitHub Actions workflows cover Terraform formatting, validation, Terraform tests, TFLint, Checkov, and Gitleaks secret scanning.

## Architecture

Terraform declares the infrastructure. The dashboard runs locally and invokes command-line tools to validate or scan configuration, then displays the results. Report history is stored locally by the dashboard's report service.

The Terraform CI workflow is intended for verification, not deployment. It does not run `terraform apply` or `terraform destroy`; Terraform tests use mocked AWS data sources and plan-only assertions.

## Repository structure

```text
SecureCloudLab/
├── .github/
│   └── workflows/
│       ├── terraform.yml
│       └── secrets.yml
├── dashboard/
│   ├── app.py
│   ├── services/
│   ├── templates/
│   ├── static/
│   └── reports/
├── data/
├── docs/
├── scripts/
├── terraform/
│   ├── versions.tf
│   ├── variables.tf
│   ├── main.tf
│   ├── network.tf
│   ├── routing.tf
│   ├── nacls.tf
│   ├── security.tf
│   ├── logging.tf
│   ├── iam.tf
│   ├── cloudtrail.tf
│   ├── config.tf
│   ├── guardduty.tf
│   └── tests/
├── tests/
├── .gitleaks.toml
├── .tflint.hcl
└── README.md
```

## Prerequisites

Install the tools required for the parts of the project you want to use.

| Tool | Purpose |
| --- | --- |
| Python 3.10+ | Run the FastAPI dashboard |
| pip | Install Python dependencies |
| Terraform | Format, initialize, validate, and test infrastructure code |
| TFLint | Lint Terraform configuration |
| Checkov | Scan Terraform for security issues |
| Gitleaks | Detect potential secrets in source code |
| Git | Clone and manage the repository |
| AWS account and credentials | Needed only for AWS operations that require authenticated access |

Use versions compatible with the constraints in `terraform/versions.tf`. Terraform, TFLint, Checkov, and Gitleaks are separate command-line tools.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/MESLIMOHAMEDM22005188/SecureCloudLab.git
cd SecureCloudLab
```

### 2. Create a Python virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dashboard dependencies

If the repository does not provide a dependency file for the dashboard, install the core runtime packages:

```bash
python -m pip install --upgrade pip
python -m pip install fastapi "uvicorn[standard]" jinja2
```

Install any additional dependencies imported by the dashboard services or needed by your chosen scanning tools.

### 4. Check your tools

```bash
python --version
terraform version
tflint --version
checkov --version
gitleaks version
```

Run the version commands for the tools you have installed.

## Run the dashboard

From the repository root, run:

```bash
python -m uvicorn dashboard.app:app --reload
```

Then open:

- Dashboard: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs
- Alternative API documentation: http://127.0.0.1:8000/redoc

Stop the server with `Ctrl+C`.

The dashboard invokes local command-line tools. Operations will fail if the required executable is not installed or cannot be found in the process `PATH`.

## Using the dashboard

1. Open the Dashboard page.
2. Run Terraform formatting and validation checks.
3. Run a Checkov scan to look for common infrastructure misconfigurations.
4. Review scan output and security findings.
5. Open Scan History to review saved reports, when available.
6. Explore the Infrastructure, Network Topology, Security Analysis, and Settings pages.

The negative security test is intended to verify that the scanner detects deliberately insecure test configuration. **Never deploy deliberately vulnerable test resources to AWS.**

A successful scan means that the configured checks completed; it does not prove that all risks have been eliminated.

## Terraform verification

Run these commands from the `terraform` directory:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
terraform test
tflint --recursive
checkov --directory . --framework terraform
```

These commands check formatting, initialize Terraform without configuring a backend, validate the configuration, run Terraform tests, lint the configuration, and scan it with Checkov.

Before applying infrastructure to an AWS account:

1. Review all Terraform changes and variable values.
2. Confirm the target AWS account, region, and credentials.
3. Review IAM permissions, network exposure, and logging configuration.
4. Run `terraform plan` and inspect the full plan.
5. Understand the potential service charges.
6. Ensure Terraform state is stored and protected appropriately.

Do not run `terraform apply` or `terraform destroy` unless you explicitly intend to create or remove resources and understand the consequences.

## Continuous integration

The GitHub Actions workflows are intended to run checks on repository changes.

The Terraform workflow includes formatting, initialization and validation, Terraform tests, TFLint, and Checkov. The secret-scanning workflow uses Gitleaks.

CI is designed not to provision infrastructure: it does not run `terraform apply` or `terraform destroy`. The configured Checkov threshold fails CI on findings of medium severity or higher; inspect the workflow files for the exact current behavior.

## Security design

### Network isolation

- Public and private subnets are separated.
- Private subnets have no default Internet route.
- No NAT Gateway is provisioned by default.
- Public and private subnet network ACLs have separate rules.
- The baseline security group denies ingress and egress and is not attached to a workload by default.

### Identity and access

- A dedicated workload IAM role is defined.
- The role has no permissions attached by default.
- Add only narrowly scoped permissions required by a specific workload.
- Avoid static access keys wherever possible.

### Logging and monitoring

- VPC Flow Logs send network-flow records to CloudWatch Logs.
- CloudTrail records management events and delivers logs to a protected S3 bucket.
- AWS Config evaluates selected managed compliance rules.
- GuardDuty findings are routed through EventBridge to an SNS topic.

To receive notifications, configure an approved SNS subscription after deployment and confirm the subscription.

### Secrets and Terraform state

- Never commit access keys, passwords, tokens, private keys, secret variable files, Terraform state, or saved plan files.
- Review `.gitignore` and the Gitleaks configuration before sharing changes.
- If a secret is exposed, revoke or rotate it immediately and follow [the secret incident response guide](docs/secret-incident-response.md).
- `terraform/backend.tf.example` documents a possible remote S3 backend. It is not a pre-provisioned backend; prepare the bucket, access controls, and state-locking configuration before migrating state.

Additional documentation:

- [IAM audit and Terraform state](docs/iam-audit-and-state.md)
- [Secret incident response](docs/secret-incident-response.md)
- [Security monitoring](docs/security-monitoring.md)

## Cost considerations

Services in this configuration may incur charges after deployment, including AWS Config, GuardDuty, CloudTrail delivery, S3 storage and requests, and CloudWatch Logs ingestion and retention. Costs depend on region, usage, configuration, and current AWS pricing.

Review current AWS pricing and your account's service settings before deployment. The absence of a NAT Gateway does not make the overall infrastructure cost-free.

## Troubleshooting

### Uvicorn cannot import the application

Run the command from the repository root:

```bash
python -m uvicorn dashboard.app:app --reload
```

Verify that `dashboard/app.py` exists, the virtual environment is active, and required packages are installed.

### A page or stylesheet returns 404

Confirm that templates are in `dashboard/templates/`, static files are in `dashboard/static/`, and the application mounts the static directory. Restart Uvicorn after changing Python route configuration.

### Terraform, Checkov, or TFLint is not recognized

Install the relevant executable, add it to your system `PATH`, open a new terminal, and retry the version command. Restart the dashboard after updating environment variables.

### Terraform validation fails

Run commands from the `terraform` directory. Review the full error output, Terraform and provider constraints, required variables, and initialization status.

### Scan history is empty or unavailable

History may be empty before the first scan. Check the dashboard logs and the report service's local database or report-storage path if previously saved reports cannot be loaded.

## Limitations

- This is a learning and portfolio project, not a certified security product or production-ready landing zone.
- Automated scans cannot guarantee that infrastructure is free of vulnerabilities.
- Actual AWS resources and costs depend on what is deployed in the target account.
- The dashboard depends on locally installed tools and the endpoints implemented in the current version.
- A local dashboard is not a secure multi-user service. Do not expose it publicly without authentication, authorization, network restrictions, and deployment hardening.
- Review and test infrastructure changes before using them in a real environment.

## Contributing

1. Create a feature branch.
2. Keep changes focused and describe their security impact.
3. Run the relevant Terraform, linting, and security checks.
4. Do not include credentials, state files, or sensitive scan artifacts.
5. Open a pull request describing the changes and checks performed.

## License

No license terms are stated in this README. Unless a license is added to the repository, reuse and redistribution are not automatically granted. Add an appropriate license file if you intend to publish the project for reuse.
