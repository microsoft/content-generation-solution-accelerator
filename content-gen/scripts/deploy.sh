#!/bin/bash
# Deployment script for Content Generation Solution Accelerator
# 
# This solution uses Microsoft Agent Framework with HandoffBuilder orchestration
# for multi-agent content generation workflows.

set -e

echo "============================================"
echo "Content Generation Solution Accelerator"
echo "Deployment Script"
echo "============================================"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed. Container builds will need to be done in ACR."
fi

# Check Azure login
echo "Checking Azure login status..."
az account show &> /dev/null || {
    echo "Not logged in to Azure. Running 'az login'..."
    az login
}

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Default configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-}"
CONTAINER_NAME="${CONTAINER_NAME:-aci-contentgen-backend}"
APP_SERVICE_NAME="${APP_SERVICE_NAME:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo ""
echo "Current configuration:"
echo "  Resource Group: ${RESOURCE_GROUP:-<not set>}"
echo "  Location: $LOCATION"
echo "  ACR Name: ${ACR_NAME:-<not set>}"
echo "  Container Name: $CONTAINER_NAME"
echo "  App Service: ${APP_SERVICE_NAME:-<not set>}"
echo "  Image Tag: $IMAGE_TAG"
echo ""

# Prompt for missing values
if [ -z "$RESOURCE_GROUP" ]; then
    read -p "Enter Resource Group name: " RESOURCE_GROUP
fi

if [ -z "$ACR_NAME" ]; then
    read -p "Enter Azure Container Registry name: " ACR_NAME
fi

if [ -z "$APP_SERVICE_NAME" ]; then
    read -p "Enter App Service name: " APP_SERVICE_NAME
fi

