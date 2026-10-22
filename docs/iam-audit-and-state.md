# IAM, audit logging, and Terraform state controls

## IAM least privilege

- `terraform/iam.tf` creates a dedicated EC2 workload role with a trust policy and no attached permissions by default.
- Add only action/resource-scoped policies after defining the workload. Avoid wildcard permissions unless technically required and justified.
- Use IAM roles and short-lived credentials. Do not create or commit static access keys.
- CloudTrail uses the S3 bucket policy to permit only the CloudTrail service to deliver logs for the expected trail ARN.

## CloudTrail and S3 audit bucket

- `terraform/cloudtrail.tf` enables a multi-region trail, global service events, log-file validation, and management-event logging (CloudTrail's default event selector).
- The dedicated S3 bucket blocks public access, enforces bucket-owner object ownership, enables versioning, and enforces SSE-S3 (AES-256) at rest.
- SSE-S3 is the simpler baseline. Use SSE-KMS if key separation, customer-managed key policies, or additional audit controls are required; then review KMS cost and key administration.
- Bucket names are globally unique in AWS. The configured name includes environment, account ID, and region, but deployment may still fail if the name is already taken.
- CloudTrail, S3 storage, requests, and data events beyond the default management-event selection can incur charges. Review AWS pricing before deployment.

## Terraform state

- Local state is still the default. `terraform/backend.tf.example` documents a remote S3 backend but is not active Terraform configuration.
- Before enabling remote state, create and secure the state bucket separately, configure encryption and versioning, restrict access, and choose a supported state-locking approach. The example uses S3 native lockfiles with a compatible Terraform version.
- Backend initialization and state migration are intentionally not automated by CI. Back up and review the state before migrating; never commit state files or backend credentials.

## Secret detection

- `.github/workflows/secrets.yml` runs Gitleaks on pushes and pull requests.
- If a secret is detected, revoke/rotate it first, investigate use, remove it from tracked files/history as appropriate, then re-run scanning. Follow `docs/secret-incident-response.md`.
- A scanner reduces risk but does not replace prevention, least privilege, rotation, or incident response.
