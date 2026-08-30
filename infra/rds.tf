resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "Postgres, reachable only from the ECS container instance"
  vpc_id      = data.aws_vpc.default.id

  tags = { Name = "${local.name}-db" }
}

# The database accepts connections from the container instance's security group
# and from nowhere else. It has no public address.
resource "aws_vpc_security_group_ingress_rule" "db_from_ecs" {
  security_group_id            = aws_security_group.db.id
  description                  = "Postgres from the ECS container instance"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.ecs_instance.id
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name}-db"
  engine         = "postgres"
  engine_version = "16"

  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = 0 # Autoscaling off, so storage cannot silently grow past the free tier.
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "helpdesk"
  username = "helpdesk"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false

  multi_az                = false # Multi-AZ is not free tier eligible.
  backup_retention_period = 7
  skip_final_snapshot     = true
  deletion_protection     = false

  # Postgres 16 minor versions are patched in place during the maintenance window.
  auto_minor_version_upgrade = true

  tags = { Name = "${local.name}-db" }
}
