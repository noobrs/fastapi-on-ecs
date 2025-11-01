# PowerShell Deployment Script for FastAPI on ECS
# This replaces the Makefile for Windows users

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('setup-ecr', 'deploy-container', 'deploy-service', 'destroy-service', 'update')]
    [string]$Command
)

# Load environment variables from .env file
function Load-EnvFile {
    if (Test-Path ".env") {
        Get-Content .env | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "Loaded: $name" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "Error: .env file not found. Please create it from .env.example" -ForegroundColor Red
        exit 1
    }
}

# Check prerequisites
function Check-Prerequisites {
    $tools = @('aws', 'docker', 'terraform')
    $missing = @()
    
    foreach ($tool in $tools) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            $missing += $tool
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "Error: Missing required tools: $($missing -join ', ')" -ForegroundColor Red
        Write-Host "Please install them before proceeding." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✓ All prerequisites installed" -ForegroundColor Green
}

# Set environment variables
function Set-EnvVariables {
    if (-not $env:AWS_ACCOUNT_ID -or -not $env:AWS_REGION) {
        Write-Host "Error: AWS_ACCOUNT_ID and AWS_REGION must be set in .env file" -ForegroundColor Red
        exit 1
    }
    
    $env:APP_NAME = "my-app-name"  # Change this to your app name
    $env:TAG = "latest"
    $env:TF_VAR_app_name = $env:APP_NAME
    $env:REGISTRY_NAME = $env:APP_NAME
    $env:TF_VAR_image = "$($env:AWS_ACCOUNT_ID).dkr.ecr.$($env:AWS_REGION).amazonaws.com/$($env:REGISTRY_NAME):$($env:TAG)"
    $env:TF_VAR_region = $env:AWS_REGION
    
    Write-Host "Environment variables set:" -ForegroundColor Cyan
    Write-Host "  APP_NAME: $env:APP_NAME"
    Write-Host "  AWS_REGION: $env:AWS_REGION"
    Write-Host "  IMAGE: $env:TF_VAR_image"
}

# Setup ECR
function Setup-ECR {
    Write-Host "`n=== Setting up ECR Repository ===" -ForegroundColor Cyan
    Push-Location infra/setup
    terraform init
    terraform apply -auto-approve
    Pop-Location
    Write-Host "✓ ECR repository created" -ForegroundColor Green
}

# Deploy Container
function Deploy-Container {
    Write-Host "`n=== Building and Pushing Docker Image ===" -ForegroundColor Cyan
    Push-Location app
    
    Write-Host "Logging in to ECR..." -ForegroundColor Yellow
    aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$($env:AWS_ACCOUNT_ID).dkr.ecr.$($env:AWS_REGION).amazonaws.com"
    
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build --no-cache --platform=linux/amd64 -t $env:REGISTRY_NAME .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "Tagging image..." -ForegroundColor Yellow
    docker tag "$($env:REGISTRY_NAME):$($env:TAG)" "$($env:AWS_ACCOUNT_ID).dkr.ecr.$($env:AWS_REGION).amazonaws.com/$($env:REGISTRY_NAME):$($env:TAG)"
    
    Write-Host "Pushing to ECR..." -ForegroundColor Yellow
    docker push "$($env:AWS_ACCOUNT_ID).dkr.ecr.$($env:AWS_REGION).amazonaws.com/$($env:REGISTRY_NAME):$($env:TAG)"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker push failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "✓ Docker image pushed to ECR" -ForegroundColor Green
}

# Deploy Service
function Deploy-Service {
    Write-Host "`n=== Deploying ECS Service ===" -ForegroundColor Cyan
    Push-Location infra/app
    terraform init
    terraform apply -auto-approve
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ ECS service deployed successfully!" -ForegroundColor Green
        Write-Host "`nYour application URL:" -ForegroundColor Cyan
        terraform output alb_dns_name
    } else {
        Write-Host "Error: Terraform apply failed" -ForegroundColor Red
    }
    
    Pop-Location
}

# Destroy Service
function Destroy-Service {
    Write-Host "`n=== Destroying ECS Service ===" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure you want to destroy the service? (yes/no)"
    
    if ($confirm -eq "yes") {
        Push-Location infra/app
        terraform init
        terraform destroy -auto-approve
        Pop-Location
        Write-Host "✓ ECS service destroyed" -ForegroundColor Green
    } else {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
    }
}

# Update deployment
function Update-Deployment {
    Write-Host "`n=== Updating Application ===" -ForegroundColor Cyan
    Deploy-Container
    
    Write-Host "Forcing ECS service update..." -ForegroundColor Yellow
    aws ecs update-service `
        --cluster "$($env:APP_NAME)-cluster" `
        --service "$($env:APP_NAME)-service" `
        --force-new-deployment `
        --region $env:AWS_REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Service update initiated" -ForegroundColor Green
        Write-Host "Note: It may take a few minutes for the new version to be deployed" -ForegroundColor Yellow
    } else {
        Write-Host "Error: Service update failed" -ForegroundColor Red
    }
}

# Main execution
Write-Host "FastAPI on ECS - Deployment Script" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

Check-Prerequisites
Load-EnvFile
Set-EnvVariables

switch ($Command) {
    'setup-ecr' { Setup-ECR }
    'deploy-container' { Deploy-Container }
    'deploy-service' { Deploy-Service }
    'destroy-service' { Destroy-Service }
    'update' { Update-Deployment }
}

Write-Host "`n=== Done ===" -ForegroundColor Green