echo ""
echo "This deployment will:"
echo "  1. Build and push the backend container to ACR"
echo "  2. Update the Azure Container Instance"
echo "  3. Build and deploy the frontend to App Service"
echo "  4. Configure RBAC roles for managed identity"
echo ""
echo "Required Azure resources (should already exist):"
echo "  - Azure Container Registry (ACR)"
echo "  - Azure Container Instance (ACI) in VNet"
echo "  - Azure App Service (frontend)"
echo "  - Azure Cosmos DB (products, conversations containers)"
echo "  - Azure Blob Storage (product-images, generated-images containers)"
echo "  - Azure OpenAI (GPT model for text generation)"
echo "  - Azure OpenAI (DALL-E 3 for image generation - can be separate resource)"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    
    # Step 1: Build and push container
    echo ""
    echo "Step 1: Building and pushing backend container..."
    echo "=========================================="
    
    cd "$PROJECT_DIR/src"
    
    # Login to ACR
    az acr login --name "$ACR_NAME"
    
    # Build and push using ACR tasks
    az acr build \
        --registry "$ACR_NAME" \
        --image "contentgen-backend:$IMAGE_TAG" \
        --file WebApp.Dockerfile \
        .
    
    echo "✓ Container built and pushed to $ACR_NAME.azurecr.io/contentgen-backend:$IMAGE_TAG"
    
    # Step 2: Get the current container's managed identity
    echo ""
    echo "Step 2: Updating Azure Container Instance..."
    echo "=========================================="
    
    # Get current ACI configuration
    CURRENT_IP=$(az container show -g "$RESOURCE_GROUP" -n "$CONTAINER_NAME" --query "ipAddress.ip" -o tsv 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_IP" ]; then
        echo "Current container IP: $CURRENT_IP"
        echo "Restarting container with new image..."
        az container restart -g "$RESOURCE_GROUP" -n "$CONTAINER_NAME"
    else
        echo "Warning: Container $CONTAINER_NAME not found. You may need to create it manually."
    fi
    
    # Step 3: Build and deploy frontend
    echo ""
    echo "Step 3: Building and deploying frontend..."
    echo "=========================================="
    
    cd "$PROJECT_DIR/src/frontend"
    npm install
    npm run build
    
    # Copy built files to server directory
    cp -r "$PROJECT_DIR/src/static/"* "$PROJECT_DIR/src/frontend-server/static/"
    
    cd "$PROJECT_DIR/src/frontend-server"
    
    # Create deployment package
    rm -f frontend-deploy.zip
    zip -r frontend-deploy.zip static/ server.js package.json package-lock.json
    
    # Deploy to App Service
    az webapp deploy \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --src-path frontend-deploy.zip \
        --type zip
    
    echo "✓ Frontend deployed to $APP_SERVICE_NAME"
    
    # Step 4: Get managed identity and show RBAC requirements
    echo ""
    echo "Step 4: RBAC Configuration"
    echo "=========================================="
    
    PRINCIPAL_ID=$(az container show -g "$RESOURCE_GROUP" -n "$CONTAINER_NAME" --query "identity.principalId" -o tsv 2>/dev/null || echo "")
    
    if [ -n "$PRINCIPAL_ID" ]; then
        echo "Container Managed Identity Principal ID: $PRINCIPAL_ID"
        echo ""
        echo "Required RBAC role assignments for the managed identity:"
        echo ""
        echo "1. Azure OpenAI (GPT model):"
        echo "   Role: Cognitive Services OpenAI User"
        echo "   az role assignment create --assignee $PRINCIPAL_ID \\"
        echo "     --role 'Cognitive Services OpenAI User' \\"
        echo "     --scope <GPT_RESOURCE_ID>"
        echo ""
        echo "2. Azure OpenAI (DALL-E model - if separate resource):"
        echo "   Role: Cognitive Services OpenAI User"
        echo "   az role assignment create --assignee $PRINCIPAL_ID \\"
        echo "     --role 'Cognitive Services OpenAI User' \\"
        echo "     --scope <DALLE_RESOURCE_ID>"
        echo ""
        echo "3. Azure Cosmos DB:"
        echo "   Role: Cosmos DB Built-in Data Contributor (data plane)"
        echo "   az cosmosdb sql role assignment create \\"
        echo "     --account-name <COSMOS_ACCOUNT> \\"
        echo "     --resource-group $RESOURCE_GROUP \\"
        echo "     --scope '/' \\"
        echo "     --principal-id $PRINCIPAL_ID \\"
        echo "     --role-definition-id 00000000-0000-0000-0000-000000000002"
        echo ""
        echo "   Role: Cosmos DB Account Reader Role (for metadata)"
        echo "   az role assignment create --assignee $PRINCIPAL_ID \\"
        echo "     --role 'Cosmos DB Account Reader Role' \\"
        echo "     --scope <COSMOS_RESOURCE_ID>"
        echo ""
        echo "4. Azure Blob Storage:"
        echo "   Role: Storage Blob Data Contributor"
        echo "   az role assignment create --assignee $PRINCIPAL_ID \\"
        echo "     --role 'Storage Blob Data Contributor' \\"
        echo "     --scope <STORAGE_RESOURCE_ID>"
    else
        echo "Warning: Could not retrieve managed identity. Configure RBAC manually."
    fi
    
    echo ""
    echo "============================================"
    echo "Deployment complete!"
    echo "============================================"
    
    # Get App Service URL
    WEBAPP_URL=$(az webapp show -g "$RESOURCE_GROUP" -n "$APP_SERVICE_NAME" --query "defaultHostName" -o tsv 2>/dev/null || echo "")
    if [ -n "$WEBAPP_URL" ]; then
        echo ""
        echo "Application URL: https://$WEBAPP_URL"
    fi
    
    echo ""
    echo "Post-deployment steps:"
    echo "1. Verify RBAC roles are assigned (see above)"
    echo "2. Upload product data: python scripts/load_sample_data.py"
    echo "3. Test the application at the URL above"
    echo ""
    
else
    echo "Deployment cancelled."
fi
