// ============================================================================
// Module: Private DNS Zone
// Description: AVM wrapper for a single Private DNS Zone linked to a VNet.
// AVM Module: avm/res/network/private-dns-zone:0.8.1
// ============================================================================

@description('Required. Name of the private DNS zone (e.g. privatelink.blob.core.windows.net).')
param name string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Resource ID of the virtual network to link.')
param virtualNetworkResourceId string

module zone 'br/public:avm/res/network/private-dns-zone:0.8.1' = {
  name: take('avm.res.network.private-dns-zone.${replace(name, '.', '-')}', 64)
  params: {
    name: name
    tags: tags
    enableTelemetry: enableTelemetry
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetworkResourceId
        registrationEnabled: false
      }
    ]
  }
}

@description('Resource ID of the private DNS zone.')
output resourceId string = zone.outputs.resourceId

@description('Name of the private DNS zone.')
output name string = zone.outputs.name
