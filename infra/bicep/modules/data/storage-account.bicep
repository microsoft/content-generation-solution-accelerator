// ============================================================================
// Module: Storage Account
// Description: Vanilla Bicep module for an Azure Storage Account (blob) used for
//              product and generated image storage.
// Resource: Microsoft.Storage/storageAccounts@2024-01-01
// ============================================================================

@description('Required. Name of the storage account.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Optional. Storage account SKU.')
param skuName string = 'Standard_LRS'

@description('Required. Blob containers to create. Each item: { name, publicAccess }.')
param containers array

@description('Required. Principal ID of the managed identity to grant Storage Blob Data Contributor.')
param principalId string

resource storageAccount 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Enabled'
    encryption: {
      requireInfrastructureEncryption: true
      keySource: 'Microsoft.Storage'
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = [
  for container in containers: {
    parent: blobServices
    name: container.name
    properties: {
      publicAccess: container.?publicAccess ?? 'None'
    }
  }
]

// Storage Blob Data Contributor role assignment for the managed identity.
resource blobDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, principalId, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Resource ID of the storage account.')
output resourceId string = storageAccount.id

@description('Name of the storage account.')
output name string = storageAccount.name
