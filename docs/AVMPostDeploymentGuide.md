# AVM Post Deployment Guide

> **📋 Note**: This guide is specifically for post-deployment steps after using the AVM template. For complete deployment from scratch, see the main [Deployment Guide](./DEPLOYMENT.md).

---

This document provides guidance on post-deployment steps after deploying the Content Generation solution accelerator from the [AVM (Azure Verified Modules) repository](https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/sa/content-generation).

## Overview

After successfully deploying the Content Generation Solution Accelerator using the AVM template, you'll need to complete some configuration steps to make the solution fully operational. The AVM deployment provisions all required Azure resources, and the post-deployment process will upload sample data, create search indexes, and verify the application is ready to use.

---

## Prerequisites

Before starting the post-deployment process, ensure you have the following:

### 1. Azure Subscription & Permissions

You need access to an [Azure subscription](https://azure.microsoft.com/free/) with permissions to:
- Create resource groups and resources
- Create app registrations
- Assign roles at the resource group level (Contributor + RBAC)

📖 Follow the steps in [Azure Account Set Up](./AzureAccountSetUp.md) for detailed instructions.

### 2. Deployed Infrastructure

A successful Content Generation solution accelerator deployment from the [AVM repository](https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/sa/content-generation).

The deployment should have created the following resources:
- Azure App Service (frontend web app)
- Azure Container Instance (backend API)
- Azure AI Foundry (AI orchestration)
- Azure OpenAI Service (GPT and Image models)
- Azure Cosmos DB (product catalog and conversations)
- Azure Blob Storage (product images and generated images)
- Azure AI Search (product search index)
- User Assigned Managed Identity
- App Service Plan

**Optional resources** (depending on deployment parameters):
- Log Analytics Workspace and Application Insights (if monitoring is enabled)
- Virtual Network, Private DNS Zones, and Private Endpoints (if private networking is enabled)
- Azure Bastion and Jumpbox VM (if enabled for private network administration)

**Important:** The deployment references an **existing Azure Container Registry** (specified via the `acrName` parameter) that must contain pre-built container images (`content-gen-app` and `content-gen-api`). The ACR is not created by this deployment.

### 3. Required Tools

Ensure the following tools are installed on your machine:

| Tool | Version | Download Link |
|------|---------|---------------|
| PowerShell | v7.0+ | [Install PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.5) |
| Azure CLI | v2.50+ | [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) |
| Python | 3.11+ | [Download Python](https://www.python.org/downloads/) |
| Git | Latest | [Download Git](https://git-scm.com/downloads) |

#### Important Note for PowerShell Users

If you encounter issues running PowerShell scripts due to execution policy restrictions, you can temporarily adjust the `ExecutionPolicy` by running the following command in an elevated PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This will allow the scripts to run for the current session without permanently changing your system's policy.

---

## Post-Deployment Steps

### Step 1: Clone the Repository

Clone this repository to access the post-deployment scripts and sample data:

```powershell
git clone https://github.com/microsoft/content-generation-solution-accelerator.git
cd content-generation-solution-accelerator
```

---

### Step 2: Run the Post-Deployment Script

The AVM deployment provisions the Azure infrastructure but does NOT include automated post-deployment hooks. You need to manually run the post-deployment script to upload sample data and create search indexes.

> **📝 Note**: Unlike `azd up` deployments which run post-deployment hooks automatically via `azure.yaml`, AVM deployments require manual execution of the post-deployment script.

#### 2.1 Login to Azure

```shell
az login
```

> 💡 **Tip**: If using VS Code Web or environments without browser access, use device code authentication:
> ```shell
> az login --use-device-code
> ```

#### 2.2 Set Up Environment

Navigate to the repository root directory and create a Python virtual environment:

**For Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ./scripts/requirements-post-deploy.txt
```

**For Linux/Mac (bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ./scripts/requirements-post-deploy.txt
```

#### 2.3 Execute the Post-Deployment Script

Run the post-deployment script with your resource group name. The script will automatically retrieve resource names from the Azure deployment outputs.

**For Windows (PowerShell):**
```powershell
python ./scripts/post_deploy.py -g <your-resource-group-name> --skip-tests
```

**For Linux/Mac (bash):**
```bash
python3 ./scripts/post_deploy.py -g <your-resource-group-name> --skip-tests
```

**Example:**
```powershell
python ./scripts/post_deploy.py -g rg-contentgen-prod --skip-tests
```

> ⚠️ **Important**: The script uses Azure CLI authentication and will automatically discover resource names from deployment outputs. Ensure you're logged in with `az login` before running.

**How it works:**
- The script queries the deployment outputs using the resource group name
- It automatically retrieves App Service, Storage Account, Cosmos DB, and AI Search names
- No need to manually specify individual resource names

**Alternative:** If you prefer to specify resources explicitly, you can use environment variables or command-line arguments:
```powershell
# Using environment variables
$env:RESOURCE_GROUP_NAME = "rg-contentgen-prod"
$env:APP_SERVICE_NAME = "app-contentgen-abc123"
$env:AZURE_BLOB_ACCOUNT_NAME = "stcontentgenabc123"
$env:COSMOSDB_ACCOUNT_NAME = "cosmos-contentgen-abc123"
$env:AI_SEARCH_SERVICE_NAME = "search-contentgen-abc123"
python ./scripts/post_deploy.py --skip-tests
```

The script will:
- Upload sample product data to Cosmos DB
- Upload sample product images to Blob Storage
- Create and populate the Azure AI Search index
- Verify all connections and configurations

---

### Step 3: Access the Application

1. Navigate to the [Azure Portal](https://portal.azure.com)
2. Open the **resource group** created during deployment
3. Locate the **App Service** (name typically starts with `app-contentgen-`)
4. Copy the **URL** from the Overview page (format: `https://app-contentgen-<unique-id>.azurewebsites.net`)
5. Open the URL in your browser to access the application

> 📝 **Note**: It may take a few minutes for the App Service to start up after deployment.

---

### Step 4: Configure Authentication (Optional)

If you want to enable authentication for your application, follow the [App Authentication Guide](./AppAuthentication.md).

> **⚠️ Important**: Authentication changes can take up to 10 minutes to propagate.

---

### Step 5: Verify Data Processing

Confirm your deployment is working correctly:

| Check | Location | How to Verify |
|-------|----------|---------------|
| ✅ Sample data uploaded | Azure Cosmos DB | Navigate to Cosmos DB → Data Explorer → Check `products` and `conversations` containers |
| ✅ Sample images uploaded | Azure Blob Storage | Navigate to Storage Account → Containers → Check `product-images` container |
| ✅ AI Search index created | Azure AI Search | Navigate to AI Search → Indexes → Verify `products-index` exists and has documents |
| ✅ Application loads | App Service URL | Open the web app URL and verify the welcome screen appears |

---

## Getting Started

To learn how to use the Content Generation solution and try sample workflows, see the [Sample Workflow](./DEPLOYMENT.md#sample-workflow) section in the main Deployment Guide.

---

## Clean Up Resources

If you need to delete the resources after testing or a failed deployment:

Follow the steps in [Delete Resource Group](./DeleteResourceGroup.md) to clean up all deployed resources.

> ⚠️ **Warning**: Deleting the resource group will permanently delete all resources and data. This action cannot be undone.