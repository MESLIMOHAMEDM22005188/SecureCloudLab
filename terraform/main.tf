resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "securecloudlab-${var.environment}"
    Environment = var.environment
    Project     = "SecureCloudLab"
  }
}