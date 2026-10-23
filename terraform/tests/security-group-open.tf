terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.36.0"
    }
  }
}

resource "aws_security_group" "intentionally_insecure_test" {
  name        = "intentionally-insecure-test"
  description = "INTENTIONAL VULNERABILITY FOR NEGATIVE TESTS ONLY"
  vpc_id      = "vpc-0000000"

  ingress {
    description = "INTENTIONAL BAD CONFIGURATION - SSH OPEN TO INTERNET"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
