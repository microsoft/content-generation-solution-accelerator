// ============================================================================
// Monitoring add-on (standalone deployment)
// ----------------------------------------------------------------------------
// Deploys Log Analytics Workspace + Application Insights into an EXISTING
// resource group, using the same naming convention as infra/main.bicep
// (`log-${solutionSuffix}` and `appi-${solutionSuffix}`).
//
// Use this when the main accelerator was deployed with `enableMonitoring=false`
// and you want to add monitoring afterwards WITHOUT re-running the full
// deployment.
//
// After this deployment completes, set the App Service / Container App
// `APPLICATIONINSIGHTS_CONNECTION_STRING` setting to the value emitted by the
// `applicationInsightsConnectionString` output (or run `azd env set` and
// re-deploy the app code only).
//
// Scope: resourceGroup
// ============================================================================

targetScope = 'resourceGroup'

@minLength(3)
@maxLength(15)
@description('Required. Same `solutionName` you passed to main.bicep / azd. Used to derive the resource names.')
param solutionName string

@description('Optional. Same `solutionUniqueText` used by main.bicep. Defaults to the same expression: substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5).')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@description('Optional. Azure region for the new resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Optional. Tags applied to both resources.')
param tags object = {}

@description('Optional. Data retention (days) for both Log Analytics and Application Insights.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 365

// Mirror the suffix logic from main.bicep so names line up exactly.
var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var logAnalyticsWorkspaceResourceName = 'log-${solutionSuffix}'
var applicationInsightsResourceName = 'appi-${solutionSuffix}'

// ========== Log Analytics Workspace ==========
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = {
  name: take('avm.res.operational-insights.workspace.${logAnalyticsWorkspaceResourceName}', 64)
  params: {
    name: logAnalyticsWorkspaceResourceName
    tags: tags
    location: location
    skuName: 'PerGB2018'
    dataRetention: retentionInDays
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
    diagnosticSettings: [{ useThisWorkspace: true }]
  }
}

// ========== Application Insights ==========
module applicationInsights 'br/public:avm/res/insights/component:0.7.1' = {
  name: take('avm.res.insights.component.${applicationInsightsResourceName}', 64)
  params: {
    name: applicationInsightsResourceName
    tags: tags
    location: location
    retentionInDays: retentionInDays
    kind: 'web'
    disableIpMasking: false
    flowType: 'Bluefield'
    workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
  }
}

@description('Resource ID of the Log Analytics workspace.')
output logAnalyticsWorkspaceResourceId string = logAnalyticsWorkspace.outputs.resourceId

@description('Name of the Log Analytics workspace.')
output logAnalyticsWorkspaceName string = logAnalyticsWorkspaceResourceName

@description('Resource ID of the Application Insights component.')
output applicationInsightsResourceId string = applicationInsights.outputs.resourceId

@description('Name of the Application Insights component.')
output applicationInsightsName string = applicationInsightsResourceName

@description('Connection string for Application Insights. Set this on your app as APPLICATIONINSIGHTS_CONNECTION_STRING.')
output applicationInsightsConnectionString string = applicationInsights.outputs.connectionString
