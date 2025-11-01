# Quick Setup Script for FastAPI on ECS
# Run this first before deploying

Write-Host "FastAPI on ECS - Quick Setup" -ForegroundColor Cyan
Write-Host "============================`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env and add your AWS credentials" -ForegroundColor Yellow
    $needsEdit = $true
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Check if app/.env.local exists
if (-not (Test-Path "app/.env.local")) {
    Write-Host "Creating app/.env.local file from template..." -ForegroundColor Yellow
    Copy-Item app/.env.local.example app/.env.local
    Write-Host "✓ Created app/.env.local file" -ForegroundColor Green
    Write-Host "⚠️  Please review app/.env.local and update if needed" -ForegroundColor Yellow
    $needsEdit = $true
} else {
    Write-Host "✓ app/.env.local file already exists" -ForegroundColor Green
}

# Get AWS Account ID
Write-Host "`nChecking AWS credentials..." -ForegroundColor Cyan
$awsAccountId = aws sts get-caller-identity --query Account --output text 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ AWS CLI configured" -ForegroundColor Green
    Write-Host "  Account ID: $awsAccountId" -ForegroundColor White
    
    # Update .env with actual account ID if it has the placeholder
    $envContent = Get-Content .env
    if ($envContent -match "123456789012") {
        Write-Host "Updating .env with your AWS Account ID..." -ForegroundColor Yellow
        (Get-Content .env) -replace "123456789012", $awsAccountId | Set-Content .env
        Write-Host "✓ Updated .env with your AWS Account ID" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  AWS CLI not configured or credentials not set" -ForegroundColor Yellow
    Write-Host "   Run: aws configure" -ForegroundColor White
}

# Check Docker
Write-Host "`nChecking Docker..." -ForegroundColor Cyan
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Docker not found. Please install Docker Desktop" -ForegroundColor Yellow
}

# Check Terraform
Write-Host "`nChecking Terraform..." -ForegroundColor Cyan
$tfVersion = terraform --version 2>$null | Select-Object -First 1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Terraform installed: $tfVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Terraform not found. Please install Terraform" -ForegroundColor Yellow
}

# Summary
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

if ($needsEdit) {
    Write-Host "`n⚠️  ACTION REQUIRED:" -ForegroundColor Yellow
    Write-Host "   1. Edit .env and set your AWS credentials" -ForegroundColor White
    Write-Host "   2. Review app/.env.local and update secrets" -ForegroundColor White
    Write-Host "   3. Change APP_NAME in deploy.ps1 (line 50)" -ForegroundColor White
} else {
    Write-Host "`n✓ Configuration files exist" -ForegroundColor Green
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Review and edit configuration files" -ForegroundColor White
Write-Host "  2. Run: .\deploy.ps1 setup-ecr" -ForegroundColor White
Write-Host "  3. Run: .\deploy.ps1 deploy-container" -ForegroundColor White
Write-Host "  4. Run: .\deploy.ps1 deploy-service" -ForegroundColor White

Write-Host "`nFor detailed instructions, see DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host "`n================================`n" -ForegroundColor Cyan
