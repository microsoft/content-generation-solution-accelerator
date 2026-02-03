# Azure Developer CLI (azd) Deployment Guide

This guide covers deploying the Content Generation Solution Accelerator using Azure Developer CLI (`azd`).

## Prerequisites

### Required Tools

1. **Azure Developer CLI (azd)** v1.18.0 or higher
   ```bash
   # Install on Linux/macOS
   curl -fsSL https://aka.ms/install-azd.sh | bash
   
   # Install on Windows (PowerShell)
   powershell -ex AllSigned -c "Invoke-RestMethod 'https://aka.ms/install-azd.ps1' | Invoke-Expression"
   
   # Verify installation
   azd version
   ```

2. **Azure CLI**
   ```bash
   # Install: https://docs.microsoft.com/cli/azure/install-azure-cli
   az version
   ```

3. **Node.js** v18 or higher (for frontend build)
   ```bash
   node --version
   ```

4. **Python** 3.11+ (for post-deployment scripts)
   ```bash
   python3 --version
   ```

### Azure Requirements

- An Azure subscription with the following permissions:
  - Create Resource Groups
  - Deploy Azure AI Services (GPT-4o, DALL-E 3 or GPT-Image-1, Text Embeddings)
  - Create Container Registry, Container Instances, App Service
  - Create Cosmos DB, Storage Account, AI Search
  - Assign RBAC roles

- **Quota**: Ensure you have sufficient quota for:
  - GPT-4o (or your chosen model)
  - DALL-E 3 or GPT-Image-1 (for image generation)
  - Text-embedding-3-large

## Quick Start

### 1. Authenticate

```bash
# Login to Azure
azd auth login

# Login to Azure CLI (required for some post-deployment scripts)
az login
```

### 2. Initialize Environment

```bash
cd content-gen

# Create a new environment
azd env new <environment-name>

# Example:
azd env new content-gen-dev
```

### 3. Configure Parameters (Optional)

The deployment has sensible defaults, but you can customize:

```bash
# Set the Azure region (default: eastus)
azd env set AZURE_LOCATION swedencentral

# Set AI Services region (must support your models)
azd env set azureAiServiceLocation swedencentral

# GPT Model configuration
azd env set gptModelName gpt-4o
azd env set gptModelVersion 2024-11-20
azd env set gptModelDeploymentType GlobalStandard
azd env set gptModelCapacity 50

# Image generation model (dalle-3 or gpt-image-1)
azd env set imageModelChoice gpt-image-1
azd env set dalleModelCapacity 1

# Embedding model
azd env set embeddingModel text-embedding-3-large
azd env set embeddingDeploymentCapacity 50

# Azure OpenAI API version
azd env set azureOpenaiAPIVersion 2024-12-01-preview
```

### 4. Enable Optional Features (WAF Pillars)

```bash
# Enable private networking (VNet integration)
azd env set enablePrivateNetworking true

# Enable monitoring (Log Analytics + App Insights)
azd env set enableMonitoring true

# Enable scalability (auto-scaling, higher SKUs)
azd env set enableScalability true

# Enable redundancy (zone redundancy, geo-replication)
azd env set enableRedundancy true
```

### 5. Deploy

```bash
azd up
```

This single command will:
1. **Provision** all Azure resources (AI Services, Cosmos DB, Storage, AI Search, App Service, Container Registry)
2. **Build** the Docker container image and push to ACR
3. **Deploy** the container to Azure Container Instances
4. **Build** the frontend (React/TypeScript)
5. **Deploy** the frontend to App Service
6. **Configure** RBAC and Cosmos DB roles
7. **Upload** sample data and create the search index

## Deployment Parameters Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `AZURE_LOCATION` | eastus | Primary Azure region |
| `azureAiServiceLocation` | eastus | Region for AI Services (must support chosen models) |
| `gptModelName` | gpt-4o | GPT model for content generation |
| `gptModelVersion` | 2024-11-20 | Model version |
| `gptModelDeploymentType` | GlobalStandard | Deployment type |
| `gptModelCapacity` | 50 | TPM capacity (in thousands) |
| `imageModelChoice` | dalle-3 | Image model: `dalle-3` or `gpt-image-1` |
| `dalleModelCapacity` | 1 | Image model capacity |
| `embeddingModel` | text-embedding-3-large | Embedding model |
| `embeddingDeploymentCapacity` | 50 | Embedding TPM capacity |
| `enablePrivateNetworking` | false | Enable VNet and private endpoints |
| `enableMonitoring` | false | Enable Log Analytics + App Insights |
| `enableScalability` | false | Enable auto-scaling |
| `enableRedundancy` | false | Enable zone/geo redundancy |

## Using Existing Resources

### Reuse Existing AI Foundry Project

```bash
# Set the resource ID of your existing AI Project
azd env set azureExistingAIProjectResourceId "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project-name>"
```

### Reuse Existing Log Analytics Workspace

```bash
# Set the resource ID of your existing Log Analytics workspace
azd env set existingLogAnalyticsWorkspaceId "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>"
```

### Use Existing Container Registry

```bash
# Set the name of your existing ACR
azd env set acrName myexistingacr
```

