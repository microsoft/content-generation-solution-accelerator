# Local Development Guide

This guide covers running the Content Generation Solution Accelerator locally for development and testing.

## Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **Azure CLI** - For authentication and environment setup
- **Azure Developer CLI (azd)** - Optional, for automatic environment configuration

### Azure Resources

You need access to the following Azure resources (can use an existing deployment):

- Azure OpenAI with GPT and image generation models deployed
- Azure Cosmos DB account with database and containers
- Azure Blob Storage account
- Azure AI Search service (optional, for product search)

## Quick Start

### Linux/Mac

```bash
# First time setup
./scripts/local_dev.sh setup

# Start development servers
./scripts/local_dev.sh
```

### Windows PowerShell

```powershell
# First time setup
.\scripts\local_dev.ps1 -Command setup

# Start development servers
.\scripts\local_dev.ps1
```

## Environment Configuration

### Option 1: Generate from Azure Deployment

If you have an existing Azure deployment with `azd`:

```bash
./scripts/local_dev.sh env
```

### Option 2: Manual Configuration

1. Copy the environment template:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` with your Azure resource values (see [Environment Variables Reference](#environment-variables-reference) below)

## Development Commands

| Command | Description |
|---------|-------------|
| `setup` | Create virtual environment, install Python and Node.js dependencies |
| `env` | Generate `.env` file from Azure resources (uses azd if available) |
| `backend` | Start only the Python/Quart backend server (port 5000) |
| `frontend` | Start only the Vite frontend dev server (port 3000) |
| `all` | Start both backend and frontend in parallel (default) |
| `build` | Build frontend for production |
| `clean` | Remove cache files, node_modules, and build artifacts |

### Usage Examples

**Linux/Mac:**
```bash
# Full setup and start
./scripts/local_dev.sh setup
./scripts/local_dev.sh

# Start only backend (for API development)
./scripts/local_dev.sh backend

# Start only frontend (if backend is running elsewhere)
./scripts/local_dev.sh frontend

# Build for production
./scripts/local_dev.sh build

# Clean up
./scripts/local_dev.sh clean
```

**Windows PowerShell:**
```powershell
# Full setup and start
.\scripts\local_dev.ps1 -Command setup
.\scripts\local_dev.ps1

# Start only backend
.\scripts\local_dev.ps1 -Command backend

