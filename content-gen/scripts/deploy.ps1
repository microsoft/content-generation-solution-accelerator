# PowerShell deployment script for Content Generation Solution Accelerator
#
# This solution uses Microsoft Agent Framework with HandoffBuilder orchestration
# for multi-agent content generation workflows.

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Content Generation Solution Accelerator" -ForegroundColor Cyan
Write-Host "Deployment Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$azCli = Get-Command az -ErrorAction SilentlyContinue
if (-not $azCli) {
    Write-Host "Error: Azure CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

$dockerCli = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCli) {
    Write-Host "Warning: Docker is not installed. Container builds will need to be done in ACR." -ForegroundColor Yellow
}

# Check Azure login
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
try {
    az account show | Out-Null
} catch {
    Write-Host "Not logged in to Azure. Running 'az login'..." -ForegroundColor Yellow
    az login
}

# Get current directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

# Configuration from environment or prompt
$ResourceGroup = if ($env:RESOURCE_GROUP) { $env:RESOURCE_GROUP } else { $null }
$Location = if ($env:LOCATION) { $env:LOCATION } else { "eastus" }
$AcrName = if ($env:ACR_NAME) { $env:ACR_NAME } else { $null }
$ContainerName = if ($env:CONTAINER_NAME) { $env:CONTAINER_NAME } else { "aci-contentgen-backend" }
$AppServiceName = if ($env:APP_SERVICE_NAME) { $env:APP_SERVICE_NAME } else { $null }
$ImageTag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "latest" }

Write-Host ""
Write-Host "Current configuration:"
Write-Host "  Resource Group: $($ResourceGroup ?? '<not set>')"
Write-Host "  Location: $Location"
Write-Host "  ACR Name: $($AcrName ?? '<not set>')"
Write-Host "  Container Name: $ContainerName"
Write-Host "  App Service: $($AppServiceName ?? '<not set>')"
Write-Host "  Image Tag: $ImageTag"
Write-Host ""

# Prompt for missing values
if (-not $ResourceGroup) {
    $ResourceGroup = Read-Host "Enter Resource Group name"
}

if (-not $AcrName) {
    $AcrName = Read-Host "Enter Azure Container Registry name"
}

if (-not $AppServiceName) {
    $AppServiceName = Read-Host "Enter App Service name"
}

Write-Host ""
Write-Host "This deployment will:" -ForegroundColor Yellow
Write-Host "  1. Build and push the backend container to ACR"
Write-Host "  2. Update the Azure Container Instance"
Write-Host "  3. Build and deploy the frontend to App Service"
Write-Host "  4. Configure RBAC roles for managed identity"
Write-Host ""
Write-Host "Required Azure resources (should already exist):" -ForegroundColor Yellow
Write-Host "  - Azure Container Registry (ACR)"
Write-Host "  - Azure Container Instance (ACI) in VNet"
Write-Host "  - Azure App Service (frontend)"
Write-Host "  - Azure Cosmos DB (products, conversations containers)"
Write-Host "  - Azure Blob Storage (product-images, generated-images containers)"
Write-Host "  - Azure OpenAI (GPT model for text generation)"
Write-Host "  - Azure OpenAI (DALL-E 3 for image generation - can be separate resource)"
Write-Host ""

$continue = Read-Host "Continue with deployment? (y/n)"

