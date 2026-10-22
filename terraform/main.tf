locals {
  name_prefix = "securecloudlab-${var.environment}"

  common_tags = {
    Project     = "SecureCloudLab"
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-vpc"
    Function = "network"
  })
}
