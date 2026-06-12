// ============================================================================
// Module: AI Search
// Description: AVM wrapper for an Azure AI Search service.
// AVM Module: avm/res/search/search-service:0.12.0
// ============================================================================

@description('Required. Name of the AI Search service.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. SKU of the AI Search service.')
param sku string = 'basic'

@description('Optional. Number of replicas.')
param replicaCount int = 1

@description('Required. Principal ID of the managed identity to grant search data/service roles.')
param principalId string

@description('Optional. Diagnostic settings for monitoring.')
param diagnosticSettings array = []

module search 'br/public:avm/res/search/search-service:0.12.0' = {
  name: take('avm.res.search.search-service.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    sku: sku
    replicaCount: replicaCount
    partitionCount: 1
    hostingMode: 'Default'
    semanticSearch: 'free'
    managedIdentities: { systemAssigned: true }
    disableLocalAuth: true
    roleAssignments: [
      {
        principalId: principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
      }
      {
        principalId: principalId
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
    diagnosticSettings: !empty(diagnosticSettings) ? diagnosticSettings : null
    // AI Search remains publicly accessible - accessed from ACI via managed identity
    publicNetworkAccess: 'Enabled'
  }
}

@description('Resource ID of the AI Search service.')
output resourceId string = search.outputs.resourceId

@description('Name of the AI Search service.')
output name string = search.outputs.name
