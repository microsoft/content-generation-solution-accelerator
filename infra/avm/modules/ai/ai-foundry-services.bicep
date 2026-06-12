// ============================================================================
// Module: AI Foundry - AI Services Account
// Description: AVM wrapper for an Azure AI Services (Cognitive Services)
//              account configured for AI Foundry, including model deployments
//              and role assignments.
// AVM Module: avm/res/cognitive-services/account:0.14.2
// ============================================================================

@description('Required. Name of the AI Services account.')
param name string

@description('Required. Azure region for the AI Services deployment.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Model deployments to create (format/name/model/version/sku/raiPolicyName).')
param modelDeployments array

@description('Required. Principal ID of the user assigned managed identity.')
param principalId string

@description('Required. Principal ID of the deploying user/service principal.')
param deployerPrincipalId string

@description('Required. Resource ID of the user assigned managed identity to assign to the account.')
param userAssignedIdentityResourceId string

@description('Optional. Enable monitoring diagnostics.')
param enableMonitoring bool = false

@description('Optional. Resource ID of the Log Analytics workspace for diagnostics.')
param logAnalyticsWorkspaceResourceId string = ''

@description('Optional. Disable public network access (private networking).')
param enablePrivateNetworking bool = false

module account 'br/public:avm/res/cognitive-services/account:0.14.2' = {
  name: take('avm.res.cognitive-services.account.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    sku: 'S0'
    kind: 'AIServices'
    disableLocalAuth: true
    allowProjectManagement: true
    customSubDomainName: name
    restrictOutboundNetworkAccess: false
    deployments: [
      for deployment in modelDeployments: {
        name: deployment.name
        model: {
          format: deployment.format
          name: deployment.name
          version: deployment.version
        }
        raiPolicyName: deployment.raiPolicyName
        sku: {
          name: deployment.sku.name
          capacity: deployment.sku.capacity
        }
      }
    ]
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    managedIdentities: {
      userAssignedResourceIds: [userAssignedIdentityResourceId]
    }
    roleAssignments: [
      {
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User
        principalId: principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
        principalId: principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
        principalId: principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User for deployer
        principalId: deployerPrincipalId
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
  }
}

@description('Resource ID of the AI Services account.')
output resourceId string = account.outputs.resourceId

@description('Name of the AI Services account.')
output name string = account.outputs.name
