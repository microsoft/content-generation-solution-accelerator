#!/bin/bash

# Variables
storageAccount="$1"
fileSystem="$2"
keyvaultName="$3"
cosmosDbAccountName="$4"
resourceGroupName="$5"
aiSearchName="$6"
managedIdentityClientId="$7"
aif_resource_id="${8}"

# Global variables to track original network access states
original_storage_public_access=""
original_keyvault_public_access=""
original_foundry_public_access=""
aif_resource_group=""
aif_account_resource_id=""
aif_subscription_id=""

# Function to enable public network access temporarily
enable_public_access() {
    echo "=== Temporarily enabling public network access for services ==="
    
    # Enable public access for Storage Account
    original_storage_public_access=$(az storage account show \
        --name "$storageAccount" \
        --resource-group "$resourceGroupName" \
        --query "publicNetworkAccess" \
        -o tsv)
    
    if [ "$original_storage_public_access" != "Enabled" ]; then
        echo "Enabling public access for Storage Account: $storageAccount"
        az storage account update \
            --name "$storageAccount" \
            --resource-group "$resourceGroupName" \
            --public-network-access Enabled \
            --default-action Allow \
            --output none
        if [ $? -eq 0 ]; then
            echo "✓ Storage Account public access enabled"
        else
            echo "✗ Failed to enable Storage Account public access"
            return 1
        fi
    else
        echo "✓ Storage Account public access already enabled"
    fi

    # Enable public access for AI Foundry
    aif_account_resource_id=$(echo "$aif_resource_id" | sed 's|/projects/.*||')
    aif_resource_group=$(echo "$aif_account_resource_id" | sed -n 's|.*/resourceGroups/\([^/]*\)/.*|\1|p')
    # Extract subscription ID from AI Foundry resource ID
    aif_subscription_id=$(echo "$aif_account_resource_id" | sed -n 's|.*/subscriptions/\([^/]*\)/.*|\1|p')

    original_foundry_public_access=$(MSYS_NO_PATHCONV=1 az resource show \
        --ids "$aif_account_resource_id" \
        --subscription "$aif_subscription_id" \
        --api-version 2024-10-01 \
        --query "properties.publicNetworkAccess" \
        --output tsv)
    if [ -z "$original_foundry_public_access" ] || [ "$original_foundry_public_access" = "null" ]; then
        echo "⚠ Info: Could not retrieve AI Foundry network access status."
        echo "  AI Foundry network access might be managed differently."
    elif [ "$original_foundry_public_access" != "Enabled" ]; then
        echo "Enabling public access for AI Foundry: $aif_resource_group"
        if MSYS_NO_PATHCONV=1 az resource update \
            --ids "$aif_account_resource_id" \
            --api-version 2024-10-01 \
            --subscription "$aif_subscription_id" \
            --set properties.publicNetworkAccess=Enabled \
            --set properties.apiProperties.qnaAzureSearchEndpointKey="" \
            --output none; then
            echo "✓ AI Foundry public access enabled"
        else
            echo "⚠ Warning: Failed to enable AI Foundry public access automatically."
        fi
    else
        echo "✓ AI Foundry public access already enabled"
    fi
    
    # Enable public access for Key Vault
    original_keyvault_public_access=$(az keyvault show \
        --name "$keyvaultName" \
        --resource-group "$resourceGroupName" \
        --query "properties.publicNetworkAccess" \
        -o tsv)
    
    if [ "$original_keyvault_public_access" != "Enabled" ]; then
        echo "Enabling public access for Key Vault: $keyvaultName"
        az keyvault update \
            --name "$keyvaultName" \
            --resource-group "$resourceGroupName" \
            --public-network-access Enabled \
            --default-action Allow \
            --output none
        if [ $? -eq 0 ]; then
            echo "✓ Key Vault public access enabled"
        else
            echo "✗ Failed to enable Key Vault public access"
            return 1
        fi
    else
        echo "✓ Key Vault public access already enabled"
    fi
    
    # Additional wait for all changes to propagate fully
    echo "Allowing additional time for all network access changes to propagate..."
    sleep 30
    echo "=== Public network access configuration completed ==="
    return 0
}

