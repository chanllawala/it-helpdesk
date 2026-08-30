variable "project_name" {
  type        = string
  default     = "it-helpdesk"
  description = "Prefix for all resource names."
}

variable "region" {
  type        = string
  default     = "eu-west-2"
  description = "AWS region. Free tier applies per account, not per region."
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "ECS container instance type. t3.micro is free tier eligible for 12 months."
}

variable "db_instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "RDS instance class. db.t3.micro is free tier eligible for 12 months."
}

variable "db_allocated_storage" {
  type        = number
  default     = 20
  description = "GB of RDS storage. The free tier covers 20."
}

variable "app_port" {
  type        = number
  default     = 8000
  description = "Port the container listens on, and the host port it is published to."
}

variable "desired_count" {
  type        = number
  default     = 1
  description = "Number of tasks. One container instance publishes a fixed host port, so this stays at 1."
}

variable "github_repository" {
  type        = string
  default     = "chanllawala/it-helpdesk"
  description = "owner/repo allowed to assume the deploy role via OIDC."
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Image tag to deploy. CI overrides this with the commit SHA."
}
