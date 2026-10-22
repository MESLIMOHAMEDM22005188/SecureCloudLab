# SecureCloudLab — Security Test Plan

## 1. Objective

Verify Terraform configuration quality and scan infrastructure-as-code for common security misconfigurations before any AWS deployment.

## 2. Automated and configuration checks

| ID | Check | Expected result |
|---|---|---|
| TC-01 | Terraform formatting | `terraform fmt -check -recursive` completes without formatting changes. |
| TC-02 | Terraform initialization | Providers initialize with `terraform init -backend=false`; no backend is configured. |
| TC-03 | Terraform validation | `terraform validate` reports a valid configuration. |
| TC-04 | IaC security scan | Checkov findings are reviewed; current CI mode is non-blocking. |
| TC-05 | Secret hygiene | No credentials, secret variable files, state files, or plan files are tracked. |
| TC-06 | Route isolation | Public subnets use the Internet Gateway route table; private subnets have no default Internet route. |
| TC-07 | Security Group review | Baseline security group has no ingress/egress rules and is not attached to a workload. |
| TC-08 | Network ACL review | Public and private subnets use separate NACLs; private NACL permits only VPC-CIDR traffic. |
| TC-09 | Private subnet exposure | Private subnets do not auto-assign public IPv4 addresses and have no direct Internet route. |
| TC-10 | VPC Flow Logs | Flow Logs target CloudWatch Logs with 30-day retention. |
| TC-11 | Workload IAM role | Dedicated EC2 role exists with no attached permissions by default; no static keys are created. |
| TC-12 | CloudTrail | Multi-region trail enabled with global service events and log-file validation. |
| TC-13 | Audit bucket access | S3 Block Public Access enabled; bucket policy restricts writes to CloudTrail delivery. |
| TC-14 | Audit bucket encryption | Default SSE-S3 encryption is configured. |
| TC-15 | Audit bucket versioning | S3 versioning is enabled. |
| TC-16 | Secret scanner | Gitleaks workflow runs on pushes and pull requests; verify results in GitHub Actions. |
| TC-17 | Remote state readiness | Backend example is inactive; remote state is not migrated or enabled automatically. |
| TC-18 | NAT cost decision | No NAT Gateway is created in the baseline; review need and pricing before adding one. |

## 3. Safety constraints

- CI does not run `terraform plan`, `apply`, or `destroy`.
- No real credentials or secrets are committed to Git.
- Do not deploy without reviewing AWS permissions and possible CloudTrail, S3, and CloudWatch charges.
- A NAT Gateway is intentionally omitted; private subnets have no Internet egress route.
- Every security exception or accepted scanner finding must be documented and justified.

## 4. Evidence

For each test, record the command, expected result, actual result, and relevant CI log or screenshot. Do not mark a test as passed until its result has been observed.

## 5. Known limitations

- The workload role intentionally has no attached permissions and is not yet used by an application.
- The baseline security group is not attached to a workload.
- The public NACL allows inbound HTTP/HTTPS and ephemeral TCP ports; actual workload requirements have not been tested.
- Private subnet NACLs permit only VPC-internal traffic. Reassess them if an outbound path is introduced.
- CIDR syntax is validated, but overlap and VPC containment for custom CIDRs are not automatically proven.
- Checkov is currently non-blocking.
- The S3 backend example is inactive; remote state, locking, and migration are not configured.
- Gitleaks workflow results must be checked in GitHub Actions; a configured scanner is not proof that every historical commit is clean.
