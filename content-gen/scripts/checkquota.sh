#!/bin/bash

# =============================================================================
# Quota Check Script for Content Generation Solution Accelerator
# Checks Azure OpenAI quota across regions for GPT and image models.
# Selects the first region with sufficient quota for ALL required models.
#
# Works in both CI (service principal) and local (existing az login) modes.
# Auto-detects mode based on environment variables.
#
# Usage (local):
#   bash checkquota.sh [image_model_choice]
#   bash checkquota.sh gpt-image-1
#   bash checkquota.sh none
#
# Usage (CI - via env vars):
#   Set AZURE_SUBSCRIPTION_ID, GPT_MIN_CAPACITY, AZURE_REGIONS, IMAGE_MODEL_CHOICE
#   Authentication is handled externally via OIDC (az login already done before this script runs)
# =============================================================================

# ---- Determine run mode: CI (pre-authenticated) or Local (existing session) ----
if [[ -n "$AZURE_SUBSCRIPTION_ID" ]] && az account show &>/dev/null; then
    RUN_MODE="ci"
else
    RUN_MODE="local"
fi

# ---- Configuration ----
# In local mode, image model can be passed as first argument
if [[ "$RUN_MODE" == "local" ]]; then
    IMAGE_MODEL_CHOICE="${1:-${IMAGE_MODEL_CHOICE:-gpt-image-1}}"
else
    IMAGE_MODEL_CHOICE="${IMAGE_MODEL_CHOICE:-gpt-image-1}"
fi

GPT_MIN_CAPACITY="${GPT_MIN_CAPACITY:-150}"
IMAGE_MODEL_MIN_CAPACITY="${IMAGE_MODEL_MIN_CAPACITY:-1}"

# Regions to check
if [[ -n "$AZURE_REGIONS" ]]; then
    IFS=', ' read -ra REGIONS <<< "$AZURE_REGIONS"
else
    REGIONS=("westus3" "eastus2" "uaenorth" "swedencentral" "australiaeast" "eastus" "uksouth" "japaneast")
fi

# Map image model choice to Azure quota model name
declare -A IMAGE_MODEL_QUOTA_NAME
IMAGE_MODEL_QUOTA_NAME=(
  ["gpt-image-1"]="OpenAI.GlobalStandard.gpt-image-1"
  ["gpt-image-1.5"]="OpenAI.GlobalStandard.gpt-image-1.5"
  ["none"]=""
)

# ---- Validate image model choice ----
ALLOWED_MODELS=("gpt-image-1" "gpt-image-1.5" "none")
if [[ ! " ${ALLOWED_MODELS[@]} " =~ " ${IMAGE_MODEL_CHOICE} " ]]; then
    echo "❌ ERROR: Invalid image model choice: '$IMAGE_MODEL_CHOICE'"
    echo "   Allowed values: ${ALLOWED_MODELS[*]}"
    exit 1
fi

# ---- Authentication ----
if [[ "$RUN_MODE" == "ci" ]]; then
    echo "🔑 Using pre-authenticated Azure CLI session (CI mode via OIDC)..."

    SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"
    if [[ -z "$SUBSCRIPTION_ID" || -z "$GPT_MIN_CAPACITY" ]]; then
        echo "❌ ERROR: Missing required environment variables."
        echo "   AZURE_SUBSCRIPTION_ID=${SUBSCRIPTION_ID:-(empty)}"
        echo "   GPT_MIN_CAPACITY=${GPT_MIN_CAPACITY:-(empty)}"
        echo "   AZURE_REGIONS=${AZURE_REGIONS:-(empty)}"
        exit 1
    fi

    echo "🔄 Setting Azure subscription..."
    if ! az account set --subscription "$SUBSCRIPTION_ID"; then
        echo "❌ ERROR: Invalid subscription ID or insufficient permissions."
        exit 1
    fi
    echo "✅ Azure subscription set successfully."
else
    echo "🔑 Using existing Azure CLI session (local mode)..."
    if ! az account show &>/dev/null; then
        echo "❌ Not logged in. Run 'az login' first."
        exit 1
    fi
    SUBSCRIPTION=$(az account show --query "name" -o tsv)
    echo "✅ Using subscription: $SUBSCRIPTION"
fi

echo ""
echo "📋 Configuration:"
echo "   Mode: $RUN_MODE"
echo "   Image Model Choice: $IMAGE_MODEL_CHOICE"
echo "   GPT Min Capacity: $GPT_MIN_CAPACITY"
echo "   Image Model Min Capacity: $IMAGE_MODEL_MIN_CAPACITY"
echo "   Regions to check: ${REGIONS[*]}"
echo ""

