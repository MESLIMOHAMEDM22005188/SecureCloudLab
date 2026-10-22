resource "aws_security_group" "intentionally_insecure" {
  name        = "negative-test-open-ssh"
  description = "Intentionally insecure fixture for Checkov negative testing"
  vpc_id      = "vpc-00000000"

  ingress {
    description = "Intentionally exposed SSH for security scanner testing"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