if ($continue -eq "y" -or $continue -eq "Y") {
    
    # Step 1: Build and push container
    Write-Host ""
    Write-Host "Step 1: Building and pushing backend container..." -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    Set-Location "$ProjectDir\src"
    
    # Login to ACR
    az acr login --name $AcrName
    
    # Build and push using ACR tasks
    az acr build `
        --registry $AcrName `
        --image "contentgen-backend:$ImageTag" `
        --file WebApp.Dockerfile `
        .
    
    Write-Host "✓ Container built and pushed to $AcrName.azurecr.io/contentgen-backend:$ImageTag" -ForegroundColor Green
    
    # Step 2: Update ACI
    Write-Host ""
    Write-Host "Step 2: Updating Azure Container Instance..." -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    try {
        $currentIP = az container show -g $ResourceGroup -n $ContainerName --query "ipAddress.ip" -o tsv 2>$null
        if ($currentIP) {
            Write-Host "Current container IP: $currentIP"
            Write-Host "Restarting container with new image..."
            az container restart -g $ResourceGroup -n $ContainerName
        }
    } catch {
        Write-Host "Warning: Container $ContainerName not found. You may need to create it manually." -ForegroundColor Yellow
    }
    
    # Step 3: Build and deploy frontend
    Write-Host ""
    Write-Host "Step 3: Building and deploying frontend..." -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    Set-Location "$ProjectDir\src\frontend"
    npm install
    npm run build
    
    # Copy built files to server directory
    Copy-Item -Path "$ProjectDir\src\static\*" -Destination "$ProjectDir\src\frontend-server\static\" -Recurse -Force
    
    Set-Location "$ProjectDir\src\frontend-server"
    
    # Create deployment package
    if (Test-Path "frontend-deploy.zip") {
        Remove-Item "frontend-deploy.zip"
    }
    Compress-Archive -Path "static", "server.js", "package.json", "package-lock.json" -DestinationPath "frontend-deploy.zip"
    
    # Deploy to App Service
    az webapp deploy `
        --resource-group $ResourceGroup `
        --name $AppServiceName `
        --src-path "frontend-deploy.zip" `
        --type zip
    
    Write-Host "✓ Frontend deployed to $AppServiceName" -ForegroundColor Green
    
    # Step 4: Get managed identity and show RBAC requirements
    Write-Host ""
    Write-Host "Step 4: RBAC Configuration" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    try {
        $principalId = az container show -g $ResourceGroup -n $ContainerName --query "identity.principalId" -o tsv 2>$null
        
        if ($principalId) {
            Write-Host "Container Managed Identity Principal ID: $principalId" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Required RBAC role assignments for the managed identity:" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "1. Azure OpenAI (GPT model):" -ForegroundColor Cyan
            Write-Host "   Role: Cognitive Services OpenAI User"
            Write-Host "   az role assignment create --assignee $principalId ``"
            Write-Host "     --role 'Cognitive Services OpenAI User' ``"
            Write-Host "     --scope <GPT_RESOURCE_ID>"
            Write-Host ""
            Write-Host "2. Azure OpenAI (DALL-E model - if separate resource):" -ForegroundColor Cyan
            Write-Host "   Role: Cognitive Services OpenAI User"
            Write-Host "   az role assignment create --assignee $principalId ``"
            Write-Host "     --role 'Cognitive Services OpenAI User' ``"
            Write-Host "     --scope <DALLE_RESOURCE_ID>"
            Write-Host ""
            Write-Host "3. Azure Cosmos DB:" -ForegroundColor Cyan
            Write-Host "   Role: Cosmos DB Built-in Data Contributor (data plane)"
            Write-Host "   az cosmosdb sql role assignment create ``"
            Write-Host "     --account-name <COSMOS_ACCOUNT> ``"
            Write-Host "     --resource-group $ResourceGroup ``"
            Write-Host "     --scope '/' ``"
            Write-Host "     --principal-id $principalId ``"
            Write-Host "     --role-definition-id 00000000-0000-0000-0000-000000000002"
            Write-Host ""
            Write-Host "   Role: Cosmos DB Account Reader Role (for metadata)"
            Write-Host "   az role assignment create --assignee $principalId ``"
            Write-Host "     --role 'Cosmos DB Account Reader Role' ``"
            Write-Host "     --scope <COSMOS_RESOURCE_ID>"
            Write-Host ""
            Write-Host "4. Azure Blob Storage:" -ForegroundColor Cyan
            Write-Host "   Role: Storage Blob Data Contributor"
            Write-Host "   az role assignment create --assignee $principalId ``"
            Write-Host "     --role 'Storage Blob Data Contributor' ``"
            Write-Host "     --scope <STORAGE_RESOURCE_ID>"
        }
    } catch {
        Write-Host "Warning: Could not retrieve managed identity. Configure RBAC manually." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    
    # Get App Service URL
    try {
        $webappUrl = az webapp show -g $ResourceGroup -n $AppServiceName --query "defaultHostName" -o tsv 2>$null
        if ($webappUrl) {
            Write-Host ""
            Write-Host "Application URL: https://$webappUrl" -ForegroundColor Cyan
        }
    } catch {}
    
    Write-Host ""
    Write-Host "Post-deployment steps:" -ForegroundColor Yellow
    Write-Host "1. Verify RBAC roles are assigned (see above)"
    Write-Host "2. Upload product data: python scripts/load_sample_data.py"
    Write-Host "3. Test the application at the URL above"
    Write-Host ""
    
} else {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
}
