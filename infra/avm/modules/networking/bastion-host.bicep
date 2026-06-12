// ============================================================================
// Module: Bastion Host
// Description: AVM wrapper for an Azure Bastion host (Standard SKU).
// AVM Module: avm/res/network/bastion-host:0.8.2
// ============================================================================

@description('Required. Name of the Bastion host.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Resource ID of the virtual network to attach the Bastion host to.')
param virtualNetworkResourceId string

@description('Optional. Resource ID of the Log Analytics workspace for diagnostics. Empty disables diagnostics.')
param logAnalyticsWorkspaceResourceId string = ''

module bastion 'br/public:avm/res/network/bastion-host:0.8.2' = {
  name: take('avm.res.network.bastion-host.${name}', 64)
  params: {
    name: name
    skuName: 'Standard'
    location: location
    virtualNetworkResourceId: virtualNetworkResourceId
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId)
      ? [
          {
            name: 'bastionDiagnostics'
            workspaceResourceId: logAnalyticsWorkspaceResourceId
            logCategoriesAndGroups: [
              {
                categoryGroup: 'allLogs'
                enabled: true
              }
            ]
          }
        ]
      : []
    tags: tags
    enableTelemetry: enableTelemetry
    publicIPAddressObject: {
      name: 'pip-${name}'
    }
  }
}

@description('Resource ID of the Bastion host.')
output resourceId string = bastion.outputs.resourceId

@description('Name of the Bastion host.')
output name string = bastion.outputs.name
