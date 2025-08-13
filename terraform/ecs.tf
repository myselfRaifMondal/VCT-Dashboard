# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs.name
      }
    }
  }

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30

  tags = local.common_tags
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = local.name_prefix
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "commit-"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# EFS File System for database persistence
resource "aws_efs_file_system" "database" {
  count = var.use_efs ? 1 : 0

  creation_token   = "${local.name_prefix}-database"
  performance_mode = "generalPurpose"
  throughput_mode  = "provisioned"
  provisioned_throughput_in_mibps = 10

  encrypted = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-efs"
  })
}

# EFS Mount Targets
resource "aws_efs_mount_target" "database" {
  count = var.use_efs ? length(aws_subnet.private) : 0

  file_system_id  = aws_efs_file_system.database[0].id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs[0].id]
}

# EFS Security Group
resource "aws_security_group" "efs" {
  count = var.use_efs ? 1 : 0

  name_prefix = "${local.name_prefix}-efs-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for EFS"

  ingress {
    description     = "NFS from ECS"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-efs-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Additional policies for EFS access
resource "aws_iam_role_policy" "ecs_task_efs" {
  count = var.use_efs ? 1 : 0

  name = "${local.name_prefix}-efs-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite",
          "elasticfilesystem:ClientRootAccess"
        ]
        Resource = aws_efs_file_system.database[0].arn
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = local.name_prefix
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = local.name_prefix
      image = "${aws_ecr_repository.app.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8501
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "PYTHONPATH"
          value = "/app"
        },
        {
          name  = "STREAMLIT_SERVER_HEADLESS"
          value = "true"
        },
        {
          name  = "STREAMLIT_BROWSER_GATHER_USAGE_STATS"
          value = "false"
        }
      ]
      
      mountPoints = var.use_efs ? [
        {
          sourceVolume  = "database"
          containerPath = "/app/vct.db"
          readOnly      = false
        }
      ] : []
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:8501/_stcore/health || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      
      essential = true
    }
  ])

  dynamic "volume" {
    for_each = var.use_efs ? [1] : []
    content {
      name = "database"
      efs_volume_configuration {
        file_system_id     = aws_efs_file_system.database[0].id
        root_directory     = "/"
        transit_encryption = "ENABLED"
        authorization_config {
          access_point_id = aws_efs_access_point.database[0].id
          iam             = "ENABLED"
        }
      }
    }
  }

  tags = local.common_tags
}

# EFS Access Point
resource "aws_efs_access_point" "database" {
  count = var.use_efs ? 1 : 0

  file_system_id = aws_efs_file_system.database[0].id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/database"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = 755
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-access-point"
  })
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  platform_version = "1.4.0"

  network_configuration {
    security_groups = [aws_security_group.ecs_tasks.id]
    subnets         = aws_subnet.private[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = local.name_prefix
    container_port   = 8501
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  enable_execute_command = true

  depends_on = [
    aws_lb_listener.app,
    aws_iam_role_policy_attachment.ecs_task_execution
  ]

  tags = local.common_tags
}
