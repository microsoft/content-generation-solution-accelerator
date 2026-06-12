// ============================================================================
// Module: User Assigned Managed Identity
// Description: AVM wrapper for a User Assigned Managed Identity.
// AVM Module: avm/res/managed-identity/user-assigned-identity:0.5.0
// ============================================================================

@description('Required. Name of the user assigned managed identity.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

module identity 'br/public:avm/res/managed-identity/user-assigned-identity:0.5.0' = {
  name: take('avm.res.managed-identity.user-assigned-identity.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

@description('Resource ID of the managed identity.')
output resourceId string = identity.outputs.resourceId

@description('Principal (object) ID of the managed identity.')
output principalId string = identity.outputs.principalId

@description('Client ID of the managed identity.')
output clientId string = identity.outputs.clientId

@description('Name of the managed identity.')
output name string = identity.outputs.name
