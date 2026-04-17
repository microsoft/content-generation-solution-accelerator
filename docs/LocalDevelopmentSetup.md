# Local Development Setup Guide

This guide provides comprehensive instructions for setting up the Content Generation Solution Accelerator for local development across Windows and Linux platforms.

## Important Setup Notes

### Multi-Service Architecture

This application consists of **two separate services** that run in parallel:

1. **Backend API**: Python/Quart server providing content generation and orchestration APIs
2. **Frontend**: React/Vite-based user interface

> **💡 Note:** The local development script (`local_dev.ps1` / `local_dev.sh`) manages both services automatically. When running individually, each service requires its own terminal window.

### Path Conventions

**All paths in this guide are relative to the repository root directory:**

```bash
content-generation-solution-accelerator/    ← Repository root (start here)
├── scripts/
│   ├── local_dev.ps1               ← Local dev script (Windows)
│   └── local_dev.sh                ← Local dev script (Linux/Mac)
├── src/
│   ├── backend/
│   │   ├── app.py                  ← API entry point
│   │   └── requirements.txt        ← Python dependencies
│   └── app/
│       └── frontend/
│           └── package.json        ← Node.js dependencies
├── .env.sample                     ← Template for environment variables
├── .env                            ← Your local config file
└── docs/                           ← Documentation (you are here)
```

## Step 1: Prerequisites - Install Required Tools

### Windows Development

#### Option 1: Native Windows (PowerShell)

```powershell
# Install Git
winget install Git.Git

# Install Node.js for frontend
winget install OpenJS.NodeJS.LTS

# Install Python 3.11+
winget install Python.Python.3.12

# Install Azure CLI and Azure Developer CLI
winget install Microsoft.AzureCLI
winget install Microsoft.Azd
```

#### Option 2: Windows with WSL2 (Recommended)

```bash
# Install WSL2 first (run in PowerShell as Administrator):
# wsl --install -d Ubuntu

# Then in WSL2 Ubuntu terminal:
sudo apt update && sudo apt install git curl python3.11 python3.11-venv -y

# Install Node.js 20+ from NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash
```

### Linux Development

#### Ubuntu/Debian

```bash
# Install prerequisites
sudo apt update && sudo apt install git curl python3.11 python3.11-venv -y

# Install Node.js 20+ from NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash
```

### Verify Installations

```bash
python3 --version    # or python --version on Windows
node --version
git --version
az --version
azd version
```

### Clone the Repository

```bash
git clone https://github.com/microsoft/content-generation-solution-accelerator.git
cd content-generation-solution-accelerator
```

## Step 2: Development Tools Setup

### Visual Studio Code (Recommended)

#### Required Extensions

Create `.vscode/extensions.json` in the workspace root and copy the following JSON:

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.pylint",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-vscode-remote.remote-wsl",
        "ms-vscode-remote.remote-containers",
        "redhat.vscode-yaml",
        "ms-vscode.azure-account",
        "ms-python.mypy-type-checker"
    ]
}
```

VS Code will prompt you to install these recommended extensions when you open the workspace.

#### Settings Configuration

Create `.vscode/settings.json` and copy the following JSON:

```json
{
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.associations": {
        "*.yaml": "yaml",
        "*.yml": "yaml"
    }
}
```

## Step 3: Azure Infrastructure Deployment & Authentication

Before running the application locally, you need to deploy the Azure infrastructure. Follow the [AZD Deployment Guide](AZD_DEPLOYMENT.md) to deploy using `azd up`.

### Azure Authentication

After deployment, ensure you are authenticated with Azure CLI:

```bash
# Login to Azure CLI
az login

# Set your subscription
az account set --subscription "your-subscription-id"

