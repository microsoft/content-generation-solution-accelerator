// ============================================================================
// Module: Log Analytics Workspace
// Description: Vanilla Bicep module for an Azure Log Analytics Workspace.
// Resource: Microsoft.OperationalInsights/workspaces@2025-02-01
// ============================================================================

@description('Required. Name of the Log Analytics workspace.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 365
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

@description('Resource ID of the Log Analytics workspace.')
output resourceId string = workspace.id

@description('Name of the Log Analytics workspace.')
output name string = workspace.name
