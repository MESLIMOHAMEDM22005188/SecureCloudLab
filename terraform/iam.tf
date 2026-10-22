# Example workload role with no permissions attached by default.
# Add narrowly scoped policies only when a workload requirement is defined.
data "aws_iam_policy_document" "workload_assume_role" {
  statement {
    sid     = "AllowEc2WorkloadAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "workload" {
  name                 = "${local.name_prefix}-workload-role"
  assume_role_policy   = data.aws_iam_policy_document.workload_assume_role.json
  max_session_duration = 3600

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-workload-role"
    Function = "identity"
  })
}

# No access keys or static credentials are created by this configuration.
# CloudTrail delivery uses its own service role in cloudtrail.tf.
