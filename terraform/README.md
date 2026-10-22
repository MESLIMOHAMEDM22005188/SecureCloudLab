# Terraform infrastructure

This directory defines the SecureCloudLab AWS network foundation, IAM baseline, and audit controls.

## Files

| File | Responsibility |
|---|---|
| `versions.tf` | Terraform/provider versions and AWS region configuration |
| `variables.tf` | Input variables and IPv4 CIDR validation |
| `main.tf` | VPC, common tags and naming prefix |
| `network.tf` | Two public and two private subnets across two available Availability Zones |
| `routing.tf` | Internet Gateway, route tables and subnet associations |
| `nacls.tf` | Separate stateless network ACLs for public and private subnets |
| `security.tf` | Baseline security group with no ingress or egress |
| `logging.tf` | VPC Flow Logs, CloudWatch log group and delivery IAM role |
| `iam.tf` | Dedicated EC2 workload role without attached permissions by default |
| `cloudtrail.tf` | Multi-region CloudTrail and protected S3 audit bucket |
| `backend.tf.example` | Inactive example of an encrypted S3 backend with native state locking |
| `outputs.tf` | VPC and subnet outputs |
| `terraform.tfvars.example` | Example values without secrets |

## Validate locally

Run these commands from this directory:

```powershell
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

`terraform plan` reads AWS data sources for available Availability Zones and the current account identity, so it requires working AWS credentials and network access. CI intentionally avoids `plan`, `apply` and `destroy`.

## IAM and audit controls

- The workload role has a dedicated EC2 trust policy and no attached permissions by default. Add narrowly scoped policies only after defining the workload.
- CloudTrail records management events in a multi-region trail and validates log files.
- The audit S3 bucket blocks public access, enforces bucket-owner object ownership, enables versioning, and enforces SSE-S3 encryption.
- CloudTrail delivery is restricted by a bucket policy to the CloudTrail service and the expected trail ARN.

## Network security decisions

- The public route table has a default route to the Internet Gateway. The private route table has no default Internet route.
- Public subnet NACLs allow VPC-internal traffic, inbound TCP 80/443, and TCP ephemeral ports (1024–65535) needed for stateless return traffic. They do not allow inbound SSH by default.
- Private subnet NACLs allow only traffic within the VPC CIDR.
- The baseline security group denies all inbound and outbound traffic and is not attached to a workload.
- Private subnets do not automatically assign public IPv4 addresses.

## NAT Gateway and costs

A NAT Gateway is intentionally not provisioned. It incurs hourly and data-processing charges. Revisit NAT only when a concrete outbound-connectivity requirement exists and current pricing has been reviewed.

CloudTrail, S3 storage/requests, and CloudWatch ingestion/storage may incur charges after deployment. Check current AWS pricing before any apply.

## Terraform state

No remote backend is active. `backend.tf.example` is documentation only; Terraform will not load it as a backend configuration. Before enabling remote state, create and secure the state bucket separately, enable versioning and encryption, restrict access to deployment roles, and confirm the locking method is supported by the installed Terraform version. Back up local state before migration.

This is a learning environment, not a production-ready landing zone.
