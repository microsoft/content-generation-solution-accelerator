// ============================================================================
// Module: User Assigned Managed Identity
// Description: Vanilla Bicep module for a User Assigned Managed Identity.
// Resource: Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30
// ============================================================================

@description('Required. Name of the user assigned managed identity.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: name
  location: location
  tags: tags
}

@description('Resource ID of the managed identity.')
output resourceId string = identity.id

@description('Principal (object) ID of the managed identity.')
output principalId string = identity.properties.principalId

@description('Client ID of the managed identity.')
output clientId string = identity.properties.clientId

@description('Name of the managed identity.')
output name string = identity.name
