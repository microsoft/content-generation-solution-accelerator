# Intelligent Content Generation Accelerator

A multimodal content generation solution for retail marketing campaigns using Microsoft Agent Framework with HandoffBuilder orchestration. The system interprets creative briefs and generates compliant marketing content (text and images) grounded in enterprise product data, brand guidelines, and product images.

## Overview

This accelerator provides an internal chatbot that can:

- **Interpret Creative Briefs**: Parse free-text creative briefs into structured fields (overview, objectives, target audience, key message, tone/style, deliverable, timelines, visual guidelines, CTA)
- **Generate Multimodal Content**: Create marketing copy and images using GPT models and DALL-E 3
- **Ensure Brand Compliance**: Validate all content against brand guidelines with severity-categorized warnings
- **Ground in Enterprise Data**: Leverage product information, product images, and brand guidelines stored in Azure services

## Architecture

### Backend
- **Runtime**: Python 3.11 + Quart + Hypercorn
- **Deployment**: Azure Container Instance (ACI) in private VNet
- **Authentication**: System-assigned Managed Identity

### Frontend
- **Framework**: React + Vite + TypeScript + Fluent UI
- **Deployment**: Azure App Service with Node.js proxy
- **Features**: Server-Sent Events (SSE) for streaming responses

### Specialized Agents (Microsoft Agent Framework)

The solution uses **HandoffBuilder** orchestration with 6 specialized agents:

| Agent | Role |
|-------|------|
| **TriageAgent** | Coordinator that routes user requests to appropriate specialists |
| **PlanningAgent** | Parses creative briefs, develops content strategy, returns for user confirmation |
| **ResearchAgent** | Retrieves products from CosmosDB, fetches brand guidelines, assembles grounding data |
| **TextContentAgent** | Generates marketing copy (headlines, body, CTAs) using GPT |
| **ImageContentAgent** | Creates marketing images via DALL-E 3 with product context |
| **ComplianceAgent** | Validates content against brand guidelines, categorizes violations |

### Compliance Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Error** | Legal/regulatory violations | Blocks acceptance until modified |
| **Warning** | Brand guideline deviations | Review recommended |
| **Info** | Style suggestions | Optional improvements |

### Azure Services

| Service | Purpose |
|---------|---------|
| Azure OpenAI (GPT) | Text generation and content creation |
| Azure OpenAI (DALL-E 3) | Image generation (can be separate resource) |
| Azure Cosmos DB | Products catalog, chat conversations |
| Azure Blob Storage | Product images, generated images |
| Azure Container Instance | Backend API hosting |
| Azure App Service | Frontend hosting |
| Azure Container Registry | Container image storage |

## Creative Brief Fields

The system extracts the following fields from free-text creative briefs:

1. **Overview** - Campaign summary
2. **Objectives** - Goals and KPIs
3. **Target Audience** - Demographics and psychographics
4. **Key Message** - Core messaging
5. **Tone and Style** - Voice and manner
6. **Deliverable** - Expected outputs
7. **Timelines** - Due dates and milestones
8. **Visual Guidelines** - Image requirements
9. **CTA** - Call to action

## Product Schema

```json
{
  "product_name": "string",
  "category": "string",
  "sub_category": "string",
  "marketing_description": "string",
  "detailed_spec_description": "string",
  "sku": "string",
  "model": "string",
  "image_description": "string (auto-generated via GPT-5 vision)",
  "image_url": "string"
}
```

## Getting Started

### Prerequisites

- Azure subscription with access to:
  - Azure OpenAI (GPT model - GPT-4 or higher recommended)
  - Azure OpenAI (DALL-E 3 - can be same or different resource)
  - Azure Cosmos DB
  - Azure Blob Storage
  - Azure Container Instance
  - Azure App Service
  - Azure Container Registry
- Azure CLI >= 2.50.0
- Docker (optional - ACR can build containers)
- Python 3.11+
- Node.js 18+

### Quick Deployment (Recommended)

Using Azure Developer CLI (`azd`):

```bash
# Clone the repository
git clone <repository-url>
cd content-gen

# Deploy everything with one command
azd up
```

See [docs/AZD_DEPLOYMENT.md](docs/AZD_DEPLOYMENT.md) for detailed `azd` deployment instructions.

### Manual Deployment

For more control over individual resources:

```bash
# Clone the repository
git clone <repository-url>
cd content-gen

# Run deployment script
./scripts/deploy.sh
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed manual deployment instructions.

### Local Development

```bash
# Backend
cd src
pip install -r requirements.txt
python app.py

# Frontend
cd src/app/frontend
npm install
npm run dev
```

## Configuration

### Environment Variables

See `src/backend/settings.py` for all configuration options. Key settings:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint for GPT model |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT model deployment name |
| `AZURE_OPENAI_DALLE_ENDPOINT` | Azure OpenAI endpoint for DALL-E (if separate) |
| `AZURE_OPENAI_DALLE_DEPLOYMENT` | DALL-E deployment name (dall-e-3) |
| `COSMOS_ENDPOINT` | Azure Cosmos DB endpoint |
| `COSMOS_DATABASE` | Cosmos DB database name |
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage account name |
| `BRAND_*` | Brand guideline parameters |

### Brand Guidelines

Brand guidelines are configured via environment variables with the `BRAND_` prefix:

```env
BRAND_TONE=Professional yet approachable
BRAND_VOICE=Innovative, trustworthy, customer-focused
BRAND_PROHIBITED_WORDS=guarantee,best,only,exclusive
BRAND_REQUIRED_DISCLOSURES=Terms apply,See details
BRAND_PRIMARY_COLOR=#0078D4
BRAND_SECONDARY_COLOR=#107C10
```

## Documentation

- [Local Development Guide](docs/LOCAL_DEPLOYMENT.md) - Run locally for development
- [AZD Deployment Guide](docs/AZD_DEPLOYMENT.md) - Deploy with Azure Developer CLI
- [Manual Deployment Guide](docs/DEPLOYMENT.md) - Step-by-step manual deployment
- [Image Generation Configuration](docs/IMAGE_GENERATION.md) - DALL-E 3 and GPT-Image-1 setup
- [API Reference](docs/API.md)

## License

MIT License - See [LICENSE](LICENSE) for details.
