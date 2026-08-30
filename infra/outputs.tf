output "site_url" {
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
  description = "The application. Serves the React app, and the API under /api."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "Push target for the backend image."
}

output "frontend_bucket" {
  value       = aws_s3_bucket.frontend.bucket
  description = "Sync the built frontend here."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.main.id
  description = "Needed to invalidate the cache after a frontend deploy."
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.backend.name
}

output "api_public_dns" {
  value       = aws_eip.api.public_dns
  description = "Origin address for the API. Not reachable directly; the security group admits CloudFront only."
}

output "github_actions_values" {
  description = "Repository variables to set for the deploy workflow."
  value = {
    AWS_REGION         = var.region
    ECR_REPOSITORY     = aws_ecr_repository.backend.name
    ECS_CLUSTER        = aws_ecs_cluster.main.name
    ECS_SERVICE        = aws_ecs_service.backend.name
    ECS_TASK_FAMILY    = aws_ecs_task_definition.backend.family
    FRONTEND_BUCKET    = aws_s3_bucket.frontend.bucket
    CLOUDFRONT_DIST_ID = aws_cloudfront_distribution.main.id
  }
}
