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
- A dedicated EC2 workload IAM role with no permissions attached by default.
- A multi-region CloudTrail trail writing management events to a dedicated S3 bucket with public access blocked, versioning, SSE-S3 encryption, and log-file validation.
- Gitleaks secret scanning on pushes and pull requests.
- Common tags for project, environment, owner, and Terraform management.

Default subnet CIDRs are `10.0.1.0/24` and `10.0.2.0/24` for public subnets, and `10.0.11.0/24` and `10.0.12.0/24` for private subnets, inside `10.0.0.0/16`.

## Repository layout

- `terraform/versions.tf`: Terraform and AWS provider constraints.
- `terraform/variables.tf`: inputs and basic input validation.
- `terraform/main.tf`: VPC, naming convention, and common tags.
- `terraform/network.tf`: four subnets across two available zones.
- `terraform/routing.tf`: Internet Gateway, route tables, and subnet associations.
- `terraform/nacls.tf`: separate network ACLs for public and private subnets.
- `terraform/security.tf`: restrictive baseline security group.
- `terraform/logging.tf`: VPC Flow Logs and CloudWatch delivery role.
- `terraform/iam.tf`: dedicated workload IAM role.
- `terraform/cloudtrail.tf`: CloudTrail and protected S3 audit bucket.
- `terraform/backend.tf.example`: example only; remote state backend is not enabled.
- `.github/workflows/terraform.yml`: Terraform validation and Checkov scan.
- `.github/workflows/secrets.yml`: Gitleaks secret scanning.
- `docs/iam-audit-and-state.md`: IAM, audit logging, and state security decisions.
- `docs/secret-incident-response.md`: response procedure for exposed secrets.

## Local verification

Run from the `terraform` directory:

```powershell
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

A plan reads AWS data sources such as available Availability Zones and the current AWS account identity, so it requires working AWS credentials and network access. The GitHub Actions workflow deliberately does not run `terraform plan`, `apply`, or `destroy`; no AWS resources are created by CI.

## Security, state, and cost notes

- CloudTrail, S3 storage/requests, and CloudWatch Logs can incur charges after deployment. Review current AWS pricing before applying.
- The CloudTrail S3 bucket blocks public access, enforces bucket-owner object ownership, enables versioning, and uses SSE-S3 (AES-256). SSE-KMS can be considered if customer-managed key controls are required.
- The workload role has no attached permissions by default. Add only scoped permissions once a workload requirement is defined; do not create static access keys.
- No NAT Gateway is provisioned. Private subnets have no direct Internet route.
- The baseline security group denies ingress and egress and is not attached to a workload.
- No remote Terraform backend is active. `terraform/backend.tf.example` documents a possible S3 backend with encryption and native state locking, but the state bucket and access controls must be prepared separately before migration.
- The Checkov scan currently reports findings without failing CI. Review findings before treating the project as production-ready.
- Gitleaks helps detect secrets but does not replace credential rotation or incident response. Follow `docs/secret-incident-response.md` if a secret is exposed.
- This is a learning portfolio, not a production-ready landing zone.

Never commit access keys, passwords, Terraform state, plan files, or secret variable files.
