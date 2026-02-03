#!/bin/bash
#
# assign_aci_roles.sh
# Assigns required role assignments to the ACI managed identity for:
# - Cosmos DB (Built-in Data Contributor)
# - Storage Account (Storage Blob Data Contributor)
# - AI Search (Search Index Data Contributor)
# - Azure OpenAI (Cognitive Services OpenAI Contributor) - optional external resource
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Usage
usage() {
    echo "Usage: $0 -g <resource-group> -c <container-name> [-o <openai-resource-group>] [-a <openai-account-name>]"
    echo ""
    echo "Required parameters:"
    echo "  -g  Resource group name containing the ACI and other resources"
    echo "  -c  Container instance name"
    echo ""
    echo "Optional parameters:"
    echo "  -o  Resource group containing Azure OpenAI resource (if external)"
    echo "  -a  Azure OpenAI account name (if external)"
    echo ""
    echo "Example:"
    echo "  $0 -g rg-contentgen-jahunte -c content-gen-app"
    echo "  $0 -g rg-contentgen-jahunte -c content-gen-app -o rg-dev -a ai-account-254ly3n5ky7vw"
    exit 1
}

# Parse arguments
while getopts "g:c:o:a:h" opt; do
    case $opt in
        g) RESOURCE_GROUP="$OPTARG" ;;
        c) CONTAINER_NAME="$OPTARG" ;;
        o) OPENAI_RESOURCE_GROUP="$OPTARG" ;;
        a) OPENAI_ACCOUNT_NAME="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ] || [ -z "$CONTAINER_NAME" ]; then
    print_error "Resource group and container name are required"
    usage
fi

echo "=================================================="
echo "ACI Role Assignment Script"
echo "=================================================="
echo ""

# Authenticate with Azure
if az account show &> /dev/null; then
    print_status "Already authenticated with Azure"
else
    print_warning "Not authenticated. Attempting to login..."
    az login
fi

# Get ACI managed identity principal ID
echo ""
echo "Getting ACI managed identity..."
ACI_PRINCIPAL_ID=$(az container show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --query "identity.principalId" -o tsv 2>/dev/null)

if [ -z "$ACI_PRINCIPAL_ID" ]; then
    print_error "Could not get principal ID for container '$CONTAINER_NAME'"
    print_error "Make sure the container exists and has a system-assigned managed identity"
    exit 1
fi

print_status "ACI Principal ID: $ACI_PRINCIPAL_ID"

# ========================================
# 1. Cosmos DB Role Assignment
# ========================================
echo ""
echo "------------------------------------------"
echo "1. Cosmos DB Role Assignment"
echo "------------------------------------------"

