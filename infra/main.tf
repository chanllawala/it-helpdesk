# The default VPC is used deliberately. A purpose-built VPC with private
# subnets would need a NAT gateway for the container instance to pull images,
# and that alone costs about $32/month — more than everything else here
# combined, for a portfolio deployment that gains nothing from it.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_region" "current" {}

# CloudFront publishes the IP ranges its origin-facing servers use as a managed
# prefix list, which lets the container instance accept traffic from CloudFront
# and nothing else.
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

# Amazon's ECS-optimized AMI, resolved at plan time so the instance is never
# pinned to a stale image.
data "aws_ssm_parameter" "ecs_ami" {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2023/recommended/image_id"
}

locals {
  name = var.project_name
}
