// ============================================================================
// Module: Data Collection Rule (Windows Security Events)
// Description: Vanilla Bicep module for an Azure Monitor Data Collection Rule that
//              collects Windows Security audit events from the jumpbox VM
//              (SFI-AzTBv17 compliance).
// Resource: Microsoft.Insights/dataCollectionRules@2023-03-11
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
// ============================================================================

@description('Required. Name of the data collection rule.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Resource ID of the Log Analytics workspace destination.')
param workspaceResourceId string

@description('Optional. Name of the Log Analytics destination.')
param destinationName string = 'la-destination'

resource dcr 'Microsoft.Insights/dataCollectionRules@2023-03-11' = {
  name: name
  location: location
  tags: tags
  kind: 'Windows'
  properties: {
    description: 'Collects Windows Security audit success/failure events from jumpbox VM (SFI-AzTBv17 compliance).'
    dataSources: {
      windowsEventLogs: [
        {
          name: 'securityEventLogsDataSource'
          streams: [
            'Microsoft-SecurityEvent'
          ]
          xPathQueries: [
            'Security!*[System[(band(Keywords,13510798882111488)) and (EventID != 4624)]]'
          ]
        }
      ]
    }
    destinations: {
      logAnalytics: [
        {
          name: destinationName
          workspaceResourceId: workspaceResourceId
        }
      ]
    }
    dataFlows: [
      {
        streams: [
          'Microsoft-SecurityEvent'
        ]
        destinations: [
          destinationName
        ]
      }
    ]
  }
}

@description('Resource ID of the data collection rule.')
output resourceId string = dcr.id

@description('Name of the data collection rule.')
output name string = dcr.name
