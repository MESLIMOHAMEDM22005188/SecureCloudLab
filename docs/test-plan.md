# SecureCloudLab — Security Test Plan

## 1. Objective

Verify Terraform configuration quality and scan infrastructure-as-code for common security misconfigurations before any AWS deployment.

## 2. Automated and configuration checks

| ID | Check | Expected result |
|---|---|---|
| TC-01 | Terraform formatting | `terraform fmt -check -recursive` completes without formatting changes. |
| TC-02 | Terraform initialization | `terraform init -backend=false` initializes providers; no backend is configured. |
| TC-03 | Terraform validation | `terraform validate` reports a valid configuration. |
| TC-04 | Terraform tests | `terraform test` passes plan-only assertions using mocked AWS data sources; no resources are deployed. |
| TC-05 | TFLint | AWS provider lint rules complete without errors. |
| TC-06 | IaC security scan | Checkov findings are reported but do not currently fail CI while baseline findings are triaged; every finding must be reviewed and documented. |
| TC-07 | Secret hygiene | Gitleaks runs on pushes and pull requests; no credentials, secret variable files, state files, or plan files are tracked. |
| TC-08 | Route isolation | Public subnets use the Internet Gateway route table; private subnets have no default Internet route. |
| TC-09 | Security Group review | Baseline security group has no ingress/egress rules and is not attached to a workload. |
| TC-10 | Network ACL review | Public and private subnets use separate NACLs; private NACL permits only VPC-CIDR traffic. |
| TC-11 | VPC Flow Logs | Flow Logs target CloudWatch Logs with 30-day retention. |
| TC-12 | Workload IAM role | Dedicated EC2 role exists with no attached permissions by default; no static keys are created. |
| TC-13 | CloudTrail | Multi-region trail enabled with global service events and log-file validation. |
| TC-14 | Audit bucket access | S3 Block Public Access enabled; bucket policy restricts writes to CloudTrail and AWS Config delivery. |
| TC-15 | Audit bucket encryption/versioning | Default SSE-S3 encryption and S3 versioning are configured. |
| TC-16 | AWS Config compliance | Recorder, delivery channel, and five managed rules are defined; review actual compliance results after deployment. |
| TC-17 | GuardDuty alert route | GuardDuty findings match an EventBridge rule and target the SNS topic; confirm an endpoint subscription and delivery after deployment. |
| TC-18 | Remote state readiness | Backend example is inactive; remote state is not migrated or enabled automatically. |
| TC-19 | NAT cost decision | No NAT Gateway is created in the baseline; review need and pricing before adding one. |

## 3. Safety constraints

- CI does not run `terraform plan`, `apply`, or `destroy`.
- No real credentials or secrets are committed to Git.
- Do not deploy without reviewing AWS permissions and possible AWS Config, GuardDuty, CloudTrail, S3, SNS, EventBridge, and CloudWatch charges.
- A NAT Gateway is intentionally omitted; private subnets have no Internet egress route.
- Every security exception or accepted scanner finding must be documented and justified.

## 4. Evidence

For each test, record the command, expected result, actual result, and relevant CI log or screenshot. Do not mark a test as passed until its result has been observed.

## 5. Known limitations

- AWS Config and GuardDuty are configured in code but are not deployed or runtime-verified.
- GuardDuty notifications require a confirmed SNS subscription.
- The workload role intentionally has no attached permissions and is not yet used by an application.
- The baseline security group is not attached to a workload.
- The public NACL allows inbound HTTP/HTTPS and ephemeral TCP ports; actual workload requirements have not been tested.
- Private subnet NACLs permit only VPC-internal traffic. Reassess them if an outbound path is introduced.
- CIDR syntax is validated, but overlap and VPC containment for custom CIDRs are not automatically proven.
- The S3 backend example is inactive; remote state, locking, and migration are not configured.
- Gitleaks workflow results must be checked in GitHub Actions; a configured scanner is not proof that every historical commit is clean.
