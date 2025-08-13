# VCT Dashboard Deployment Guide

Complete guide for deploying the VCT Dashboard using Docker, Heroku, and AWS infrastructure.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git
- AWS CLI (for AWS deployment)
- Heroku CLI (for Heroku deployment)

### Local Development
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/VCT-Dashboard.git
cd VCT-Dashboard

# Install dependencies
pip install -r requirements.txt

# Import CSV data to SQLite
python scripts/import_to_sqlite.py

# Run the application
streamlit run app.py
```

## 📊 Database Setup

### SQLite Database Import
The application uses SQLite for better performance and easier deployment:

```bash
# Import all CSV data to SQLite database
python scripts/import_to_sqlite.py

# Verify database structure
python scripts/verify_database.py

# Import large files (if needed)
python scripts/import_large_files.py
```

**Database Features:**
- 📁 Imports from `data/` directory and all `vct_*` subfolders
- 🔄 Automatic schema inference and data type detection
- 📊 111+ tables with 364,810+ rows of VCT data
- 📈 Optimized indexes for fast queries
- 🛡️ Error handling for encoding and format issues

## 🐳 Docker Deployment

### Local Docker
```bash
# Build and run with Docker
docker build -t vct-dashboard .
docker run -p 8501:8501 vct-dashboard

# Or use Docker Compose
docker-compose up --build

# Run with database admin interface
docker-compose --profile admin up
```

### Docker Configuration
- **Image**: Python 3.11 slim for security and size
- **Port**: 8501 (Streamlit default)
- **Health Check**: Built-in health monitoring
- **Security**: Non-root user for container security
- **Persistence**: Volume mounting for database

## ☁️ Heroku Deployment

### One-Click Deploy
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Manual Heroku Deployment
```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-vct-dashboard

# Set stack to container
heroku stack:set container -a your-vct-dashboard

# Deploy
git push heroku main

# Open the app
heroku open -a your-vct-dashboard
```

### Heroku Configuration
- **Stack**: Container (Docker-based)
- **Dyno**: Basic tier recommended
- **Environment**: Configured via `app.json`
- **Buildpack**: Container (uses Dockerfile)

## 🚀 GitHub Actions CI/CD

### Automated Deployment Pipeline
The repository includes a complete CI/CD pipeline:

```yaml
# .github/workflows/deploy.yml features:
✅ Automated testing and database verification
🐳 Multi-platform Docker image builds
📦 Docker Hub image publishing
🚀 Automatic Heroku deployment
🔐 Security scanning with Trivy
☁️ Optional AWS ECS deployment
```

### Required GitHub Secrets
```bash
# Docker Hub
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password

# Heroku
HEROKU_API_KEY=your-heroku-api-key
HEROKU_EMAIL=your-email@example.com

# AWS (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### Workflow Triggers
- **Push to main**: Full deployment pipeline
- **Push to develop**: Build and test only
- **Pull requests**: Testing and validation
- **Manual**: On-demand deployment

## ☁️ AWS ECS Deployment

### Terraform Infrastructure
Complete AWS infrastructure as code:

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure
terraform apply

# View outputs
terraform output
```

### AWS Architecture
```
Internet Gateway
       ↓
Application Load Balancer (Public Subnets)
       ↓
ECS Fargate Tasks (Private Subnets)
       ↓
EFS/RDS Database (Optional)
```

### AWS Components
- **VPC**: Isolated network with public/private subnets
- **ALB**: Load balancer with health checks
- **ECS Fargate**: Serverless container hosting
- **ECR**: Private Docker image registry
- **EFS**: Persistent file storage for SQLite
- **CloudWatch**: Monitoring and logging
- **IAM**: Secure role-based access

### Terraform Variables
```hcl
# terraform/terraform.tfvars
aws_region = "us-east-1"
environment = "production"
desired_count = 2
cpu = 512
memory = 1024
use_efs = true
enable_alb_logs = true
certificate_arn = "arn:aws:acm:..."  # For HTTPS
domain_name = "vct.yourcompany.com"
zone_id = "Z123456789"  # Route 53 zone
```

### EFS vs RDS Options
```bash
# SQLite with EFS (recommended)
use_efs = true
use_rds = false

