# How to use this Repo
## Warning
- Always make sure to destroy your API Service. Forgetting to do so could incur a large AWS fee
- Never commit your AWS Account ID to git. Save it in an `.env` file and ensure `.env` is added to your `.gitignore`

## Setup, Deploy, and Destroy

### Setup Env Variables
Add an `.env` file containing your AWS account ID and region. Example file:
```
AWS_ACCOUNT_ID=1234567890
AWS_REGION=ap-southeast-1
```

Create a `backend.tf` file and add it to both `/infra/setup/backend.tf` and `/infra/app/backend.tf`. Example files:
```
terraform {
  backend "s3" {
    region = "<AWS_REGION>"
    bucket = "<BUCKET_NAME>"
    key    = "<APP_NAME>/terraform.tfstate"
  }
}
```
```
terraform {
  backend "s3" {
    region = "<AWS_REGION>"
    bucket = "<BUCKET_NAME>"
    key    = "<APP_NAME>/terraform.tfstate"
  }
}
```
Alternatively you can skip this step to store your Terraform state locally.

<br>

### Setup, Deploy, and Destroy Infrastructure/App

#### For Windows PowerShell Users:

1. **Quick Setup** (First time only)
    ```powershell
    .\setup.ps1
    ```
    This will create your configuration files and check prerequisites.

2. **Edit Configuration**
    - Update `.env` with your AWS credentials
    - Update `app/.env.local` with your secrets
    - Edit `deploy.ps1` line 50 to set your APP_NAME

3. **Deploy to AWS**
    ```powershell
    # Setup ECR Repository (one time)
    .\deploy.ps1 setup-ecr
    
    # Build and push Docker image
    .\deploy.ps1 deploy-container
    
    # Deploy ECS service
    .\deploy.ps1 deploy-service
    ```

4. **Update your application** (after code changes)
    ```powershell
    .\deploy.ps1 update
    ```

5. **Destroy your API Service**
    ```powershell
    .\deploy.ps1 destroy-service
    ```

#### For Linux/Mac/WSL Users (Makefile):

1. Setup your ECR Repository (one time)
    ```bash
    make setup-ecr
    ```

2. Build and deploy your container
    ```bash
    make deploy-container
    ```

3. Deploy your API Service on ECS Fargate
    ```bash
    make deploy-service
    ```

4. Destroy your API Service on ECS Fargate
    ```bash
    make destroy-service
    ```

**Note:** The URL for your endpoint will be printed by Terraform once deployment is complete. Example: `alb_dns_name = "<APP_NAME>-alb-123456789.<AWS_REGION>.elb.amazonaws.com"`. Navigate to that URL in your browser to ensure the API is working. You can also check out the API docs at the `<URL>/api/py/docs` endpoint.

**See DEPLOYMENT_GUIDE.md for detailed instructions and troubleshooting.**

