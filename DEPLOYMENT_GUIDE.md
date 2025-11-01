# AWS Deployment Guide for FastAPI on ECS

## Prerequisites

✅ **Already Completed:**
- ECR setup attempted (you ran `make setup-ecr`)
- Environment variables configured in `.env.local.example`

## ⚠️ Windows Setup Issue

The `make` command doesn't work natively on Windows PowerShell. You have **3 options**:

### Option 1: Use WSL (Recommended)
```bash
# Open WSL
wsl

# Navigate to your project
cd /mnt/d/fastapi-on-ecs

# Follow the deployment steps below
```

### Option 2: Install Make for Windows
```powershell
# Install via Chocolatey
choco install make

# Or download from: http://gnuwin32.sourceforge.net/packages/make.htm
```

### Option 3: Run Commands Manually (What I'll show below)

---

## 📋 Step-by-Step Deployment Process

### Step 1: Set Up Environment Variables

First, create your `.env` file from the example:

```powershell
# In the root directory
Copy-Item .env.example .env
```

Edit `.env` with your actual AWS credentials:
```env
AWS_ACCOUNT_ID=your-actual-account-id
AWS_REGION=your-preferred-region  # e.g., us-east-1, ap-southeast-1
```

**Get your AWS Account ID:**
```powershell
aws sts get-caller-identity --query Account --output text
```

### Step 2: Copy Application Environment Variables

```powershell
# In the app directory
cd app
Copy-Item .env.local.example .env.local
```

Edit `app/.env.local` and update:
- `RESUME_PIPELINE_HMAC_SECRET` - Use a strong random string
- `RESUME_PIPELINE_WEBHOOK_URL` - Your production webhook URL
- Ensure Supabase credentials are correct

**Generate a secure HMAC secret:**
```powershell
# PowerShell command to generate random secret
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

### Step 3: Create Terraform Backend (Optional but Recommended)

Create `infra/setup/backend.tf`:
```hcl
terraform {
  backend "s3" {
    region = "your-region"
    bucket = "your-terraform-state-bucket"
    key    = "fastapi-on-ecs-setup/terraform.tfstate"
  }
}
```

Create `infra/app/backend.tf`:
```hcl
terraform {
  backend "s3" {
    region = "your-region"
    bucket = "your-terraform-state-bucket"
    key    = "fastapi-on-ecs-app/terraform.tfstate"
  }
}
```

**Note:** If you skip this, Terraform will store state locally (not recommended for production).

---

## 🚀 Deployment Commands (Manual Execution)

### Step 1: Set Environment Variables for PowerShell Session

```powershell
# Load .env file into PowerShell session
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Set additional variables
$env:APP_NAME = "my-app-name"  # Change this to your app name
$env:TAG = "latest"
$env:TF_VAR_app_name = $env:APP_NAME
$env:REGISTRY_NAME = $env:APP_NAME
$env:TF_VAR_image = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/${env:REGISTRY_NAME}:${env:TAG}"
$env:TF_VAR_region = $env:AWS_REGION
```

### Step 2: Create ECR Repository

```powershell
cd infra/setup
terraform init
terraform apply -auto-approve
cd ../..
```

**What this does:** Creates an ECR (Elastic Container Registry) repository to store your Docker images.

### Step 3: Build and Push Docker Image

```powershell
cd app

# Login to ECR
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"

# Build the Docker image
docker build --no-cache --platform=linux/amd64 -t ${env:REGISTRY_NAME} .

# Tag the image
docker tag "${env:REGISTRY_NAME}:${env:TAG}" "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/${env:REGISTRY_NAME}:${env:TAG}"

# Push to ECR
docker push "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/${env:REGISTRY_NAME}:${env:TAG}"

cd ..
```

**What this does:** 
- Builds your Docker image with all dependencies
- Pushes it to AWS ECR so ECS can use it

### Step 4: Deploy ECS Infrastructure

```powershell
cd infra/app
terraform init
terraform apply -auto-approve
cd ../..
```

**What this does:**
- Creates VPC and networking infrastructure
- Sets up Application Load Balancer (ALB)
- Creates ECS cluster and service
- Deploys your container on Fargate

### Step 5: Get Your Application URL

After deployment completes, Terraform will output your ALB DNS name:

```powershell
cd infra/app
terraform output alb_dns_name
```

Your API will be available at: `http://<alb-dns-name>`

