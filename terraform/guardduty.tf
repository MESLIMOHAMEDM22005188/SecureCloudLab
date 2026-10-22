# GuardDuty analyzes supported AWS data sources for suspicious activity.
# Findings are forwarded to SNS through EventBridge; subscribe an email endpoint
# to the topic after deployment to receive notifications.
resource "aws_guardduty_detector" "main" {
  enable = true

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-guardduty"
    Function = "threat-detection"
  })
}

resource "aws_sns_topic" "security_alerts" {
  name = "${local.name_prefix}-security-alerts"

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-security-alerts"
    Function = "alerting"
  })
}

data "aws_iam_policy_document" "security_alerts_topic" {
  statement {
    sid    = "AllowEventBridgeToPublish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.security_alerts.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.guardduty_findings.arn]
    }
  }
}

resource "aws_sns_topic_policy" "security_alerts" {
  arn    = aws_sns_topic.security_alerts.arn
  policy = data.aws_iam_policy_document.security_alerts_topic.json
}

resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "${local.name_prefix}-guardduty-findings"
  description = "Route GuardDuty findings to the SecureCloudLab security alert topic."

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
  })

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-guardduty-findings"
    Function = "alerting"
  })
}

resource "aws_cloudwatch_event_target" "guardduty_findings" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "security-alerts-sns"
  arn       = aws_sns_topic.security_alerts.arn

  depends_on = [aws_sns_topic_policy.security_alerts]
}

output "security_alerts_topic_arn" {
  description = "SNS topic ARN for GuardDuty notifications; subscribe an endpoint to receive alerts."
  value       = aws_sns_topic.security_alerts.arn
}
