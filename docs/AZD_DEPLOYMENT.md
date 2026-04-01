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
  - Deploy Azure AI Services (GPT-5.1, GPT-Image-1-mini)
  - Create Container Registry, Container Instances, App Service
  - Create Cosmos DB, Storage Account, AI Search
  - Assign RBAC roles

- **Quota**: Ensure you have sufficient quota for:
  - GPT-5.1 (or your chosen model)
  - GPT-Image-1-mini (or GPT-Image-1.5 - for image generation)

## Quick Start

### 1. Authenticate

```bash
# Login to Azure
azd auth login

# Login to Azure CLI (required for some post-deployment scripts)
az login
```
 Alternatively, login to Azure using a device code (recommended when using VS Code Web):

```
az login --use-device-code
```

### 2. Initialize Environment

```bash

# Create a new environment
azd env new <environment-name>

# Example:
azd env new content-gen-dev
```

### 3. Choose Deployment Configuration

The [`infra`](../infra) folder contains the [`main.bicep`](../infra/main.bicep) Bicep script, which defines all Azure infrastructure components for this solution.

By default, the `azd up` command uses the [`main.parameters.json`](../infra/main.parameters.json) file to deploy the solution. This file is pre-configured for a **sandbox environment**.

For **production deployments**, the repository also provides [`main.waf.parameters.json`](../infra/main.waf.parameters.json), which applies a [Well-Architected Framework (WAF) aligned](https://learn.microsoft.com/en-us/azure/well-architected/) configuration. This can be used for Production scenarios.

**How to choose your deployment configuration:**

* **To use sandbox/dev environment** — Use the default `main.parameters.json` file.

* **To use production configuration:**

Before running `azd up`, copy the contents from the production configuration file to your main parameters file:

1. Navigate to the `infra` folder in your project.
2. Open `main.waf.parameters.json` in a text editor (like Notepad, VS Code, etc.).
3. Select all content (Ctrl+A) and copy it (Ctrl+C).
4. Open `main.parameters.json` in the same text editor.
5. Select all existing content (Ctrl+A) and paste the copied content (Ctrl+V).
6. Save the file (Ctrl+S).

### 4. Deploy

**NOTE:** If you are running the latest azd version (version 1.23.9), please run the following command. 
```bash 
azd config set provision.preflight off
```

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

## Using Existing Resources

### Reuse Existing AI Foundry Project

```bash
# Set the resource ID of your existing AI Project
azd env set AZURE_EXISTING_AI_PROJECT_RESOURCE_ID "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project-name>"
```

### Reuse Existing Log Analytics Workspace

```bash
# Set the resource ID of your existing Log Analytics workspace
azd env set AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>"
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
azd env set AZURE_ENV_OPENAI_LOCATION eastus
```

#### 3. Container Build Fails

```
Error: az acr build failed
```

**Solution**: Check the Dockerfile and ensure all required files are present:
```bash
# Manual build for debugging
cd src/app
docker build -f WebApp.Dockerfile -t content-gen-app:test .
```

#### 4. Frontend Deployment Fails

```
Error: az webapp deploy failed
```

**Solution**: Ensure the frontend builds successfully:
```bash
cd src/app
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
│  └──────────────────┘      │  (GPT-5.1, GPT-Image-1-mini) │   │
│                            └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Image Generation Configuration](IMAGE_GENERATION.md)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
