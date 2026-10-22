# Plan-only tests use mocked AWS data sources; no AWS credentials or deployment are required.
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["eu-west-3a", "eu-west-3b"]
    }
  }

  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
      arn        = "arn:aws:iam::123456789012:user/terraform-test"
      user_id    = "AIDATESTUSER"
    }
  }
}

run "network_and_security_baseline" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "The default VPC CIDR should be 10.0.0.0/16."
  }

  assert {
    condition     = aws_subnet.private_a.map_public_ip_on_launch == false
    error_message = "Private subnet A must not auto-assign public IP addresses."
  }

  assert {
    condition     = aws_subnet.private_b.map_public_ip_on_launch == false
    error_message = "Private subnet B must not auto-assign public IP addresses."
  }

  assert {
    condition     = aws_iam_role.workload.max_session_duration == 3600
    error_message = "The workload role session duration should be limited to one hour."
  }

  assert {
    condition     = aws_s3_bucket_versioning.audit_logs.versioning_configuration[0].status == "Enabled"
    error_message = "Audit bucket versioning must be enabled."
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.audit_logs.block_public_acls && aws_s3_bucket_public_access_block.audit_logs.block_public_policy && aws_s3_bucket_public_access_block.audit_logs.ignore_public_acls && aws_s3_bucket_public_access_block.audit_logs.restrict_public_buckets
    error_message = "All four S3 Block Public Access controls must be enabled on the audit bucket."
  }

  assert {
    condition     = aws_cloudtrail.audit.is_multi_region_trail && aws_cloudtrail.audit.enable_log_file_validation
    error_message = "CloudTrail must be multi-region and validate log files."
  }

  assert {
    condition     = aws_guardduty_detector.main.enable
    error_message = "GuardDuty must be enabled in the planned configuration."
  }
}
