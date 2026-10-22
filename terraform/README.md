# Terraform infrastructure

This directory defines the SecureCloudLab AWS network foundation and baseline security controls.

## Files

| File | Responsibility |
|---|---|
| `versions.tf` | Terraform/provider versions and AWS region configuration |
| `variables.tf` | Input variables and IPv4 CIDR validation |
| `main.tf` | VPC, common tags and naming prefix |
| `network.tf` | Two public and two private subnets across two available Availability Zones |
| `routing.tf` | Internet Gateway, route tables and subnet associations |
| `security.tf` | Baseline security group with no ingress or egress |
| `logging.tf` | VPC Flow Logs, CloudWatch log group and delivery IAM role |
| `outputs.tf` | VPC and subnet outputs |
| `terraform.tfvars.example` | Example values without secrets |

## Validate locally

Run these commands from this directory:

```powershell
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

`terraform plan` queries AWS for available Availability Zones and therefore requires working AWS credentials and network access. The CI workflow intentionally avoids `plan`, `apply` and `destroy`.

## Security and cost

The baseline security group denies all inbound and outbound traffic and is not attached to a workload. Add narrowly scoped rules only after defining a workload requirement.

VPC Flow Logs are configured to send all VPC traffic to CloudWatch Logs with 30-day retention. CloudWatch ingestion and storage may incur charges after deployment. Review AWS pricing and permissions before any apply.

The private route table has no default Internet route and there is no NAT Gateway. No remote backend is configured. This is a learning environment, not a production-ready landing zone.
