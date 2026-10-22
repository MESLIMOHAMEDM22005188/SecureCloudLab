# Terraform infrastructure

This directory defines the current SecureCloudLab AWS network foundation.

## Files

| File | Responsibility |
|---|---|
| `versions.tf` | Terraform/provider versions and AWS region configuration |
| `variables.tf` | Input variables and basic input validation |
| `main.tf` | VPC, common tags and naming prefix |
| `network.tf` | Public and private subnets |
| `routing.tf` | Internet Gateway and route tables |
| `security.tf` | Reserved for future security controls |
| `logging.tf` | Reserved for future logging controls |
| `outputs.tf` | VPC and subnet outputs |
| `terraform.tfvars.example` | Example values without secrets |

## Validate locally

```powershell
terraform fmt -recursive
terraform init -backend=false
terraform validate
terraform plan
```

Do not run `terraform apply` unless deployment has been explicitly approved and its costs and permissions have been reviewed.
