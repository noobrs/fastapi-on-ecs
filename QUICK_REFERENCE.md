# 🚀 Quick Deployment Reference

## Initial Setup (One Time)

```powershell
# 1. Run setup script
.\setup.ps1

# 2. Edit configuration files
notepad .env                    # Add AWS credentials
notepad app\.env.local          # Verify secrets
notepad deploy.ps1              # Set APP_NAME (line 50)

# 3. Create ECR repository
.\deploy.ps1 setup-ecr
```

## Deploy Application

```powershell
# Build and push Docker image
.\deploy.ps1 deploy-container

# Deploy to ECS
.\deploy.ps1 deploy-service
```

## Update Application

```powershell
# After making code changes
.\deploy.ps1 update
```

## Destroy (Stop Billing)

```powershell
# Remove ECS service
.\deploy.ps1 destroy-service
```

## Useful Commands

```powershell
# Get application URL
cd infra/app
terraform output alb_dns_name

# View ECS tasks
aws ecs list-tasks --cluster my-app-name-cluster --region $env:AWS_REGION

# Force redeploy
aws ecs update-service --cluster my-app-name-cluster --service my-app-name-service --force-new-deployment --region $env:AWS_REGION

# View logs
# Go to AWS Console → CloudWatch → Log Groups → /ecs/my-app-name-service
```

## Testing Endpoints

After deployment, your API will be at: `http://<alb-dns-name>`

```powershell
# Health check
curl http://<alb-dns-name>/api/py/health

# API documentation
# Open in browser: http://<alb-dns-name>/api/py/docs
```

## Troubleshooting

**Container won't start:**
- Check CloudWatch logs: AWS Console → CloudWatch → Log Groups
- Verify environment variables in app/.env.local
- Test Docker image locally: `docker run -p 8000:80 --env-file app/.env.local my-app-name`

**502 Bad Gateway:**
- Wait 2-3 minutes for container to fully start
- Check target group health in EC2 console
- Verify app is listening on port 80

**AWS credentials error:**
- Run: `aws sts get-caller-identity`
- Reconfigure: `aws configure`

## Cost Reminder

💰 Running on AWS costs ~$50-75/month

⚠️ **Always destroy when not in use:** `.\deploy.ps1 destroy-service`

## Files You Need

- ✅ `.env` - AWS credentials (in root)
- ✅ `app/.env.local` - Application secrets
- ✅ `deploy.ps1` - Modified with your APP_NAME
- ⚠️ `infra/setup/backend.tf` - Optional (for remote state)
- ⚠️ `infra/app/backend.tf` - Optional (for remote state)
