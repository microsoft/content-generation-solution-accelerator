// ============================================================================
// Module: Private DNS Zone
// Description: Vanilla Bicep module for a single Private DNS Zone linked to a VNet.
// Resource: Microsoft.Network/privateDnsZones@2024-06-01
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
// ============================================================================

@description('Required. Name of the private DNS zone (e.g. privatelink.blob.core.windows.net).')
param name string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Resource ID of the virtual network to link.')
param virtualNetworkResourceId string

resource zone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: name
  location: 'global'
  tags: tags
}

resource virtualNetworkLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: zone
  name: '${last(split(virtualNetworkResourceId, '/'))}-link'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkResourceId
    }
  }
}

@description('Resource ID of the private DNS zone.')
output resourceId string = zone.id

@description('Name of the private DNS zone.')
output name string = zone.name
