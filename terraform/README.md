# Terraform configuration

This directory contains the SecureCloudLab infrastructure-as-code example.

## Resources

- Provider: `hashicorp/local` pinned through `.terraform.lock.hcl`.
- Input: `environment`, a string that defaults to `dev`.
- Resource: `local_file.security_report`, which renders the environment name to
  `security-report.txt` when explicitly applied.

The resource keeps `file_permission = "0600"` and
`directory_permission = "0700"`. These values are intentional and must not be
weakened to satisfy a scanner or local development constraint.

## Checks

```powershell
terraform fmt -check
terraform validate
terraform plan -input=false -lock=false
```

The expected plan contains one local create action and no cloud changes. Do not
run `terraform apply` or `terraform destroy` for the verification workflow.

Generated provider files (`.terraform/`), state files, crash logs, and the
generated report are excluded from Git. Keep `.terraform.lock.hcl` under
version control to ensure deterministic provider selection.
