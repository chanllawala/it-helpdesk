resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR is free for 500 MB in the first year; without expiry every CI run would
# add another image until that fills up.
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the 10 most recent images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}-backend"
  retention_in_days = 7 # Indefinite retention is not free.
}

resource "aws_ecs_cluster" "main" {
  name = local.name
}

resource "aws_security_group" "ecs_instance" {
  name        = "${local.name}-ecs-instance"
  description = "ECS container instance; API reachable only via CloudFront"
  vpc_id      = data.aws_vpc.default.id

  tags = { Name = "${local.name}-ecs-instance" }
}

# The API port is open to CloudFront's origin-facing ranges only, so the
# instance's public address cannot be used to bypass CloudFront.
resource "aws_vpc_security_group_ingress_rule" "api_from_cloudfront" {
  security_group_id = aws_security_group.ecs_instance.id
  description       = "API from CloudFront edge locations only"
  from_port         = var.app_port
  to_port           = var.app_port
  ip_protocol       = "tcp"
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
}

# Needed to pull images and reach Secrets Manager. No inbound SSH rule exists;
# shell access is via Session Manager.
resource "aws_vpc_security_group_egress_rule" "instance_all" {
  security_group_id = aws_security_group.ecs_instance.id
  description       = "Outbound to ECR, Secrets Manager and monitored endpoints"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_launch_template" "ecs" {
  name_prefix   = "${local.name}-ecs-"
  image_id      = data.aws_ssm_parameter.ecs_ami.value
  instance_type = var.instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.ecs_instance.arn
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.ecs_instance.id]
  }

  # Joins the ECS cluster, then claims the fixed Elastic IP so CloudFront's
  # origin address survives this instance being replaced.
  user_data = base64encode(<<-EOF
    #!/bin/bash
    echo "ECS_CLUSTER=${aws_ecs_cluster.main.name}" >> /etc/ecs/ecs.config

    TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
      -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
    INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
      http://169.254.169.254/latest/meta-data/instance-id)

    aws ec2 associate-address \
      --region ${var.region} \
      --instance-id "$INSTANCE_ID" \
      --allocation-id ${aws_eip.api.allocation_id} \
      --allow-reassociation
  EOF
  )

  metadata_options {
    http_tokens = "required" # IMDSv2 only.
  }

  tag_specifications {
    resource_type = "instance"
    tags          = { Name = "${local.name}-ecs" }
  }
}

# An autoscaling group of exactly one, so a failed instance is replaced
# automatically rather than needing a manual rebuild.
resource "aws_autoscaling_group" "ecs" {
  name                = "${local.name}-ecs"
  vpc_zone_identifier = data.aws_subnets.default.ids
  min_size            = 1
  max_size            = 1
  desired_capacity    = 1
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.ecs.id
    version = "$Latest"
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = ""
    propagate_at_launch = true
  }
}

resource "aws_ecs_task_definition" "backend" {
  family             = "${local.name}-backend"
  network_mode       = "bridge"
  execution_role_arn = aws_iam_role.task_execution.arn

  # Sized to leave headroom on a 1 GB t3.micro for the ECS agent itself.
  cpu    = 512
  memory = 700

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
    essential = true

    portMappings = [{
      containerPort = var.app_port
      hostPort      = var.app_port
      protocol      = "tcp"
    }]

    environment = [
      # Served from the same domain as the frontend, so requests are
      # same-origin and CORS never comes into it.
      { name = "API_PREFIX", value = "/api" },
      { name = "CORS_ORIGINS", value = "" },
      { name = "ACCESS_TOKEN_EXPIRE_MINUTES", value = "60" },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "JWT_SECRET_KEY", valueFrom = aws_secretsmanager_secret.jwt_key.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:${var.app_port}/health').status==200 else 1)\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "${local.name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count

  # One instance publishing a fixed host port cannot run two tasks at once, so
  # the old task is stopped before the new one starts. That means a few seconds
  # of downtime per deploy, which is the accepted trade for staying inside the
  # free tier — a second instance or a load balancer would remove it.
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  # The instance must have registered with the cluster before a task can be placed.
  depends_on = [aws_autoscaling_group.ecs]
}
