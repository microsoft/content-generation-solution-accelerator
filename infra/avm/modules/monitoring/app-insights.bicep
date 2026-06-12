// ============================================================================
// Module: Application Insights
// Description: AVM wrapper for Azure Application Insights component.
// AVM Module: avm/res/insights/component:0.7.1
// ============================================================================

@description('Required. Name of the Application Insights component.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Resource ID of the Log Analytics workspace to link.')
param workspaceResourceId string

module component 'br/public:avm/res/insights/component:0.7.1' = {
  name: take('avm.res.insights.component.${name}', 64)
  params: {
    name: name
    tags: tags
    location: location
    enableTelemetry: enableTelemetry
    retentionInDays: 365
    kind: 'web'
    disableIpMasking: false
    flowType: 'Bluefield'
    workspaceResourceId: workspaceResourceId
  }
}

@description('Resource ID of the Application Insights component.')
output resourceId string = component.outputs.resourceId

@description('Name of the Application Insights component.')
output name string = component.outputs.name

@description('Connection string of the Application Insights component.')
output connectionString string = component.outputs.connectionString
