# Retrieve the available Availability Zones in the selected region
data "aws_availability_zones" "available" {
  state = "available"
}

# PUBLIC SUBNET A
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = var.map_public_ip_on_launch

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-public-a"
    Function = "network"
    Tier     = "public"
  })
}

# PUBLIC SUBNET B
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = var.map_public_ip_on_launch

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-public-b"
    Function = "network"
    Tier     = "public"
  })
}

# PRIVATE SUBNET A
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-private-a"
    Function = "network"
    Tier     = "private"
  })
}

# PRIVATE SUBNET B
resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_b_cidr
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-private-b"
    Function = "network"
    Tier     = "private"
  })
}