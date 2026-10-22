# SecureCloudLab

Portfolio project for learning AWS infrastructure, Terraform and cloud security practices.

## Current architecture

- One VPC with a configurable IPv4 CIDR.
- One public subnet and one private subnet, currently configured in the same Availability Zone.
- An Internet Gateway and a public route table with a default route to the Internet Gateway.
- A private route table with no default Internet route.
- DNS support and DNS hostnames configurable through input variables.
- Common resource tags: Project, Environment, Owner and ManagedBy.
- Terraform outputs for the VPC and subnet identifiers.

## Repository structure

- `terraform/versions.tf`: Terraform and AWS provider constraints.
- `terraform/variables.tf`: input variables and validations.
- `terraform/main.tf`: VPC, naming convention and common tags.
- `terraform/network.tf`: subnet resources.
- `terraform/routing.tf`: Internet Gateway and route tables.
- `terraform/security.tf`: reserved for future security resources.
- `terraform/logging.tf`: reserved for future logging resources.
- `terraform/outputs.tf`: useful resource outputs.
- `terraform/terraform.tfvars.example`: non-secret example configuration.

## Local checks

Run from the `terraform` directory:

```powershell
terraform fmt -recursive
terraform init -backend=false
terraform validate
terraform plan
```

`terraform plan` may require AWS provider configuration or credentials depending on the provider and resources. These commands do not deploy infrastructure; `terraform apply` is not part of the validation workflow.

## Current limitations

- No Security Groups or Network ACL policies are defined in this stage.
- VPC Flow Logs, CloudTrail, GuardDuty and alerting are not configured here.
- The public and private subnets currently use the same Availability Zone.
- The private subnet has no NAT Gateway or outbound Internet route.
- Terraform state has not been configured with a remote backend.
- The project is a learning portfolio and is not yet a production-ready landing zone.

Never commit access keys, passwords, state files, plan files or secret variable files.
