# Security monitoring and compliance baseline

## AWS Config

The Terraform configuration creates an AWS Config recorder for supported resource types, a delivery channel to the protected audit S3 bucket, and AWS-managed rules for:

- Public S3 read access prohibited.
- Public S3 write access prohibited.
- Root account MFA enabled.
- CloudTrail enabled.
- EBS volumes encrypted.

These rules provide a deliberately small compliance baseline; they are not a certification or complete account-wide policy. Review the compliance results in the AWS Config console after deployment. Config recording and rule evaluations can incur charges. The configuration uses the AWS-managed `AWS_ConfigRole` policy; review its current permissions against your organization's IAM standards.

## GuardDuty and EventBridge

GuardDuty is enabled by Terraform. An EventBridge rule matches events with source `aws.guardduty` and detail type `GuardDuty Finding`, then publishes them to the SNS topic exposed as Terraform output `security_alerts_topic_arn`.

After deployment:

1. Retrieve `security_alerts_topic_arn` from Terraform output.
2. Subscribe an approved endpoint (for example, an operations email address) to the SNS topic.
3. Confirm the subscription.
4. Verify delivery using a controlled test finding supported by GuardDuty, following AWS guidance.
5. Document the finding, notification delivery, and response owner.

No email endpoint is hard-coded into Terraform. A topic without a confirmed subscription does not deliver email notifications. GuardDuty and EventBridge/SNS usage may incur charges.

## CI quality gates

For pull requests that change Terraform, workflow files, the TFLint configuration, documentation, or the root README, GitHub Actions runs:

- `terraform fmt -check -recursive` — formatting failures block the workflow.
- `terraform init -backend=false` and `terraform validate` — initialization or validation failures block the workflow.
- `terraform test` — plan-only assertions use mocked AWS data sources and do not deploy resources.
- TFLint with the AWS ruleset — lint failures block the workflow.
- Checkov — medium/high/critical findings block the workflow; low/informational findings are non-blocking.
- Gitleaks — scans pushes and pull requests.

CI does not run `terraform plan`, `apply`, or `destroy` and does not require AWS credentials. Review scanner findings rather than suppressing them without justification.

## Operational limitations

- The AWS Config and GuardDuty resources are defined as code but are not deployed until an authorized operator reviews and applies Terraform.
- A successful Terraform plan or test is not proof that AWS service delivery, account-level prerequisites, or real alert delivery works; verify these after deployment.
- Review AWS pricing, retention requirements, alert ownership, and account/region coverage before enabling in a real account.
