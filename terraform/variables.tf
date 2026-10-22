variable "aws_region" {
  description = "AWS region used by SecureCloudLab"
  type        = string
  default     = "eu-west-3"

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be dev, test, or prod."
  }
}

variable "owner" {
  description = "Owner or maintainer of the project resources"
  type        = string
  default     = "SecureCloudLab"

  validation {
    condition     = length(trimspace(var.owner)) > 0
    error_message = "Owner must not be empty."
  }
}

variable "vpc_cidr" {
  description = "IPv4 CIDR block of the main VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "public_subnet_cidr" {
  description = "IPv4 CIDR block of the first public subnet"
  type        = string
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrnetmask(var.public_subnet_cidr))
    error_message = "public_subnet_cidr must be a valid IPv4 CIDR block."
  }
}

variable "public_subnet_b_cidr" {
  description = "IPv4 CIDR block of the second public subnet"
  type        = string
  default     = "10.0.2.0/24"

  validation {
    condition     = can(cidrnetmask(var.public_subnet_b_cidr))
    error_message = "public_subnet_b_cidr must be a valid IPv4 CIDR block."
  }
}

variable "private_subnet_cidr" {
  description = "IPv4 CIDR block of the first private subnet"
  type        = string
  default     = "10.0.11.0/24"

  validation {
    condition     = can(cidrnetmask(var.private_subnet_cidr))
    error_message = "private_subnet_cidr must be a valid IPv4 CIDR block."
  }
}

variable "private_subnet_b_cidr" {
  description = "IPv4 CIDR block of the second private subnet"
  type        = string
  default     = "10.0.12.0/24"

  validation {
    condition     = can(cidrnetmask(var.private_subnet_b_cidr))
    error_message = "private_subnet_b_cidr must be a valid IPv4 CIDR block."
  }
}

variable "enable_dns_support" {
  description = "Enable DNS resolution in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "map_public_ip_on_launch" {
  description = "Automatically assign public IP addresses to public subnet instances"
  type        = bool
  default     = true
}

variable "allowed_ssh_cidr" {
  description = "Trusted IPv4 CIDR reserved for a future SSH ingress rule"
  type        = string
  default     = "127.0.0.1/32"

  validation {
    condition     = can(cidrnetmask(var.allowed_ssh_cidr)) && var.allowed_ssh_cidr != "0.0.0.0/0"
    error_message = "allowed_ssh_cidr must be a valid IPv4 CIDR and must not allow the entire Internet."
  }
}
