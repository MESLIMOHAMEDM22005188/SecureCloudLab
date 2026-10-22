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
| `nacls.tf` | Separate stateless network ACLs for public and private subnets |
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

## Network security decisions

- The public route table has a default route to the Internet Gateway. The private route table has no default Internet route.
- Public subnet NACLs allow VPC-internal traffic, inbound TCP 80/443, and TCP ephemeral ports (1024–65535) needed for stateless return traffic. They do not allow inbound SSH by default.
- Private subnet NACLs allow only traffic within the VPC CIDR. Because NACLs are stateless, rules must be updated deliberately if the private subnet traffic requirements change.
- The baseline security group denies all inbound and outbound traffic and is not attached to a workload. Add narrowly scoped rules only after defining a workload requirement.
- Private subnets do not automatically assign public IPv4 addresses.

## NAT Gateway and costs

A NAT Gateway is intentionally **not provisioned**. It would allow private-subnet resources to initiate outbound connections without accepting unsolicited inbound connections, but it incurs hourly and data-processing charges (and typically requires one per Availability Zone for resilient production designs). For this learning baseline, private subnets remain without direct Internet egress to avoid unnecessary cost. Revisit NAT only when a concrete outbound-update or package-download requirement exists, and review current AWS pricing first.

## Logging and deployment

VPC Flow Logs are configured to send all VPC traffic to CloudWatch Logs with 30-day retention. CloudWatch ingestion and storage may incur charges after deployment. Review AWS pricing and permissions before any apply.

No remote backend is configured. This is a learning environment, not a production-ready landing zone.