## Post-Deployment

After `azd up` completes, you'll see output like:

```
===== Deployment Complete =====

Access the web application:
   https://app-<env-name>.azurewebsites.net
```

### Verify Deployment

1. Open the Web App URL in your browser
2. Sign in with your Azure AD account
3. Navigate to the Products page to verify sample data was loaded
4. Create a test marketing content document

### Access Resources

```bash
# View all environment values
azd env get-values

# Get the web app URL
azd env get-value WEB_APP_URL

# Get resource group name
azd env get-value RESOURCE_GROUP_NAME
```

## Day-2 Operations

### Update the Application

After making code changes:

```bash
# Rebuild and redeploy everything
azd up

# Or just redeploy (no infra changes)
azd deploy
```

### Update Only the Backend (Container)

```bash
# Get ACR and ACI names
ACR_NAME=$(azd env get-value ACR_NAME)
ACI_NAME=$(azd env get-value CONTAINER_INSTANCE_NAME)
RG_NAME=$(azd env get-value RESOURCE_GROUP_NAME)

# Build and push new image
az acr build --registry $ACR_NAME --image content-gen-app:latest --file ./src/WebApp.Dockerfile ./src

# Restart ACI to pull new image
az container restart --name $ACI_NAME --resource-group $RG_NAME
```

### Update Only the Frontend

```bash
cd src/app/frontend
npm install && npm run build

cd ../frontend-server
zip -r frontend-deploy.zip static/ server.js package.json package-lock.json

az webapp deploy \
  --resource-group $(azd env get-value RESOURCE_GROUP_NAME) \
  --name $(azd env get-value APP_SERVICE_NAME) \
  --src-path frontend-deploy.zip \
  --type zip
```

### View Logs

```bash
# Backend container logs
az container logs \
  --name $(azd env get-value CONTAINER_INSTANCE_NAME) \
  --resource-group $(azd env get-value RESOURCE_GROUP_NAME) \
  --follow

# App Service logs
az webapp log tail \
  --name $(azd env get-value APP_SERVICE_NAME) \
  --resource-group $(azd env get-value RESOURCE_GROUP_NAME)
```

## Clean Up

### Delete All Resources

```bash
# Delete all Azure resources and the environment
azd down --purge

# Or just delete resources (keep environment config)
azd down
```

### Delete Specific Environment

```bash
# List environments
azd env list

# Delete an environment
azd env delete <environment-name>
```

## Troubleshooting

### Common Issues

#### 1. Quota Exceeded

```
Error: InsufficientQuota
```

**Solution**: Check your quota in the Azure portal or run:
```bash
az cognitiveservices usage list --location <region>
```

Request a quota increase or choose a different region.

#### 2. Model Not Available in Region

```
Error: The model 'gpt-4o' is not available in region 'westeurope'
```

**Solution**: Set a different region for AI Services:
```bash
azd env set azureAiServiceLocation eastus
```

#### 3. Container Build Fails

```
Error: az acr build failed
```

**Solution**: Check the Dockerfile and ensure all required files are present:
```bash
# Manual build for debugging
cd src
docker build -f WebApp.Dockerfile -t content-gen-app:test .
```

#### 4. Frontend Deployment Fails

```
Error: az webapp deploy failed
```

**Solution**: Ensure the frontend builds successfully:
```bash
cd src/app/frontend
npm install
npm run build
```

#### 5. RBAC Assignment Fails

```
Error: Authorization failed
```

**Solution**: Ensure you have Owner or User Access Administrator role on the subscription.

### Debug Mode

For more verbose output:
```bash
azd up --debug
```

### Reset Environment

If deployment gets into a bad state:
```bash
# Re-run provisioning
azd provision
```

## Architecture Deployed

When `enablePrivateNetworking` is enabled:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Resource Group                      │
│                                                                  │
│  ┌──────────────────┐      ┌───────────────────────────────┐   │
│  │   App Service    │      │         Virtual Network        │   │
│  │  (Node.js Proxy) │──────│  ┌─────────────────────────┐  │   │
│  │                  │      │  │   Container Instance    │  │   │
│  └──────────────────┘      │  │   (Python Backend)      │  │   │
│          │                 │  └─────────────────────────┘  │   │
│          │                 │                                │   │
│  ┌───────▼──────────┐      │  ┌─────────────────────────┐  │   │
│  │  Azure AI Search │◄─────│──│   Private Endpoints     │  │   │
│  └──────────────────┘      │  └─────────────────────────┘  │   │
│          │                 └───────────────────────────────┘   │
│  ┌───────▼──────────┐                                          │
│  │    Cosmos DB     │                                          │
│  └──────────────────┘                                          │
│          │                                                      │
│  ┌───────▼──────────┐      ┌───────────────────────────────┐   │
│  │  Storage Account │      │      Azure AI Services        │   │
│  └──────────────────┘      │  (GPT-4o, DALL-E, Embeddings) │   │
│                            └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Related Documentation

- [Manual Deployment Guide](DEPLOYMENT.md)
- [Image Generation Configuration](IMAGE_GENERATION.md)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
