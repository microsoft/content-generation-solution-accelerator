// ============================================================================
// Module: Bastion Host
// Description: Vanilla Bicep module for an Azure Bastion host (Standard SKU).
// Resources: Microsoft.Network/bastionHosts, Microsoft.Network/publicIPAddresses
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
// ============================================================================

@description('Required. Name of the Bastion host.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Resource ID of the virtual network to attach the Bastion host to.')
param virtualNetworkResourceId string

@description('Optional. Resource ID of the Log Analytics workspace for diagnostics. Empty disables diagnostics.')
param logAnalyticsWorkspaceResourceId string = ''

resource publicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-${name}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource bastion 'Microsoft.Network/bastionHosts@2024-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    ipConfigurations: [
      {
        name: 'IpConf'
        properties: {
          subnet: {
            id: '${virtualNetworkResourceId}/subnets/AzureBastionSubnet'
          }
          publicIPAddress: {
            id: publicIp.id
          }
        }
      }
    ]
  }
}

resource bastionDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceResourceId)) {
  name: 'bastionDiagnostics'
  scope: bastion
  properties: {
    workspaceId: logAnalyticsWorkspaceResourceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
  }
}

@description('Resource ID of the Bastion host.')
output resourceId string = bastion.id

@description('Name of the Bastion host.')
output name string = bastion.name
