# SecureCloudLab

SecureCloudLab is a portfolio project for learning AWS networking, Terraform, and practical cloud-security controls. The repository is designed to support local validation and pull-request checks before any cloud deployment.

## Architecture

- One configurable IPv4 VPC.
- Two public and two private subnets across two available Availability Zones.
- An Internet Gateway and a public route table with a default route to the Internet Gateway.
- A private route table with no default Internet route and no NAT Gateway.
- Separate subnet NACLs: public NACL allows VPC-internal traffic, TCP 80/443, and TCP ephemeral ports for stateless return traffic; private NACL allows only VPC-CIDR traffic.
- A baseline security group with no ingress or egress rules; it is not attached to a workload yet.
- VPC Flow Logs delivered to a CloudWatch Logs group with 30-day retention.
- Common tags for project, environment, owner, and Terraform management.
- Outputs for the VPC and both pairs of subnet IDs.

Default subnet CIDRs are `10.0.1.0/24` and `10.0.2.0/24` for public subnets, and `10.0.11.0/24` and `10.0.12.0/24` for private subnets, inside `10.0.0.0/16`.

## Repository layout

- `terraform/versions.tf`: Terraform and AWS provider constraints.
- `terraform/variables.tf`: inputs and basic input validation.
- `terraform/main.tf`: VPC, naming convention, and common tags.
- `terraform/network.tf`: four subnets across two available zones.
- `terraform/routing.tf`: Internet Gateway, route tables, and subnet associations.
- `terraform/nacls.tf`: separate network ACLs for public and private subnets.
- `terraform/security.tf`: restrictive baseline security group.
- `terraform/logging.tf`: VPC Flow Logs, CloudWatch log group, and least-privilege delivery role.
- `terraform/outputs.tf`: VPC and subnet identifiers.
- `terraform/terraform.tfvars.example`: non-secret example configuration.
- `.github/workflows/terraform.yml`: pull-request and push validation.

## Local verification

Run from the `terraform` directory:

```powershell
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

A plan reads AWS data sources such as available Availability Zones and therefore requires working AWS credentials and network access:

```powershell
terraform plan
```

The GitHub Actions workflow deliberately does not run `terraform plan`, `apply`, or `destroy`, and it does not need AWS credentials. No cloud resources are created by the verification workflow.

## Security and cost notes

- VPC Flow Logs and CloudWatch Logs can incur charges after deployment. Review AWS pricing and log volume before applying.
- No NAT Gateway is provisioned. It would provide outbound Internet connectivity to private workloads but creates ongoing hourly and data-processing charges; it should be added only when there is a defined requirement and after reviewing current pricing.
- Private subnets do not automatically assign public IPv4 addresses and have no direct Internet route.
- The baseline security group denies ingress and egress and is not attached to a workload. Add narrowly scoped rules only when a workload and its requirements are defined.
- NACLs are stateless, so response traffic must be allowed explicitly. The private NACL currently restricts traffic to the VPC CIDR.
- No remote Terraform backend or state locking is configured. Do not use this configuration for team/production state management as-is.
- The current CI Checkov scan is configured to report findings without failing the workflow; review and resolve findings before treating the project as production-ready.
- This is a learning portfolio, not a production-ready landing zone.

Never commit access keys, passwords, Terraform state, plan files, or secret variable files.
