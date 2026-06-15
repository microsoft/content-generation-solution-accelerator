// ============================================================================
// Module: Application Insights
// Description: Vanilla Bicep module for an Azure Application Insights component.
// Resource: Microsoft.Insights/components@2020-02-02
// ============================================================================

@description('Required. Name of the Application Insights component.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Resource ID of the Log Analytics workspace to link.')
param workspaceResourceId string

resource component 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    RetentionInDays: 365
    DisableIpMasking: false
    IngestionMode: 'LogAnalytics'
    WorkspaceResourceId: workspaceResourceId
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('Resource ID of the Application Insights component.')
output resourceId string = component.id

@description('Name of the Application Insights component.')
output name string = component.name

@description('Connection string of the Application Insights component.')
output connectionString string = component.properties.ConnectionString