# Find Cosmos DB account in the resource group
COSMOS_ACCOUNT=$(az cosmosdb list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[0].name" -o tsv 2>/dev/null)

if [ -z "$COSMOS_ACCOUNT" ]; then
    print_warning "No Cosmos DB account found in resource group '$RESOURCE_GROUP'"
else
    print_status "Found Cosmos DB account: $COSMOS_ACCOUNT"
    
    # Check if role already exists
    COSMOS_ROLE_EXISTS=$(az cosmosdb sql role assignment list \
        --resource-group "$RESOURCE_GROUP" \
        --account-name "$COSMOS_ACCOUNT" \
        --query "[?roleDefinitionId.ends_with(@, '00000000-0000-0000-0000-000000000002') && principalId == '$ACI_PRINCIPAL_ID']" -o tsv 2>/dev/null)
    
    if [ -n "$COSMOS_ROLE_EXISTS" ]; then
        print_status "ACI already has Cosmos DB Built-in Data Contributor role"
    else
        echo "Assigning Cosmos DB Built-in Data Contributor role..."
        MSYS_NO_PATHCONV=1 az cosmosdb sql role assignment create \
            --resource-group "$RESOURCE_GROUP" \
            --account-name "$COSMOS_ACCOUNT" \
            --role-definition-id "00000000-0000-0000-0000-000000000002" \
            --principal-id "$ACI_PRINCIPAL_ID" \
            --scope "/" \
            --output none 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_status "Cosmos DB Built-in Data Contributor role assigned"
        else
            print_error "Failed to assign Cosmos DB role"
        fi
    fi
fi

# ========================================
# 2. Storage Account Role Assignment
# ========================================
echo ""
echo "------------------------------------------"
echo "2. Storage Account Role Assignment"
echo "------------------------------------------"

# Find storage account in the resource group
STORAGE_ACCOUNT=$(az storage account list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[0].name" -o tsv 2>/dev/null)

if [ -z "$STORAGE_ACCOUNT" ]; then
    print_warning "No Storage account found in resource group '$RESOURCE_GROUP'"
else
    print_status "Found Storage account: $STORAGE_ACCOUNT"
    
    STORAGE_ID=$(az storage account show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STORAGE_ACCOUNT" \
        --query "id" -o tsv)
    
    # Storage Blob Data Contributor role ID
    STORAGE_ROLE_ID="ba92f5b4-2d11-453d-a403-e96b0029c9fe"
    
    # Check if role already exists
    STORAGE_ROLE_EXISTS=$(az role assignment list \
        --assignee "$ACI_PRINCIPAL_ID" \
        --role "$STORAGE_ROLE_ID" \
        --scope "$STORAGE_ID" \
        --query "[0].id" -o tsv 2>/dev/null)
    
    if [ -n "$STORAGE_ROLE_EXISTS" ]; then
        print_status "ACI already has Storage Blob Data Contributor role"
    else
        echo "Assigning Storage Blob Data Contributor role..."
        az role assignment create \
            --assignee-object-id "$ACI_PRINCIPAL_ID" \
            --assignee-principal-type "ServicePrincipal" \
            --role "$STORAGE_ROLE_ID" \
            --scope "$STORAGE_ID" \
            --output none 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_status "Storage Blob Data Contributor role assigned"
        else
            print_error "Failed to assign Storage role"
        fi
    fi
fi

# ========================================
# 3. AI Search Role Assignment
# ========================================
echo ""
echo "------------------------------------------"
echo "3. AI Search Role Assignment"
echo "------------------------------------------"

# Find AI Search service in the resource group
SEARCH_SERVICE=$(az search service list \
    --resource-group "$RESOURCE_GROUP" \
    --query "[0].name" -o tsv 2>/dev/null)

if [ -z "$SEARCH_SERVICE" ]; then
    print_warning "No AI Search service found in resource group '$RESOURCE_GROUP'"
else
    print_status "Found AI Search service: $SEARCH_SERVICE"
    
    SEARCH_ID=$(az search service show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$SEARCH_SERVICE" \
        --query "id" -o tsv)
    
    # Search Index Data Contributor role ID
    SEARCH_ROLE_ID="8ebe5a00-799e-43f5-93ac-243d3dce84a7"
    
    # Check if role already exists
    SEARCH_ROLE_EXISTS=$(az role assignment list \
        --assignee "$ACI_PRINCIPAL_ID" \
        --role "$SEARCH_ROLE_ID" \
        --scope "$SEARCH_ID" \
        --query "[0].id" -o tsv 2>/dev/null)
    
    if [ -n "$SEARCH_ROLE_EXISTS" ]; then
        print_status "ACI already has Search Index Data Contributor role"
    else
        echo "Assigning Search Index Data Contributor role..."
        az role assignment create \
            --assignee-object-id "$ACI_PRINCIPAL_ID" \
            --assignee-principal-type "ServicePrincipal" \
            --role "$SEARCH_ROLE_ID" \
            --scope "$SEARCH_ID" \
            --output none 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_status "Search Index Data Contributor role assigned"
        else
            print_error "Failed to assign Search role"
        fi
    fi
fi

# ========================================
# 4. Azure OpenAI Role Assignment (Optional)
# ========================================
echo ""
echo "------------------------------------------"
echo "4. Azure OpenAI Role Assignment"
echo "------------------------------------------"

if [ -n "$OPENAI_RESOURCE_GROUP" ] && [ -n "$OPENAI_ACCOUNT_NAME" ]; then
    print_status "Using external OpenAI resource: $OPENAI_ACCOUNT_NAME in $OPENAI_RESOURCE_GROUP"
    
    OPENAI_ID=$(az cognitiveservices account show \
        --resource-group "$OPENAI_RESOURCE_GROUP" \
        --name "$OPENAI_ACCOUNT_NAME" \
        --query "id" -o tsv 2>/dev/null)
    
    if [ -z "$OPENAI_ID" ]; then
        print_error "Could not find OpenAI resource '$OPENAI_ACCOUNT_NAME' in '$OPENAI_RESOURCE_GROUP'"
    else
        # Cognitive Services OpenAI Contributor role ID
        OPENAI_ROLE_ID="a001fd3d-188f-4b5d-821b-7da978bf7442"
        
        # Check if role already exists
        OPENAI_ROLE_EXISTS=$(az role assignment list \
            --assignee "$ACI_PRINCIPAL_ID" \
            --role "$OPENAI_ROLE_ID" \
            --scope "$OPENAI_ID" \
            --query "[0].id" -o tsv 2>/dev/null)
        
        if [ -n "$OPENAI_ROLE_EXISTS" ]; then
            print_status "ACI already has Cognitive Services OpenAI Contributor role"
        else
            echo "Assigning Cognitive Services OpenAI Contributor role..."
            az role assignment create \
                --assignee-object-id "$ACI_PRINCIPAL_ID" \
                --assignee-principal-type "ServicePrincipal" \
                --role "$OPENAI_ROLE_ID" \
                --scope "$OPENAI_ID" \
                --output none 2>/dev/null
            
            if [ $? -eq 0 ]; then
                print_status "Cognitive Services OpenAI Contributor role assigned"
            else
                print_error "Failed to assign OpenAI role"
            fi
        fi
    fi
else
    # Try to find OpenAI in same resource group
    OPENAI_ACCOUNT=$(az cognitiveservices account list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?kind=='AIServices' || kind=='OpenAI'].name | [0]" -o tsv 2>/dev/null)
    
    if [ -z "$OPENAI_ACCOUNT" ]; then
        print_warning "No Azure OpenAI/AI Services found in resource group '$RESOURCE_GROUP'"
        print_warning "Use -o and -a parameters to specify external OpenAI resource"
    else
        print_status "Found AI Services account: $OPENAI_ACCOUNT"
        
        OPENAI_ID=$(az cognitiveservices account show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$OPENAI_ACCOUNT" \
            --query "id" -o tsv)
        
        # Cognitive Services OpenAI Contributor role ID
        OPENAI_ROLE_ID="a001fd3d-188f-4b5d-821b-7da978bf7442"
        
        # Check if role already exists
        OPENAI_ROLE_EXISTS=$(az role assignment list \
            --assignee "$ACI_PRINCIPAL_ID" \
            --role "$OPENAI_ROLE_ID" \
            --scope "$OPENAI_ID" \
            --query "[0].id" -o tsv 2>/dev/null)
        
        if [ -n "$OPENAI_ROLE_EXISTS" ]; then
            print_status "ACI already has Cognitive Services OpenAI Contributor role"
        else
            echo "Assigning Cognitive Services OpenAI Contributor role..."
            az role assignment create \
                --assignee-object-id "$ACI_PRINCIPAL_ID" \
                --assignee-principal-type "ServicePrincipal" \
                --role "$OPENAI_ROLE_ID" \
                --scope "$OPENAI_ID" \
                --output none 2>/dev/null
            
            if [ $? -eq 0 ]; then
                print_status "Cognitive Services OpenAI Contributor role assigned"
            else
                print_error "Failed to assign OpenAI role"
            fi
        fi
    fi
fi

# ========================================
# Summary
# ========================================
echo ""
echo "=================================================="
echo "Role Assignment Complete"
echo "=================================================="
echo ""
echo "ACI Container: $CONTAINER_NAME"
echo "Principal ID:  $ACI_PRINCIPAL_ID"
echo ""
echo "To verify assignments, run:"
echo "  az role assignment list --assignee $ACI_PRINCIPAL_ID --all -o table"
echo ""
