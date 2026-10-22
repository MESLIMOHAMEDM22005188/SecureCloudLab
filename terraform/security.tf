resource "aws_security_group" "baseline" {
  name        = "${local.name_prefix}-baseline-sg"
  description = "Restrictive baseline security group; no ingress or egress until explicitly required"
  vpc_id      = aws_vpc.main.id

  ingress = []
  egress  = []

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-baseline-sg"
    Function = "security"
    Tier     = "baseline"
  })
}
