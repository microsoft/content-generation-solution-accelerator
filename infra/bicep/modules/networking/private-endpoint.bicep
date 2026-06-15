// ============================================================================
// Module: Private Endpoint
// Description: Vanilla Bicep module for an Azure Private Endpoint with DNS zone group.
// Resource: Microsoft.Network/privateEndpoints@2024-05-01
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
// ============================================================================

@description('Required. Name of the private endpoint.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Resource ID of the subnet to deploy the private endpoint into.')
param subnetResourceId string

@description('Required. Resource ID of the target resource (private link service).')
param targetResourceId string

@description('Required. Group IDs (sub-resources) the private endpoint connects to.')
param groupIds array

@description('Optional. Private DNS zone group configurations. Each item: { name, privateDnsZoneResourceId }.')
param privateDnsZoneConfigs array = []

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetResourceId
    }
    privateLinkServiceConnections: [
      {
        name: name
        properties: {
          privateLinkServiceId: targetResourceId
          groupIds: groupIds
        }
      }
    ]
  }
}

resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = if (!empty(privateDnsZoneConfigs)) {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      for (config, i) in privateDnsZoneConfigs: {
        name: config.?name ?? 'config-${i}'
        properties: {
          privateDnsZoneId: config.privateDnsZoneResourceId
        }
      }
    ]
  }
}

@description('Resource ID of the private endpoint.')
output resourceId string = privateEndpoint.id

@description('Name of the private endpoint.')
output name string = privateEndpoint.name
