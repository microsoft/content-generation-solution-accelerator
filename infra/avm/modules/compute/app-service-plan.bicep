// ============================================================================
// Module: App Service Plan
// Description: AVM wrapper for an Azure App Service Plan (Linux).
// AVM Module: avm/res/web/serverfarm:0.7.0
// ============================================================================

@description('Required. Name of the App Service Plan.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. SKU name of the App Service Plan.')
param skuName string = 'B1'

@description('Optional. Number of instances.')
param skuCapacity int = 1

@description('Optional. Enable zone redundancy.')
param zoneRedundant bool = false

@description('Optional. Diagnostic settings for monitoring.')
param diagnosticSettings array = []

module serverFarm 'br/public:avm/res/web/serverfarm:0.7.0' = {
  name: take('avm.res.web.serverfarm.${name}', 64)
  params: {
    name: name
    tags: tags
    enableTelemetry: enableTelemetry
    location: location
    reserved: true
    kind: 'linux'
    diagnosticSettings: !empty(diagnosticSettings) ? diagnosticSettings : null
    skuName: skuName
    skuCapacity: skuCapacity
    zoneRedundant: zoneRedundant
  }
}

@description('Resource ID of the App Service Plan.')
output resourceId string = serverFarm.outputs.resourceId

@description('Name of the App Service Plan.')
output name string = serverFarm.outputs.name
