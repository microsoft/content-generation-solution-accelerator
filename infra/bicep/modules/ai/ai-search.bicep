// ============================================================================
// Module: AI Search
// Description: Vanilla Bicep module for an Azure AI Search service.
// Resource: Microsoft.Search/searchServices@2024-06-01-preview
// ============================================================================

@description('Required. Name of the AI Search service.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Optional. SKU of the AI Search service.')
param sku string = 'basic'

@description('Optional. Number of replicas.')
param replicaCount int = 1

@description('Required. Principal ID of the managed identity to grant search data/service roles.')
param principalId string

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: 1
    hostingMode: 'default'
    semanticSearch: 'free'
    disableLocalAuth: true
    // AI Search remains publicly accessible - accessed from ACI via managed identity
    publicNetworkAccess: 'enabled'
  }
}

resource searchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, principalId, '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7') // Search Index Data Contributor
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, principalId, '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0') // Search Service Contributor
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Resource ID of the AI Search service.')
output resourceId string = search.id

@description('Name of the AI Search service.')
output name string = search.name