# Start only frontend
.\scripts\local_dev.ps1 -Command frontend
```

## Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5000 |
| Health Check | http://localhost:5000/api/health |

The frontend Vite dev server automatically proxies `/api/*` requests to the backend.

## Hot Reload

Both servers support hot reload:
- **Backend**: Uses Hypercorn with `--reload` flag
- **Frontend**: Uses Vite's built-in HMR (Hot Module Replacement)

Changes to source files will automatically trigger a reload.

---

## Environment Variables Reference

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Port for the Python backend API |
| `WORKERS` | `4` | Number of Hypercorn worker processes |
| `BACKEND_PORT` | `5000` | Alternative port variable for local dev scripts |
| `FRONTEND_PORT` | `3000` | Port for the Vite dev server |

### Azure Authentication

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_CLIENT_ID` | No | Azure AD application (client) ID for authentication |

### Azure OpenAI Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL (e.g., `https://your-resource.openai.azure.com/`) |
| `AZURE_OPENAI_GPT_MODEL` | Yes | GPT model deployment name (e.g., `gpt-4o`, `gpt-5.1`) |
| `AZURE_OPENAI_IMAGE_MODEL` | Yes | Image generation model (`dall-e-3` or `gpt-image-1`) |
| `AZURE_OPENAI_GPT_IMAGE_ENDPOINT` | No | Separate endpoint for gpt-image-1 (if different from main endpoint) |
| `AZURE_OPENAI_API_VERSION` | Yes | API version (e.g., `2024-06-01`) |
| `AZURE_OPENAI_PREVIEW_API_VERSION` | No | Preview API version for new features |
| `AZURE_OPENAI_TEMPERATURE` | No | Generation temperature (default: `0.7`) |
| `AZURE_OPENAI_MAX_TOKENS` | No | Max tokens for generation (default: `2000`) |

### Image Generation Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_IMAGE_SIZE` | `1024x1024` | Image dimensions |
| `AZURE_OPENAI_IMAGE_QUALITY` | `medium` | Image quality setting |

**DALL-E 3 Options:**
- Sizes: `1024x1024`, `1024x1792`, `1792x1024`
- Quality: `standard`, `hd`

**GPT-Image-1 Options:**
- Sizes: `1024x1024`, `1536x1024`, `1024x1536`, `auto`
- Quality: `low`, `medium`, `high`, `auto`

### Azure Cosmos DB

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_COSMOS_ENDPOINT` | Yes | Cosmos DB endpoint URL |
| `AZURE_COSMOS_DATABASE_NAME` | Yes | Database name (default: `content-generation`) |
| `AZURE_COSMOS_PRODUCTS_CONTAINER` | Yes | Products container name (default: `products`) |
| `AZURE_COSMOS_CONVERSATIONS_CONTAINER` | Yes | Conversations container name (default: `conversations`) |

### Azure Blob Storage

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_BLOB_ACCOUNT_NAME` | Yes | Storage account name |
| `AZURE_BLOB_PRODUCT_IMAGES_CONTAINER` | Yes | Container for product images (default: `product-images`) |
| `AZURE_BLOB_GENERATED_IMAGES_CONTAINER` | Yes | Container for AI-generated images (default: `generated-images`) |

### Azure AI Search

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_AI_SEARCH_ENDPOINT` | No | AI Search service endpoint URL |
| `AZURE_AI_SEARCH_PRODUCTS_INDEX` | No | Product search index name (default: `products`) |
| `AZURE_AI_SEARCH_IMAGE_INDEX` | No | Image search index name (default: `product-images`) |

### UI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UI_APP_NAME` | `Content Generation Accelerator` | Application name shown in UI |
| `UI_TITLE` | `Content Generation` | Browser tab title |
| `UI_CHAT_TITLE` | `Marketing Content Generator` | Chat interface title |
| `UI_CHAT_DESCRIPTION` | AI-powered multimodal content generation... | Chat interface description |

### Brand Guidelines

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAND_TONE` | `Professional yet approachable` | Brand voice tone |
| `BRAND_VOICE` | `Innovative, trustworthy, customer-focused` | Brand voice characteristics |
| `BRAND_PRIMARY_COLOR` | `#0078D4` | Primary brand color (hex) |
| `BRAND_SECONDARY_COLOR` | `#107C10` | Secondary brand color (hex) |
| `BRAND_IMAGE_STYLE` | `Modern, clean, minimalist...` | Image generation style guidance |
| `BRAND_MAX_HEADLINE_LENGTH` | `60` | Maximum headline character length |
| `BRAND_MAX_BODY_LENGTH` | `500` | Maximum body text character length |
| `BRAND_REQUIRE_CTA` | `true` | Require call-to-action in content |
| `BRAND_PROHIBITED_WORDS` | `cheapest,guaranteed,...` | Comma-separated list of prohibited words |
| `BRAND_REQUIRED_DISCLOSURES` | `` | Comma-separated required legal disclosures |

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_ENABLED` | `false` | Enable Azure AD authentication |
| `SANITIZE_ANSWER` | `false` | Sanitize AI responses for safety |

---

## Example .env File

```dotenv
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://my-openai.openai.azure.com/
AZURE_OPENAI_GPT_MODEL=gpt-4o
AZURE_OPENAI_IMAGE_MODEL=gpt-image-1
AZURE_OPENAI_GPT_IMAGE_ENDPOINT=https://my-openai.openai.azure.com
AZURE_OPENAI_IMAGE_SIZE=1024x1024
AZURE_OPENAI_IMAGE_QUALITY=medium
AZURE_OPENAI_API_VERSION=2024-06-01

# Cosmos DB
AZURE_COSMOS_ENDPOINT=https://my-cosmos.documents.azure.com:443/
AZURE_COSMOS_DATABASE_NAME=content-generation
AZURE_COSMOS_PRODUCTS_CONTAINER=products
AZURE_COSMOS_CONVERSATIONS_CONTAINER=conversations

# Blob Storage
AZURE_BLOB_ACCOUNT_NAME=mystorageaccount
AZURE_BLOB_PRODUCT_IMAGES_CONTAINER=product-images
AZURE_BLOB_GENERATED_IMAGES_CONTAINER=generated-images

# AI Search (optional)
AZURE_AI_SEARCH_ENDPOINT=https://my-search.search.windows.net
AZURE_AI_SEARCH_PRODUCTS_INDEX=products

# UI
UI_APP_NAME=Content Generation Accelerator
UI_TITLE=Content Generation

# Brand
BRAND_TONE=Professional yet approachable
BRAND_VOICE=Innovative, trustworthy, customer-focused
BRAND_PRIMARY_COLOR=#0078D4
BRAND_PROHIBITED_WORDS=cheapest,guaranteed,best in class

# Server
PORT=5000
AUTH_ENABLED=false
```

---

## Utility Scripts

### Data Scripts

| Script | Description |
|--------|-------------|
| `load_sample_data.py` | Load sample products into Cosmos DB and images into Blob Storage |
| `index_products.py` | Create and populate Azure AI Search index with product data |
| `upload_images.py` | Upload images from local directory to Blob Storage |
| `create_image_search_index.py` | Create image search index for visual similarity |

**Usage:**
```bash
# Load sample data
python scripts/load_sample_data.py

# Create search index
python scripts/index_products.py

# Upload images
python scripts/upload_images.py --source ./images --container product-images
```

### Testing Scripts

| Script | Description |
|--------|-------------|
| `test_content_generation.py` | End-to-end test for content generation pipeline |

**Usage:**
```bash
python scripts/test_content_generation.py
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find and kill the process
lsof -i :5000
kill -9 <PID>

# Or use a different port
BACKEND_PORT=8000 ./scripts/local_dev.sh backend
```

### Virtual Environment Issues

```bash
# Remove and recreate
rm -rf .venv
./scripts/local_dev.sh setup
```

### Node Modules Issues

```bash
# Clean and reinstall
./scripts/local_dev.sh clean
./scripts/local_dev.sh setup
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

Ensure your user has the "Cosmos DB Data Contributor" role:
```bash
az cosmosdb sql role assignment create \
  --resource-group <rg> \
  --account-name <cosmos-account> \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id $(az ad signed-in-user show --query id -o tsv) \
  --scope "/"
```

### Storage Access Denied

Ensure your user has the "Storage Blob Data Contributor" role:
```bash
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee $(az ad signed-in-user show --query userPrincipalName -o tsv) \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>
```

---

## Related Documentation

- [AZD Deployment Guide](AZD_DEPLOYMENT.md) - Deploy to Azure with `azd up`
- [Manual Deployment Guide](DEPLOYMENT.md) - Step-by-step Azure deployment
- [Image Generation Configuration](IMAGE_GENERATION.md) - DALL-E 3 and GPT-Image-1 setup
