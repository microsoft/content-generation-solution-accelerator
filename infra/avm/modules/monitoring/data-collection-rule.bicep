// ============================================================================
// Module: Data Collection Rule (Windows Security Events)
// Description: AVM wrapper for an Azure Monitor Data Collection Rule that
//              collects Windows Security audit events from the jumpbox VM
//              (SFI-AzTBv17 compliance).
// AVM Module: avm/res/insights/data-collection-rule:0.11.0
// ============================================================================

@description('Required. Name of the data collection rule.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Resource ID of the Log Analytics workspace destination.')
param workspaceResourceId string

@description('Optional. Name of the Log Analytics destination.')
param destinationName string = 'la-destination'

module dcr 'br/public:avm/res/insights/data-collection-rule:0.11.0' = {
  name: take('avm.res.insights.data-collection-rule.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    dataCollectionRuleProperties: {
      kind: 'Windows'
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
}

@description('Resource ID of the data collection rule.')
output resourceId string = dcr.outputs.resourceId

@description('Name of the data collection rule.')
output name string = dcr.outputs.name
