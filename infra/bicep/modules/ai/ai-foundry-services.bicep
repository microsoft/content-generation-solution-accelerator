// ============================================================================
// Module: AI Foundry - AI Services Account
// Description: Vanilla Bicep module for an Azure AI Services (Cognitive Services)
//              account configured for AI Foundry, including model deployments
//              and role assignments.
// Resource: Microsoft.CognitiveServices/accounts@2025-12-01
// ============================================================================

@description('Required. Name of the AI Services account.')
param name string

@description('Required. Azure region for the AI Services deployment.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Model deployments to create (format/name/model/version/sku/raiPolicyName).')
param modelDeployments array

@description('Required. Principal ID of the user assigned managed identity.')
param principalId string

@description('Required. Principal ID of the deploying user/service principal.')
param deployerPrincipalId string

@description('Required. Resource ID of the user assigned managed identity to assign to the account.')
param userAssignedIdentityResourceId string

var roleAssignmentsConfig = [
  {
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
  {
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
  {
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
  {
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User for deployer
    principalId: deployerPrincipalId
    principalType: ''
  }
]

resource account 'Microsoft.CognitiveServices/accounts@2025-12-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    customSubDomainName: name
    disableLocalAuth: true
    allowProjectManagement: true
    restrictOutboundNetworkAccess: false
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
  }
}

@batchSize(1)
resource accountDeployments 'Microsoft.CognitiveServices/accounts/deployments@2025-12-01' = [
  for deployment in modelDeployments: {
    parent: account
    name: deployment.name
    properties: {
      model: {
        format: deployment.format
        name: deployment.name
        version: deployment.version
      }
      raiPolicyName: deployment.raiPolicyName
    }
    sku: {
      name: deployment.sku.name
      capacity: deployment.sku.capacity
    }
  }
]

resource accountRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleConfig in roleAssignmentsConfig: {
    name: guid(account.id, roleConfig.principalId, roleConfig.roleDefinitionId)
    scope: account
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleConfig.roleDefinitionId)
      principalId: roleConfig.principalId
      principalType: empty(roleConfig.principalType) ? null : roleConfig.principalType
    }
  }
]

@description('Resource ID of the AI Services account.')
output resourceId string = account.id

@description('Name of the AI Services account.')
output name string = account.name
