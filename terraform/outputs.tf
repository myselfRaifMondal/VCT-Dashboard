# Outputs for VCT Dashboard Infrastructure

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.app.id
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "efs_id" {
  description = "ID of the EFS file system"
  value       = var.use_efs ? aws_efs_file_system.database[0].id : null
}

output "efs_dns_name" {
  description = "DNS name of the EFS file system"
  value       = var.use_efs ? aws_efs_file_system.database[0].dns_name : null
}

output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "application_url" {
  description = "URL to access the application"
  value = var.certificate_arn != "" ? (
    var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_lb.main.dns_name}"
  ) : (
    var.domain_name != "" ? "http://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
  )
}

output "security_group_alb_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "security_group_ecs_tasks_id" {
  description = "ID of the ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "iam_role_ecs_task_execution_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "iam_role_ecs_task_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

# Deployment instructions
output "deployment_instructions" {
  description = "Instructions for deploying the application"
  value = <<-EOT
    
    🚀 VCT Dashboard Infrastructure Deployed Successfully!
    
    Application URL: ${var.certificate_arn != "" ? (var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_lb.main.dns_name}") : (var.domain_name != "" ? "http://${var.domain_name}" : "http://${aws_lb.main.dns_name}")}
    
    ECR Repository: ${aws_ecr_repository.app.repository_url}
    ECS Cluster: ${aws_ecs_cluster.main.name}
    ECS Service: ${aws_ecs_service.app.name}
    
    📋 Next Steps:
    1. Build and push your Docker image to ECR:
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app.repository_url}
       docker build -t ${aws_ecr_repository.app.name} .
       docker tag ${aws_ecr_repository.app.name}:latest ${aws_ecr_repository.app.repository_url}:latest
       docker push ${aws_ecr_repository.app.repository_url}:latest
    
    2. Update the ECS service to deploy the new image:
       aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --force-new-deployment
    
    3. Monitor deployment status:
       aws ecs describe-services --cluster ${aws_ecs_cluster.main.name} --services ${aws_ecs_service.app.name}
    
    📊 Monitoring:
    - CloudWatch Logs: /ecs/${local.name_prefix}
    - ECS Console: https://${var.aws_region}.console.aws.amazon.com/ecs/home?region=${var.aws_region}#/clusters/${aws_ecs_cluster.main.name}/services
    - ALB Console: https://${var.aws_region}.console.aws.amazon.com/ec2/home?region=${var.aws_region}#LoadBalancers:
    
  EOT
}
