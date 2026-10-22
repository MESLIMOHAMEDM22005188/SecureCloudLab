# SecureCloudLab — Security Test Plan

## 1. Objective

Verify Terraform configuration quality and scan infrastructure-as-code for common security misconfigurations before any AWS deployment.

## 2. Automated checks

| ID | Check | Expected result |
|---|---|---|
| TC-01 | Terraform formatting | `terraform fmt -check -recursive` completes without formatting changes. |
| TC-02 | Terraform initialization | Providers initialize with `terraform init -backend=false`; no backend is configured. |
| TC-03 | Terraform validation | `terraform validate` reports a valid configuration. |
| TC-04 | IaC security scan | Checkov reports applicable findings for review. The current CI scan is non-blocking. |
| TC-05 | Secret hygiene | No credentials, secret variable files, state files, or plan files are tracked. |
| TC-06 | Route isolation | Public subnets use the Internet Gateway route table; private subnets use a route table without a default Internet route. |
| TC-07 | Security Group review | Baseline security group has no ingress/egress rules and is not attached to a workload. |
| TC-08 | Network ACL review | Public and private subnets use separate NACLs; private NACL permits only VPC-CIDR traffic. |
| TC-09 | Private subnet exposure | Private subnets do not auto-assign public IPv4 addresses and have no direct Internet route. |
| TC-10 | Flow Logs configuration | VPC Flow Logs target the configured CloudWatch log group and retention is 30 days. |
| TC-11 | NAT cost decision | No NAT Gateway is created in the baseline; document the requirement and review pricing before enabling one. |

## 3. Safety constraints

- The CI workflow does not run `terraform plan`, `apply`, or `destroy`.
- No real credentials or secrets are committed to Git.
- Do not deploy the infrastructure without reviewing AWS permissions and potential CloudWatch charges.
- A NAT Gateway is intentionally omitted because it incurs ongoing charges; private subnets have no Internet egress route.
- Every security exception or accepted scanner finding must be documented and justified.

## 4. Evidence

For each test, record the command, expected result, actual result, and relevant CI log or screenshot. Do not mark a test as passed until its result has been observed.

## 5. Known limitations

- The baseline security group is not attached to a workload.
- The public NACL allows inbound HTTP/HTTPS and ephemeral TCP ports; no application workload currently exists to validate actual traffic needs.
- Private subnet NACLs permit only VPC-internal traffic. If a NAT Gateway or other outbound path is added later, review the NACL rules as well as the route table.
- The private subnets have no NAT Gateway or default Internet route.
- CIDR syntax is validated, but overlap and VPC containment for custom CIDRs are not automatically proven.
- Checkov is currently non-blocking and therefore does not constitute a security gate.
- No CloudTrail trail, GuardDuty configuration, alerting, remote Terraform backend, or state locking is configured.
