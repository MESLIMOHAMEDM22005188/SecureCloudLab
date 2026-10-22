# SecureCloudLab — Security Test Plan

## 1. Objective

Verify that the Terraform configuration is valid and that security controls detect unsafe infrastructure configurations before deployment.

## 2. Test cases

| ID | Test | Expected result |
|---|---|---|
| TC-01 | Terraform formatting | The check passes when all files are correctly formatted. |
| TC-02 | Terraform validation | The check passes when the configuration is valid. |
| TC-03 | Public SSH access | A rule exposing SSH to the entire Internet is detected. |
| TC-04 | Public RDP access | A rule exposing RDP to the entire Internet is detected. |
| TC-05 | Network logging | Missing required VPC Flow Logs are detected. |
| TC-06 | Secret detection | A test-only fake secret is detected by the scanner. |

## 3. Safety constraints

- No AWS resources are deployed during the initial validation phase.
- No real credentials or secrets are committed to Git.
- No Terraform apply or destroy command is part of the validation pipeline.
- Every security exception must be documented and justified.

## 4. Evidence

For each test, record the command, expected result, actual result, and relevant CI log or screenshot.

## 5. Current limitations

The initial Terraform configuration uses the local provider only. AWS-specific controls cannot be tested until the corresponding AWS resources and policies are implemented.