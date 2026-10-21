# Architecture and security documentation

## Scope

SecureCloudLab currently validates a minimal Terraform configuration locally.
The architecture consists of Terraform, the `hashicorp/local` provider, and a
single protected local report. Checkov scans the Terraform source as part of
the DevSecOps verification workflow.

## Security posture

The configuration contains no cloud credentials, secrets, cloud providers,
remote state, or billable infrastructure. The local report is configured with
`0600` file permissions and `0700` directory permissions. These controls are
configuration intent; platform-specific file-system behavior must be checked
after an explicit apply.

## Scanner coverage

Checkov evaluates resources only when a matching policy exists. The current
`local_file` resource has no built-in Terraform checks in the installed Checkov
release, so a scan can correctly report zero passed and zero failed checks.
That result means no applicable policy was evaluated, not that the project is
fully secure.

Future cloud resources should add controls for least-privilege IAM, network
exposure, encryption, audit logging, secret handling, and protected remote
Terraform state before deployment.
