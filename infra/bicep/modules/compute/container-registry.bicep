// ============================================================================
// Module: Container Registry
// Description: Vanilla Bicep module for an Azure Container Registry used by the
//              Docker build (bicep) deployment flavor. AZD builds and pushes the
//              application images here.
// Resource: Microsoft.ContainerRegistry/registries@2023-11-01-preview
// ============================================================================

@description('Required. Name of the container registry.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Principal ID of the managed identity to grant AcrPull.')
param principalId string

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

// AcrPull role assignment for the managed identity.
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, principalId, '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Resource ID of the container registry.')
output resourceId string = registry.id

@description('Name of the container registry.')
output name string = registry.name

@description('Login server of the container registry.')
output loginServer string = registry.properties.loginServer