# Verify authentication
az account show
```

## Step 4: Start Development Servers

### Option A: Complete Automated Run

Start everything with a single command:

**Windows PowerShell:**
```powershell
.\scripts\local_dev.ps1
```

**Linux/Mac:**
```bash
chmod +x ./scripts/local_dev.sh   # First time only: grant execute permission
./scripts/local_dev.sh
```

The script automatically handles environment setup, dependency installation, Azure authentication, role assignments, and starts both the backend (port 5000) and frontend (port 3000).

> **Note:** RBAC changes can take 5-10 minutes to propagate. If you get "Forbidden" errors, wait and retry.

### Option B: Run Each Step Individually

If you prefer more control over the setup process, follow the steps below to configure and run each service individually.

> **Linux/Mac:** If you haven't already, run `chmod +x ./scripts/local_dev.sh` first to grant execute permission.

#### 1. Generate Environment Configuration

```powershell
.\scripts\local_dev.ps1 -Command env        # Windows PowerShell
./scripts/local_dev.sh env                  # Linux/Mac
```

This runs `azd env get-values` and writes the output to a `.env` file in the repository root.

> **Alternative: Manual Configuration**
>
> If you don't have `azd` or prefer manual setup:
> 1. Copy the sample file:
>    ```bash
>    cp .env.sample .env        # Linux/macOS
>    Copy-Item .env.sample .env  # Windows PowerShell
>    ```
> 2. Get the environment variable values from the Azure Portal:
>    - Navigate to your **Resource Group** in the Azure Portal
>    - Open the **Azure Container Instance (ACI)** resource
>    - Go to **Containers** → select the container → **Properties**
>    - Copy the environment variable values from the **Environment variables** section into your `.env` file
>
> See [Environment Variables Reference](#environment-variables-reference) for details on each variable.

#### 2. Install Dependencies

```powershell
.\scripts\local_dev.ps1 -Command setup      # Windows PowerShell
./scripts/local_dev.sh setup                # Linux/Mac
```

Creates a Python virtual environment (`.venv`), installs backend Python packages, and installs frontend Node.js packages.

#### 3. Start Backend

```powershell
.\scripts\local_dev.ps1 -Command backend    # Windows PowerShell
./scripts/local_dev.sh backend              # Linux/Mac
```

#### 4. Start Frontend (in a separate terminal)

```powershell
.\scripts\local_dev.ps1 -Command frontend   # Windows PowerShell
./scripts/local_dev.sh frontend             # Linux/Mac
```

---

## Step 5: Verify Services Are Running

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5000 |
| Health Check | http://localhost:5000/api/health |

Open http://localhost:3000 in your browser - you should see the Content Generation Accelerator UI.

Both servers support **hot reload** - changes to source files trigger automatic reload.

## Step 6: Additional Commands

### Clean Up Artifacts

Removes Python caches, `node_modules`, and build artifacts:

```powershell
.\scripts\local_dev.ps1 -Command clean      # Windows PowerShell
./scripts/local_dev.sh clean                # Linux/Mac
```

### Show Help

```powershell
.\scripts\local_dev.ps1 -Command help       # Windows PowerShell
./scripts/local_dev.sh help                 # Linux/Mac
```

---

## Environment Variables Reference

The `.env` file is loaded from the repository root. It is **auto-generated** when you run the main script if missing, or you can generate it manually using the `env` command. You can also create it manually from `.env.sample`.

### Azure OpenAI Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_ENV_GPT_MODEL_NAME` | Yes | GPT model deployment name (e.g., `gpt-5.1`) |
| `AZURE_ENV_IMAGE_MODEL_NAME` | Yes | Image generation model (e.g., `gpt-image-1-mini`) |
| `AZURE_OPENAI_GPT_IMAGE_ENDPOINT` | No | Separate endpoint for image generation (if different from main endpoint) |
| `AZURE_ENV_OPENAI_API_VERSION` | Yes | API version (e.g., `2024-06-01`) |

### Azure AI Foundry Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `USE_FOUNDRY` | Yes | Set to `true` to use Azure AI Foundry (default deployment uses Foundry) |
| `AZURE_AI_PROJECT_ENDPOINT` | Yes | AI Foundry project endpoint URL |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Yes | GPT model deployment name in Foundry |
| `AZURE_AI_IMAGE_MODEL_DEPLOYMENT` | Yes | Image model deployment name in Foundry |
| `AI_FOUNDRY_RESOURCE_ID` | Yes | Resource ID of the AI Foundry account (used for role assignments) |
| `AZURE_EXISTING_AIPROJECT_RESOURCE_ID` | No | Resource ID of an existing AI project (used for role assignments if set) |

### Azure Cosmos DB

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_COSMOS_ENDPOINT` | Yes | Cosmos DB endpoint URL |
| `AZURE_COSMOS_DATABASE_NAME` | Yes | Database name |
| `AZURE_COSMOS_PRODUCTS_CONTAINER` | Yes | Products container name |
| `AZURE_COSMOS_CONVERSATIONS_CONTAINER` | Yes | Conversations container name |
| `COSMOSDB_ACCOUNT_NAME` | Yes | Cosmos DB account name (used for role assignments) |

### Azure Blob Storage

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_BLOB_ACCOUNT_NAME` | Yes | Storage account name |
| `AZURE_BLOB_PRODUCT_IMAGES_CONTAINER` | Yes | Container for product images |
| `AZURE_BLOB_GENERATED_IMAGES_CONTAINER` | Yes | Container for AI-generated images |

