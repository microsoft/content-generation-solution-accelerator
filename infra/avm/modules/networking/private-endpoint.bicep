// ============================================================================
// Module: Private Endpoint
// Description: AVM wrapper for an Azure Private Endpoint with DNS zone group.
// AVM Module: avm/res/network/private-endpoint:0.12.0
// ============================================================================

@description('Required. Name of the private endpoint.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Resource ID of the subnet to deploy the private endpoint into.')
param subnetResourceId string

@description('Required. Resource ID of the target resource (private link service).')
param targetResourceId string

@description('Required. Group IDs (sub-resources) the private endpoint connects to.')
param groupIds array

@description('Optional. Private DNS zone group configurations.')
param privateDnsZoneConfigs array = []

module privateEndpoint 'br/public:avm/res/network/private-endpoint:0.12.0' = {
  name: take('avm.res.network.private-endpoint.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    subnetResourceId: subnetResourceId
    privateLinkServiceConnections: [
      {
        name: name
        properties: {
          privateLinkServiceId: targetResourceId
          groupIds: groupIds
        }
      }
    ]
    privateDnsZoneGroup: !empty(privateDnsZoneConfigs)
      ? {
          privateDnsZoneGroupConfigs: privateDnsZoneConfigs
        }
      : null
  }
}

@description('Resource ID of the private endpoint.')
output resourceId string = privateEndpoint.outputs.resourceId

@description('Name of the private endpoint.')
output name string = privateEndpoint.outputs.name
