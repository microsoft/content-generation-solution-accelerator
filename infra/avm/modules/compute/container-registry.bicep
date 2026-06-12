// ============================================================================
// Module: Container Registry
// Description: AVM wrapper for an Azure Container Registry used by the Docker
//              build (bicep) deployment flavor. AZD builds and pushes the
//              application images here.
// AVM Module: avm/res/container-registry/registry:0.9.0
// ============================================================================

@description('Required. Name of the container registry.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Principal ID of the managed identity to grant AcrPull.')
param principalId string

module registry 'br/public:avm/res/container-registry/registry:0.9.0' = {
  name: take('avm.res.container-registry.registry.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    acrSku: 'Standard'
    acrAdminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    roleAssignments: [
      {
        principalId: principalId
        roleDefinitionIdOrName: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

@description('Resource ID of the container registry.')
output resourceId string = registry.outputs.resourceId

@description('Name of the container registry.')
output name string = registry.outputs.name

@description('Login server of the container registry.')
output loginServer string = registry.outputs.loginServer