# PostgreSQL with RDS (enterprise)
use_efs = false
use_rds = true
db_instance_class = "db.t3.small"
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required
PYTHONPATH=/app
STREAMLIT_SERVER_HEADLESS=true

# Optional
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
STREAMLIT_SERVER_ENABLE_CORS=false
```

### Database Configuration
```python
# utils.py - Database settings
DB_PATH = "vct.db"          # SQLite database path
CONNECTION_TIMEOUT = 30      # Connection timeout
QUERY_CACHE_TTL = 300       # Cache time-to-live
```

## 🔍 Monitoring and Maintenance

### Health Checks
- **Application**: `/_stcore/health` endpoint
- **Docker**: Built-in health check
- **AWS**: ALB target group health checks
- **Database**: Connection and query validation

### Logging
```bash
# Docker logs
docker logs vct-dashboard

# Heroku logs
heroku logs --tail -a your-vct-dashboard

# AWS CloudWatch
aws logs tail /ecs/vct-dashboard --follow
```

### Database Maintenance
```bash
# Backup database
cp vct.db vct.db.backup

# Re-import fresh data
python scripts/import_to_sqlite.py

# Verify database integrity
python scripts/verify_database.py
```

## 🔐 Security Considerations

### Container Security
- ✅ Non-root user in container
- ✅ Minimal base image (Python slim)
- ✅ Security scanning in CI/CD
- ✅ No secrets in Docker images

### Network Security
- 🔒 Private subnets for application
- 🛡️ Security groups with minimal access
- 🔐 HTTPS/TLS encryption (optional)
- 🚪 ALB as single entry point

### Data Security
- 📊 SQLite database with proper permissions
- 🔄 EFS encryption at rest and in transit
- 🗂️ Backup and recovery procedures
- 📋 Access logging and monitoring

## 🐛 Troubleshooting

### Common Issues

**Database not found:**
```bash
# Run the import script
python scripts/import_to_sqlite.py

# Check file permissions
ls -la vct.db
```

**Docker build fails:**
```bash
# Check Docker daemon
docker info

# Clean build cache
docker builder prune

# Build with no cache
docker build --no-cache -t vct-dashboard .
```

**Heroku deployment fails:**
```bash
# Check app logs
heroku logs --tail -a your-app-name

# Restart dynos
heroku restart -a your-app-name

# Check dyno status
heroku ps -a your-app-name
```

**AWS deployment issues:**
```bash
# Check ECS service events
aws ecs describe-services --cluster vct-dashboard-cluster \
  --services vct-dashboard-service

# View task logs
aws logs tail /ecs/vct-dashboard --follow

# Check ALB health
aws elbv2 describe-target-health --target-group-arn <TARGET_GROUP_ARN>
```

### Performance Optimization
- 🚀 Enable Streamlit caching (`@st.cache_data`)
- 📊 Use database queries instead of loading full tables
- 🔄 Implement connection pooling
- 📈 Add database indexes for frequent queries
- 🎯 Optimize Docker image layers

## 📚 Additional Resources

### Documentation
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Heroku Container Registry](https://devcenter.heroku.com/articles/container-registry-and-runtime)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Monitoring Tools
- **Heroku Metrics**: Built-in monitoring
- **AWS CloudWatch**: Comprehensive monitoring
- **Docker Stats**: Container resource usage
- **Streamlit Analytics**: User interaction tracking

### Cost Optimization
- **Heroku**: Use Eco dynos for development
- **AWS**: Use Fargate Spot for non-critical workloads
- **Docker**: Multi-stage builds for smaller images
- **Database**: Regular cleanup and optimization

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

The CI/CD pipeline will automatically test and deploy your changes!

---

**📧 Support**: Create an issue on GitHub for questions or problems.
**🔄 Updates**: Watch the repository for updates and new features.
**⭐ Star**: If you find this useful, please star the repository!
