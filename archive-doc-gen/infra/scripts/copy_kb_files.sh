#!/bin/bash

# Variables
storageAccount="$1"
fileSystem="$2"
# baseUrl="$3"
managedIdentityClientId="$3"

echo "Script Started"

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
        az login
    fi
    echo "Not authenticated with Azure. Attempting to authenticate..."
fi

echo "Getting signed in user id"
signed_user_id=$(az ad signed-in-user show --query id -o tsv)
if [ $? -ne 0 ]; then
    if [ -z "$managedIdentityClientId" ]; then
        echo "Error: Failed to get signed in user id."
        exit 1
    else
        signed_user_id=$managedIdentityClientId
    fi
fi

echo "Getting storage account resource id"
storage_account_resource_id=$(az storage account show --name $storageAccount --query id --output tsv)

#check if user has the Storage Blob Data Contributor role, add it if not
echo "Checking if user has the Storage Blob Data Contributor role"
role_assignment=$(MSYS_NO_PATHCONV=1 az role assignment list --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --query "[].roleDefinitionId" -o tsv)
if [ -z "$role_assignment" ]; then
    echo "User does not have the Storage Blob Data Contributor role. Assigning the role."
    MSYS_NO_PATHCONV=1 az role assignment create --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --output none
    if [ $? -eq 0 ]; then
        echo "Role assignment completed successfully."
        sleep 5
        retries=3
        while [ $retries -gt 0 ]; do
            # Check if the role assignment was successful
            role_assignment_check=$(MSYS_NO_PATHCONV=1 az role assignment list --assignee $signed_user_id --role "Storage Blob Data Contributor" --scope $storage_account_resource_id --query "[].roleDefinitionId" -o tsv)
            if [ -n "$role_assignment_check" ]; then
                echo "Role assignment verified successfully."
                sleep 5
                break
            else
                echo "Role assignment not found, retrying..."
                ((retries--))
                sleep 10
            fi
        done
        if [ $retries -eq 0 ]; then
            echo "Error: Role assignment verification failed after multiple attempts. Try rerunning the script."
            exit 1
        fi
    else
        echo "Error: Role assignment failed."
        exit 1
    fi
else
    echo "User already has the Storage Blob Data Contributor role."
fi

zipFileName1="pdfdata.zip"
extractedFolder1="pdf"
zipUrl1="infra/data/$zipFileName1"
# zipUrl1=${baseUrl}"infra/data/$zipFileName1"

# zipFileName2="audio_data.zip"
# extractedFolder2="audiodata"
# zipUrl2=${baseUrl}"infra/data/audio_data.zip"

# Create folders if they do not exist
# mkdir -p "/mnt/azscripts/azscriptinput/$extractedFolder1"
# mkdir -p "/mnt/azscripts/azscriptinput/$extractedFolder2"

# Download the zip file
# curl --output /mnt/azscripts/azscriptinput/"$zipFileName1" "$zipUrl1"
# curl --output /mnt/azscripts/azscriptinput/"$zipFileName2" "$zipUrl2"

# Extract the zip file
unzip -o $zipUrl1 -d infra/data/"$extractedFolder1"
# unzip /mnt/azscripts/azscriptinput/"$zipFileName2" -d /mnt/azscripts/azscriptinput/"$extractedFolder2"

# Using az storage blob upload-batch to upload files with managed identity authentication, as the az storage fs directory upload command is not working with managed identity authentication.
echo "Uploading files to Azure Blob Storage"
az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder1" --source infra/data/"$extractedFolder1" --auth-mode login --pattern '*' --overwrite --output none
if [ $? -ne 0 ]; then
    maxRetries=5
    retries=$maxRetries
    sleepTime=10
    attempt=1
    while [ $retries -gt 0 ]; do
        echo "Error: Failed to upload files to Azure Blob Storage. Retrying upload...$attempt of $maxRetries in $sleepTime seconds"
        sleep $sleepTime
        az storage blob upload-batch --account-name "$storageAccount" --destination "$fileSystem"/"$extractedFolder1" --source infra/data/"$extractedFolder1" --auth-mode login --pattern '*' --overwrite --output none
        if [ $? -eq 0 ]; then
            echo "Files uploaded successfully to Azure Blob Storage."
            break
        else
            ((retries--))
            ((attempt++))
            sleepTime=$((sleepTime * 2))
        fi
    done

    if [ $retries -eq 0 ]; then
        echo "Error: Failed to upload files after all retry attempts."
        exit 1
    fi
else
    echo "Files uploaded successfully to Azure Blob Storage."
fi
# az storage blob upload-batch --account-name "$storageAccount" --destination data/"$extractedFolder2" --source /mnt/azscripts/azscriptinput/"$extractedFolder2" --auth-mode login --pattern '*' --overwrite