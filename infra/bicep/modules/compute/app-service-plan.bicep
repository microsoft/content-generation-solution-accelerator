// ============================================================================
// Module: App Service Plan
// Description: Vanilla Bicep module for an Azure App Service Plan (Linux).
// Resource: Microsoft.Web/serverfarms@2024-04-01
// ============================================================================

@description('Required. Name of the App Service Plan.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Optional. SKU name of the App Service Plan.')
param skuName string = 'B1'

@description('Optional. Number of instances.')
param skuCapacity int = 1

resource serverFarm 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    reserved: true
  }
}

@description('Resource ID of the App Service Plan.')
output resourceId string = serverFarm.id

@description('Name of the App Service Plan.')
output name string = serverFarm.name
