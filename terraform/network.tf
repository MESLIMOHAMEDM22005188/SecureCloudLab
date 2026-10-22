# PUBLIC SUBNET
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name        = "securecloudlab-public-${var.environment}"
    Environment = var.environment
    Project     = "SecureCloudLab"
    Tier        = "public"
  }
}

# PRIVATE SUBNET
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "securecloudlab-private-${var.environment}"
    Environment = var.environment
    Project     = "SecureCloudLab"
    Tier        = "private"
  }
}