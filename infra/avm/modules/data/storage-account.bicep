// ============================================================================
// Module: Storage Account
// Description: AVM wrapper for an Azure Storage Account (blob) used for
//              product and generated image storage.
// AVM Module: avm/res/storage/storage-account:0.32.0
// ============================================================================

@description('Required. Name of the storage account.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Storage account SKU.')
param skuName string = 'Standard_LRS'

@description('Required. Blob containers to create.')
param containers array

@description('Required. Principal ID of the managed identity to grant Storage Blob Data Contributor.')
param principalId string

@description('Optional. Enable private networking (disables public access, adds private endpoint).')
param enablePrivateNetworking bool = false

@description('Optional. Subnet resource ID for the private endpoint.')
param subnetResourceId string = ''

@description('Optional. Resource ID of the blob private DNS zone.')
param blobDnsZoneResourceId string = ''

@description('Optional. Diagnostic settings for monitoring.')
param diagnosticSettings array = []

module storageAccount 'br/public:avm/res/storage/storage-account:0.32.0' = {
  name: take('avm.res.storage.storage-account.${name}', 64)
  params: {
    name: name
    location: location
    skuName: skuName
    managedIdentities: { systemAssigned: true }
    minimumTlsVersion: 'TLS1_2'
    requireInfrastructureEncryption: true
    enableTelemetry: enableTelemetry
    tags: tags
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    blobServices: {
      containerDeleteRetentionPolicyEnabled: true
      containerDeleteRetentionPolicyDays: 7
      deleteRetentionPolicyEnabled: true
      deleteRetentionPolicyDays: 7
      containers: containers
    }
    roleAssignments: [
      {
        principalId: principalId
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: enablePrivateNetworking ? 'Deny' : 'Allow'
    }
    allowBlobPublicAccess: false
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    privateEndpoints: enablePrivateNetworking
      ? [
          {
            service: 'blob'
            subnetResourceId: subnetResourceId
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                { privateDnsZoneResourceId: blobDnsZoneResourceId }
              ]
            }
          }
        ]
      : null
    diagnosticSettings: !empty(diagnosticSettings) ? diagnosticSettings : null
  }
}

@description('Resource ID of the storage account.')
output resourceId string = storageAccount.outputs.resourceId

@description('Name of the storage account.')
output name string = storageAccount.outputs.name
