# SecureCloudLab

SecureCloudLab is a local Cloud Security and DevSecOps portfolio laboratory. It
uses Terraform to model a deliberately small, inspectable artifact and Checkov
to demonstrate infrastructure-as-code security scanning without provisioning
cloud infrastructure or incurring cloud costs.

## Current architecture

The Terraform configuration uses the `hashicorp/local` provider only. The
`local_file.security_report` resource writes a report for the selected
`environment` (default: `dev`) to `terraform/security-report.txt`. Terraform
configures the report with `0600` permissions and its parent directory with
`0700` permissions.

No cloud provider, remote state backend, secret, credential, or paid resource
is defined. The report is generated only by `terraform apply`, which is not a
required verification step and must not be run for routine checks.

## Prerequisites

- Terraform 1.5 or later.
- Python with Checkov installed. This workspace uses
  `C:\Users\mesli\SecureCloudLab-tools\Scripts\python.exe` and
  `C:\Users\mesli\SecureCloudLab-tools\Scripts\checkov`.

## Verification

Run the following from the repository root:

```powershell
Set-Location terraform
terraform fmt -check
terraform validate
terraform plan -input=false -lock=false
Set-Location ..
& "C:\Users\mesli\SecureCloudLab-tools\Scripts\python.exe" `
  "C:\Users\mesli\SecureCloudLab-tools\Scripts\checkov" `
  -d terraform --framework terraform --output cli --compact
```

`terraform plan` is read-only with respect to managed resources: it previews
the local report but does not create it. Do not run `terraform apply` or
`terraform destroy` as part of this portfolio validation.

## Security limitations

- Windows ACLs are not equivalent to POSIX mode bits; `0600` and `0700` are
  enforced by the local provider where supported and must be verified on the
  target platform after an apply.
- Checkov may produce zero checks for this configuration because it has no
  built-in policies for the `local_file` resource. A zero-check scan is not a
  security attestation.
- This lab has no cloud resources yet, so it does not demonstrate IAM, network,
  encryption, logging, state-backend, or secret-management controls.

See `terraform/README.md` for implementation details and `docs/README.md` for
the security scope.