# ---- Build Model Capacity Map ----
declare -A MIN_CAPACITY
MIN_CAPACITY=(
    ["OpenAI.GlobalStandard.gpt-5.1"]=$GPT_MIN_CAPACITY
)

# Add image model to quota check if not 'none'
IMAGE_QUOTA_NAME="${IMAGE_MODEL_QUOTA_NAME[$IMAGE_MODEL_CHOICE]}"
if [[ -n "$IMAGE_QUOTA_NAME" ]]; then
    MIN_CAPACITY["$IMAGE_QUOTA_NAME"]=$IMAGE_MODEL_MIN_CAPACITY
    echo "🖼️  Image model '$IMAGE_MODEL_CHOICE' added to quota check (key: $IMAGE_QUOTA_NAME, min capacity: $IMAGE_MODEL_MIN_CAPACITY)"
else
    echo "ℹ️  Image model set to 'none' — skipping image model quota check."
fi
echo ""

# ---- Main Quota Check Loop ----
VALID_REGION=""
for REGION in "${REGIONS[@]}"; do
    echo "========================================"
    echo "🔍 Checking region: $REGION"

    QUOTA_INFO=$(az cognitiveservices usage list --location "$REGION" --output json 2>/dev/null)
    if [ -z "$QUOTA_INFO" ]; then
        echo "   ⚠️  Failed to retrieve quota for region $REGION. Skipping."
        continue
    fi

    INSUFFICIENT_QUOTA=false
    for MODEL in "${!MIN_CAPACITY[@]}"; do
        MODEL_INFO=$(echo "$QUOTA_INFO" | awk -v model="\"value\": \"$MODEL\"" '
            BEGIN { RS="},"; FS="," }
            $0 ~ model { print $0 }
        ')

        if [ -z "$MODEL_INFO" ]; then
            echo "   ⚠️  No quota info for: $MODEL in $REGION. Skipping."
            INSUFFICIENT_QUOTA=true
            continue
        fi

        CURRENT_VALUE=$(echo "$MODEL_INFO" | awk -F': ' '/"currentValue"/ {print $2}' | tr -d ',' | tr -d ' ')
        LIMIT=$(echo "$MODEL_INFO" | awk -F': ' '/"limit"/ {print $2}' | tr -d ',' | tr -d ' ')

        CURRENT_VALUE=${CURRENT_VALUE:-0}
        LIMIT=${LIMIT:-0}

        CURRENT_VALUE=$(echo "$CURRENT_VALUE" | cut -d'.' -f1)
        LIMIT=$(echo "$LIMIT" | cut -d'.' -f1)

        AVAILABLE=$((LIMIT - CURRENT_VALUE))

        if [ "$AVAILABLE" -lt "${MIN_CAPACITY[$MODEL]}" ]; then
            echo "   ❌ $MODEL | Used: $CURRENT_VALUE | Limit: $LIMIT | Available: $AVAILABLE | Need: ${MIN_CAPACITY[$MODEL]}"
            INSUFFICIENT_QUOTA=true
            break
        else
            echo "   ✅ $MODEL | Used: $CURRENT_VALUE | Limit: $LIMIT | Available: $AVAILABLE | Need: ${MIN_CAPACITY[$MODEL]}"
        fi
    done

    if [ "$INSUFFICIENT_QUOTA" = false ]; then
        VALID_REGION="$REGION"
        echo "   🎉 Region '$REGION' has sufficient quota for all models!"
        break
    fi

done

echo ""
echo "========================================"
if [ -z "$VALID_REGION" ]; then
    echo "❌ No region with sufficient quota found!"
    echo "   Image Model: $IMAGE_MODEL_CHOICE"
    echo "   Checked regions: ${REGIONS[*]}"

    # In CI mode, set GITHUB_ENV variable instead of exiting with error
    if [[ "$RUN_MODE" == "ci" ]]; then
        echo "QUOTA_FAILED=true" >> "$GITHUB_ENV"
        exit 0
    else
        exit 1
    fi
else
    echo "✅ Recommended Region: $VALID_REGION"

    if [[ "$RUN_MODE" == "ci" ]]; then
        echo "VALID_REGION=$VALID_REGION" >> "$GITHUB_ENV"
    fi
    exit 0
fi
