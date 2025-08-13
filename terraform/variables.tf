# Variables for VCT Dashboard AWS Infrastructure

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

# ECS Configuration
variable "cpu" {
  description = "Number of CPU units for the task"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Amount of memory (in MiB) for the task"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of instances of the task"
  type        = number
  default     = 2
}

# Storage Configuration
variable "use_efs" {
  description = "Whether to use EFS for database persistence"
  type        = bool
  default     = true
}

variable "use_rds" {
  description = "Whether to use RDS instead of SQLite"
  type        = bool
  default     = false
}

# Load Balancer Configuration
variable "enable_deletion_protection" {
  description = "Enable deletion protection for the load balancer"
  type        = bool
  default     = true
}

variable "enable_alb_logs" {
  description = "Enable access logs for the load balancer"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
  default     = ""
}

# Database Configuration (RDS)
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (GB)"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "vctadmin"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  default     = ""
  sensitive   = true
}

# Auto Scaling Configuration
variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "target_memory_utilization" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable enhanced monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Backup Configuration
variable "backup_retention_period" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Database backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Database maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}