Test it:
- Health check: `http://<alb-dns-name>/api/py/health`
- API docs: `http://<alb-dns-name>/api/py/docs`

---

## 🔄 Updating Your Application

When you make code changes:

```powershell
# Set environment variables (if not already set)
# ... (same as Step 1 above)

# Navigate to app directory
cd app

# Login to ECR
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"

# Build and push new image
docker build --no-cache --platform=linux/amd64 -t ${env:REGISTRY_NAME} .
docker tag "${env:REGISTRY_NAME}:${env:TAG}" "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/${env:REGISTRY_NAME}:${env:TAG}"
docker push "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/${env:REGISTRY_NAME}:${env:TAG}"

# Force ECS to redeploy (optional - ECS will eventually pull new image)
aws ecs update-service --cluster ${env:APP_NAME}-cluster --service ${env:APP_NAME}-service --force-new-deployment --region $env:AWS_REGION

cd ..
```

---

## 🛑 Destroying Infrastructure (Important!)

**⚠️ Always destroy resources when not in use to avoid AWS charges!**

```powershell
# Destroy the ECS service and infrastructure
cd infra/app
terraform destroy -auto-approve
cd ../..

# Optionally destroy ECR (only if you want to delete everything)
cd infra/setup
terraform destroy -auto-approve
cd ../..
```

---

## 📊 Monitoring and Troubleshooting

### View ECS Logs

```powershell
# Get task ARN
aws ecs list-tasks --cluster ${env:APP_NAME}-cluster --region $env:AWS_REGION

# View logs (replace TASK_ID)
aws ecs describe-tasks --cluster ${env:APP_NAME}-cluster --tasks <TASK_ARN> --region $env:AWS_REGION
```

### Check CloudWatch Logs

Your application logs are in CloudWatch under:
- Log Group: `/ecs/${APP_NAME}-service`

### Common Issues

1. **Container fails to start:**
   - Check CloudWatch logs
   - Verify environment variables in task definition
   - Ensure Docker image built successfully

2. **502 Bad Gateway:**
   - Container may not be healthy yet
   - Check health check endpoint is responding
   - Verify port 80 is exposed and app is listening

3. **Timeout errors:**
   - Increase health check timeout in ECS task definition
   - Check security group rules

---

## 💰 Cost Estimation

Typical costs for running this setup:

- **ECS Fargate:** ~$30-50/month (0.25 vCPU, 0.5 GB RAM, always on)
- **Application Load Balancer:** ~$16-20/month
- **Data Transfer:** Variable based on usage
- **ECR Storage:** ~$0.10/GB/month

**Total:** ~$50-75/month for a small production deployment

**💡 Cost Saving Tips:**
- Use AWS Free Tier if eligible (12 months)
- Stop the service when not in use: `terraform destroy`
- Use smaller Fargate task sizes if possible
- Enable auto-scaling to scale to zero during off-hours

---

## 🔐 Security Considerations

Before going to production:

1. **Use HTTPS:** Set up ACM certificate and configure ALB listener
2. **Environment Variables:** Store secrets in AWS Secrets Manager or SSM Parameter Store
3. **IAM Roles:** Use least-privilege IAM roles for ECS tasks
4. **Network Security:** Review security group rules
5. **Enable WAF:** Consider AWS WAF for the ALB
6. **VPC Endpoints:** Use VPC endpoints for ECR to avoid data transfer costs

---

## 🎯 Quick Reference Commands

```powershell
# Check AWS credentials
aws sts get-caller-identity

# List ECR repositories
aws ecr describe-repositories --region $env:AWS_REGION

# List ECS clusters
aws ecs list-clusters --region $env:AWS_REGION

# Get ALB DNS name
cd infra/app
terraform output alb_dns_name

# Force new deployment
aws ecs update-service --cluster ${env:APP_NAME}-cluster --service ${env:APP_NAME}-service --force-new-deployment --region $env:AWS_REGION
```

---

## ✅ Deployment Checklist

- [ ] AWS CLI installed and configured
- [ ] Docker Desktop running
- [ ] `.env` file created with AWS credentials
- [ ] `app/.env.local` file created with app secrets
- [ ] Supabase `resumes-redacted` bucket exists
- [ ] Terraform installed
- [ ] ECR repository created
- [ ] Docker image built and pushed
- [ ] ECS infrastructure deployed
- [ ] Application tested via ALB URL
- [ ] Monitoring set up in CloudWatch
- [ ] Cost alerts configured in AWS Billing

---

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
