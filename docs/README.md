# Architecture and security documentation

## Scope

SecureCloudLab defines an AWS VPC with two public and two private subnets across two available Availability Zones. Terraform manages the VPC, Internet Gateway, route tables, a restrictive baseline security group, and VPC Flow Logs delivered to CloudWatch Logs.

GitHub Actions performs Terraform formatting, initialization and validation on pushes and pull requests. A Checkov scan reports infrastructure-as-code findings; its current invocation is non-blocking, so findings must still be reviewed rather than interpreted as a passing security certification.

## Security controls

- Public subnets use a route table with a default route to the Internet Gateway.
- Private subnets use a separate route table without a default Internet route.
- The baseline security group has no ingress or egress rules and is not attached to a workload.
- VPC Flow Logs are configured for all traffic and sent to a CloudWatch log group with 30-day retention.
- The Flow Logs delivery role is restricted to writing to the configured log group.
- Git ignore rules exclude local state, plan files, credentials, and editor files.

## Limitations and operational notes

- Flow Logs and CloudWatch Logs may incur charges after deployment.
- No NAT Gateway is provided, so private subnets have no Internet egress.
- No CloudTrail trail, GuardDuty configuration, alerting, or workload IAM roles are included yet.
- The security group is a baseline only; it does not protect a workload until attached.
- Terraform uses local state by default; a protected remote backend and locking are not configured.
- CIDR inputs are checked for valid IPv4 notation, but overlap and containment between custom CIDRs still require review.
- CI does not deploy resources and does not run a plan requiring AWS credentials.

A successful Terraform validation confirms syntax and internal references, not that the architecture is production-ready or that every security control is effective.