# Function to restore original network access settings
restore_network_access() {
    echo "=== Restoring original network access settings ==="
    
    # Restore Storage Account access
    if [ -n "$original_storage_public_access" ] && [ "$original_storage_public_access" != "Enabled" ]; then
        echo "Restoring Storage Account public access to: $original_storage_public_access"
        # Handle case sensitivity - convert to proper case
        case "$original_storage_public_access" in
            "enabled"|"Enabled") restore_value="Enabled" ;;
            "disabled"|"Disabled") restore_value="Disabled" ;;
            *) restore_value="$original_storage_public_access" ;;
        esac
        az storage account update \
            --name "$storageAccount" \
            --resource-group "$resourceGroupName" \
            --public-network-access "$restore_value" \
            --default-action Deny \
            --output none
        if [ $? -eq 0 ]; then
            echo "✓ Storage Account access restored"
        else
            echo "✗ Failed to restore Storage Account access"
        fi
    else
        echo "Storage Account access unchanged (already at desired state)"
    fi
    
    # Restore Key Vault access
    if [ -n "$original_keyvault_public_access" ] && [ "$original_keyvault_public_access" != "Enabled" ]; then
        echo "Restoring Key Vault public access to: $original_keyvault_public_access"
        # Handle case sensitivity - convert to proper case
        case "$original_keyvault_public_access" in
            "enabled"|"Enabled") restore_value="Enabled" ;;
            "disabled"|"Disabled") restore_value="Disabled" ;;
            *) restore_value="$original_keyvault_public_access" ;;
        esac
        az keyvault update \
            --name "$keyvaultName" \
            --resource-group "$resourceGroupName" \
            --public-network-access "$restore_value" \
            --default-action Deny \
            --output none
        if [ $? -eq 0 ]; then
            echo "✓ Key Vault access restored"
        else
            echo "✗ Failed to restore Key Vault access"
        fi
    else
        echo "Key Vault access unchanged (already at desired state)"
    fi

    # Restore AI Foundry access
    if [ -n "$original_foundry_public_access" ] && [ "$original_foundry_public_access" != "Enabled" ]; then
        echo "Restoring AI Foundry public access to: $original_foundry_public_access"
        # Try using the working approach to restore the original setting
        if MSYS_NO_PATHCONV=1 az resource update \
            --ids "$aif_account_resource_id" \
            --api-version 2024-10-01 \
            --subscription "$aif_subscription_id" \
            --set properties.publicNetworkAccess="$original_foundry_public_access" \
            --set properties.apiProperties.qnaAzureSearchEndpointKey="" \
            --set properties.networkAcls.bypass="AzureServices" \
            --output none 2>/dev/null; then
            echo "✓ AI Foundry access restored"
        else
            echo "⚠ Warning: Failed to restore AI Foundry access automatically."
            echo "  Please manually restore network access in the Azure portal if needed."
        fi
    else
        echo "AI Foundry access unchanged (already at desired state)"
    fi
    
    echo "=== Network access restoration completed ==="
}

# Function to handle script cleanup on exit
cleanup_on_exit() {
    exit_code=$?
    echo ""
    if [ $exit_code -ne 0 ]; then
        echo "Script failed with exit code: $exit_code"
    fi
    echo "Performing cleanup..."
    restore_network_access
    exit $exit_code
}

# Set up trap to ensure cleanup happens on exit
trap cleanup_on_exit EXIT INT TERM

# get parameters from azd env, if not provided
if [ -z "$resourceGroupName" ]; then
    resourceGroupName=$(azd env get-value RESOURCE_GROUP_NAME)
fi

if [ -z "$cosmosDbAccountName" ]; then
    cosmosDbAccountName=$(azd env get-value COSMOSDB_ACCOUNT_NAME)
fi

if [ -z "$storageAccount" ]; then
    storageAccount=$(azd env get-value STORAGE_ACCOUNT_NAME)
fi

if [ -z "$fileSystem" ]; then
    fileSystem=$(azd env get-value STORAGE_CONTAINER_NAME)
fi

if [ -z "$keyvaultName" ]; then
    keyvaultName=$(azd env get-value KEY_VAULT_NAME)
fi

if [ -z "$aiSearchName" ]; then
    aiSearchName=$(azd env get-value AI_SEARCH_SERVICE_NAME)
fi

if [ -z "$aif_resource_id" ]; then
    aif_resource_id=$(azd env get-value AI_FOUNDRY_RESOURCE_ID)
fi

# Get subscription id from azd env or from environment variable
azSubscriptionId=$(azd env get-value AZURE_SUBSCRIPTION_ID) || azSubscriptionId="$AZURE_SUBSCRIPTION_ID"

