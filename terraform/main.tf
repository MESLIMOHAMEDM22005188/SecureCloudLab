resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = {
    Name        = "securecloudlab-${var.environment}"
    Environment = var.environment
    Project     = "SecureCloudLab"
  }
}

