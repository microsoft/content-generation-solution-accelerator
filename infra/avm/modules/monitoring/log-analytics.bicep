// ============================================================================
// Module: Log Analytics Workspace
// Description: AVM wrapper for Azure Log Analytics Workspace.
// AVM Module: avm/res/operational-insights/workspace:0.15.0
// ============================================================================

@description('Required. Name of the Log Analytics workspace.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Enable redundancy (cross-region replication and daily quota).')
param enableRedundancy bool = false

@description('Optional. Replica region used when redundancy is enabled.')
param replicaLocation string = ''

@description('Optional. Disable public network access (private networking).')
param enablePrivateNetworking bool = false

module workspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = {
  name: take('avm.res.operational-insights.workspace.${name}', 64)
  params: {
    name: name
    tags: tags
    location: location
    enableTelemetry: enableTelemetry
    skuName: 'PerGB2018'
    dataRetention: 365
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
    diagnosticSettings: [{ useThisWorkspace: true }]
    dailyQuotaGb: enableRedundancy ? '10' : null
    replication: enableRedundancy
      ? {
          enabled: true
          location: replicaLocation
        }
      : null
    publicNetworkAccessForIngestion: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    publicNetworkAccessForQuery: enablePrivateNetworking ? 'Disabled' : 'Enabled'
  }
}

@description('Resource ID of the Log Analytics workspace.')
output resourceId string = workspace.outputs.resourceId

@description('Name of the Log Analytics workspace.')
output name string = workspace.outputs.name