# Check if all required arguments are provided
if [ -z "$storageAccount" ] || [ -z "$fileSystem" ] || [ -z "$keyvaultName" ] || [ -z "$cosmosDbAccountName" ] || [ -z "$resourceGroupName" ] || [ -z "$aif_resource_id" ] || [ -z "$aiSearchName" ]; then
    echo "Usage: $0 <storageAccount> <storageContainerName> <keyvaultName> <cosmosDbAccountName> <resourceGroupName> <aiSearchName> <managedIdentityClientId> <aif_resource_id>"
    exit 1
fi

# Authenticate with Azure
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    if [ -n "$managedIdentityClientId" ]; then
        # Use managed identity if running in Azure
        echo "Authenticating with Managed Identity..."
        az login --identity --client-id ${managedIdentityClientId}
    else
        # Use Azure CLI login if running locally
        echo "Authenticating with Azure CLI..."
        az login --use-device-code
    fi
    echo "Not authenticated with Azure. Attempting to authenticate..."
fi

#check if user has selected the correct subscription
currentSubscriptionId=$(az account show --query id -o tsv)
currentSubscriptionName=$(az account show --query name -o tsv)
if [ "$currentSubscriptionId" != "$azSubscriptionId" ]; then
    echo "Current selected subscription is $currentSubscriptionName ( $currentSubscriptionId )."
    read -rp "Do you want to continue with this subscription?(y/n): " confirmation
    if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
        echo "Fetching available subscriptions..."
        availableSubscriptions=$(az account list --query "[?state=='Enabled'].[name,id]" --output tsv)
        while true; do
            echo ""
            echo "Available Subscriptions:"
            echo "========================"
            echo "$availableSubscriptions" | awk '{printf "%d. %s ( %s )\n", NR, $1, $2}'
            echo "========================"
            echo ""
            read -rp "Enter the number of the subscription (1-$(echo "$availableSubscriptions" | wc -l)) to use: " subscriptionIndex
            if [[ "$subscriptionIndex" =~ ^[0-9]+$ ]] && [ "$subscriptionIndex" -ge 1 ] && [ "$subscriptionIndex" -le $(echo "$availableSubscriptions" | wc -l) ]; then
                selectedSubscription=$(echo "$availableSubscriptions" | sed -n "${subscriptionIndex}p")
                selectedSubscriptionName=$(echo "$selectedSubscription" | cut -f1)
                selectedSubscriptionId=$(echo "$selectedSubscription" | cut -f2)

                # Set the selected subscription
                if  az account set --subscription "$selectedSubscriptionId"; then
                    echo "Switched to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )"
                    break
                else
                    echo "Failed to switch to subscription: $selectedSubscriptionName ( $selectedSubscriptionId )."
                fi
            else
                echo "Invalid selection. Please try again."
            fi
        done
    else
        echo "Proceeding with the current subscription: $currentSubscriptionName ( $currentSubscriptionId )"
        az account set --subscription "$currentSubscriptionId"
    fi
else
    echo "Proceeding with the subscription: $currentSubscriptionName ( $currentSubscriptionId )"
    az account set --subscription "$currentSubscriptionId"
fi

# Enable public network access for required services
enable_public_access
if [ $? -ne 0 ]; then
    echo "Error: Failed to enable public network access for services."
    exit 1
fi

# Call add_cosmosdb_access.sh
echo "Running add_cosmosdb_access.sh"
bash infra/scripts/add_cosmosdb_access.sh "$resourceGroupName" "$cosmosDbAccountName" "$managedIdentityClientId"
if [ $? -ne 0 ]; then
    echo "Error: add_cosmosdb_access.sh failed."
    exit 1
fi
echo "add_cosmosdb_access.sh completed successfully."

# Call copy_kb_files.sh
echo "Running copy_kb_files.sh"
bash infra/scripts/copy_kb_files.sh "$storageAccount" "$fileSystem" "$managedIdentityClientId"
if [ $? -ne 0 ]; then
    echo "Error: copy_kb_files.sh failed."
    exit 1
fi
echo "copy_kb_files.sh completed successfully."

# Call run_create_index_scripts.sh
echo "Running run_create_index_scripts.sh"
bash infra/scripts/run_create_index_scripts.sh "$keyvaultName" "$resourceGroupName" "$aiSearchName" "$managedIdentityClientId" "$aif_resource_id"
if [ $? -ne 0 ]; then
    echo "Error: run_create_index_scripts.sh failed."
    exit 1
fi
echo "run_create_index_scripts.sh completed successfully."

echo "All scripts executed successfully."
# Note: cleanup_on_exit will be called automatically via the trap