### Azure AI Search

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_AI_SEARCH_ENDPOINT` | Yes | AI Search service endpoint URL |
| `AZURE_AI_SEARCH_PRODUCTS_INDEX` | Yes | Product search index name |
| `AZURE_AI_SEARCH_IMAGE_INDEX` | Yes | Image search index name |

### Application Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_CLIENT_ID` | Yes | Azure AD application (client) ID |
| `PORT` | No | Backend API port (default: `5000` locally, `8000` in ACI) |
| `WORKERS` | No | Number of Hypercorn worker processes (default: `4`) |
| `RESOURCE_GROUP_NAME` | Yes | Azure resource group name (used for role assignments) |

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -tulpn | grep :5000          # Linux
lsof -i :5000                        # macOS
netstat -ano | findstr :5000         # Windows PowerShell

# Kill the process if needed (use PID from above command)
kill -9 <PID>                        # Linux/macOS
Stop-Process -Id <PID>              # Windows PowerShell

# Or use a different port
BACKEND_PORT=8000 ./scripts/local_dev.sh backend                           # Linux/Mac
$env:BACKEND_PORT=8000; .\scripts\local_dev.ps1 -Command backend          # Windows PowerShell
```

### Virtual Environment Issues

- If `python` command is not found, try `python3` or `py -3.12`
- On Windows, if venv activation fails, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

```bash
rm -rf .venv                                          # Linux/macOS
Remove-Item -Recurse -Force .venv                     # Windows PowerShell

# Then re-run setup
./scripts/local_dev.sh setup                          # Linux/Mac
.\scripts\local_dev.ps1 -Command setup                # Windows PowerShell
```

### Node Modules Issues

```bash
./scripts/local_dev.sh clean && ./scripts/local_dev.sh setup              # Linux/Mac
.\scripts\local_dev.ps1 -Command clean; .\scripts\local_dev.ps1 -Command setup   # Windows PowerShell
```

### Azure Authentication

```bash
# Re-authenticate
az login
az account set --subscription <subscription-id>

# Verify authentication
az account show
```

### Cosmos DB Access Denied

The local dev script assigns the Cosmos DB Data Contributor role automatically. If you still encounter issues, add manually:

```bash
# Linux/macOS
az cosmosdb sql role assignment create \
  --resource-group <rg> \
  --account-name <cosmos-account> \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id $(az ad signed-in-user show --query id -o tsv) \
  --scope "/"
```

```powershell
# Windows PowerShell
az cosmosdb sql role assignment create `
  --resource-group <rg> `
  --account-name <cosmos-account> `
  --role-definition-id "00000000-0000-0000-0000-000000000002" `
  --principal-id (az ad signed-in-user show --query id -o tsv) `
  --scope "/"
```

### Storage Access Denied

The local dev script assigns the Storage Blob Data Contributor role automatically. If you still encounter issues, add manually:

```bash
# Linux/macOS
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee $(az ad signed-in-user show --query userPrincipalName -o tsv) \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>
```

```powershell
# Windows PowerShell
az role assignment create `
  --role "Storage Blob Data Contributor" `
  --assignee (az ad signed-in-user show --query userPrincipalName -o tsv) `
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>"
```

### Azure AI User Access Denied

The local dev script assigns the Azure AI User role automatically. If you still encounter issues, add manually:

```bash
# Linux/macOS
az role assignment create \
  --role "Azure AI User" \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<ai-foundry-account>
```

```powershell
# Windows PowerShell
az role assignment create `
  --role "Azure AI User" `
  --assignee (az ad signed-in-user show --query id -o tsv) `
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<ai-foundry-account>"
```

### Missing Environment Variables

If the `env` command fails or produces an incomplete `.env`, ensure:
1. You have run `azd up` successfully
2. Your `azd` environment is set correctly: `azd env list`
3. You can manually check values with: `azd env get-values`

---

## Related Documentation

- [AZD Deployment Guide](AZD_DEPLOYMENT.md): Deploy to Azure with `azd up`
- [Deploy Local Changes](AZD_DEPLOYMENT.md#advanced-deploy-local-changes): Deploy your local code modifications to Azure
- [Technical Guide](TECHNICAL_GUIDE.md): Architecture and technical details
- [Azure Account Setup](AzureAccountSetUp.md): Setting up your Azure account
- [Quota Check](QuotaCheck.md): Verify Azure resource quotas before deployment
