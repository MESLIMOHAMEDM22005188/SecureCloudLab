
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.9"
    }
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

resource "local_file" "security_report" {
  filename             = "${path.module}/security-report.txt"
  content              = "SecureCloudLab environment: ${var.environment}\n"
  file_permission      = "0600"
  directory_permission = "0700"
}

