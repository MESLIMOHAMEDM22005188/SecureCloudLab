# PUBLIC SUBNET
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = var.map_public_ip_on_launch

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
  cidr_block        = var.private_subnet_cidr
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "securecloudlab-private-${var.environment}"
    Environment = var.environment
    Project     = "SecureCloudLab"
    Tier        = "private"
  }
}
