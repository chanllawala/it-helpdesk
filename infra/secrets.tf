# Secrets are generated here and stored in Secrets Manager rather than being
# typed into a tfvars file. Nobody has to handle the values, they never appear
# in the repository, and ECS injects them into the container at start time.
#
# They do land in Terraform state, so state must be treated as sensitive —
# see the remote state note in the README.

resource "random_password" "db" {
  length = 32
  # RDS rejects several punctuation characters in master passwords.
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "jwt" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name}/db-password"
  description             = "RDS master password for ${local.name}"
  recovery_window_in_days = 0 # Allows a clean destroy/recreate cycle.
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${local.name}/database-url"
  description             = "Full SQLAlchemy connection string for ${local.name}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = format(
    "postgresql://%s:%s@%s/%s",
    aws_db_instance.main.username,
    urlencode(random_password.db.result),
    aws_db_instance.main.endpoint,
    aws_db_instance.main.db_name,
  )
}

resource "aws_secretsmanager_secret" "jwt_key" {
  name                    = "${local.name}/jwt-secret-key"
  description             = "JWT signing key for ${local.name}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_key" {
  secret_id     = aws_secretsmanager_secret.jwt_key.id
  secret_string = random_password.jwt.result
}
