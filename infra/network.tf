# CloudFront needs an origin address that does not change. The container
# instance lives in an autoscaling group, so a replacement would otherwise come
# back on a new IP and silently break the API origin.
#
# A load balancer is the usual answer and costs about $18/month. Instead the
# instance claims a fixed Elastic IP on boot, which is free while associated.
resource "aws_eip" "api" {
  domain = "vpc"
  tags   = { Name = "${local.name}-api" }
}

data "aws_iam_policy_document" "associate_eip" {
  statement {
    actions   = ["ec2:AssociateAddress"]
    resources = ["*"] # AssociateAddress does not support resource-level permissions.
  }
}

resource "aws_iam_role_policy" "associate_eip" {
  name   = "${local.name}-associate-eip"
  role   = aws_iam_role.ecs_instance.id
  policy = data.aws_iam_policy_document.associate_eip.json
}
