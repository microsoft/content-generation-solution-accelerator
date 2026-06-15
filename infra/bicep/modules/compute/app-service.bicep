@description('Required. Name of the site.')
param name string

@description('Optional. Location for all Resources.')
param location string = resourceGroup().location

@description('Required. Type of site to deploy.')
@allowed([
  'functionapp'
  'functionapp,linux'
  'functionapp,workflowapp'
  'functionapp,workflowapp,linux'
  'functionapp,linux,container'
  'functionapp,linux,container,azurecontainerapps'
  'app,linux'
  'app'
  'linux,api'
  'api'
  'app,linux,container'
  'app,container,windows'
])
param kind string

@description('Required. The resource ID of the app service plan to use for the site.')
param serverFarmResourceId string

@description('Optional. Configures a site to accept only HTTPS requests.')
param httpsOnly bool = true

@description('Optional. If client affinity is enabled.')
param clientAffinityEnabled bool = true

@description('Optional. The managed identity definition for this resource.')
param managedIdentities {
  @description('Optional. Enables system assigned managed identity on the resource.')
  systemAssigned: bool?

  @description('Optional. The resource ID(s) to assign to the resource.')
  userAssignedResourceIds: string[]?
}?

@description('Optional. The resource ID of the assigned identity to be used to access a key vault with.')
param keyVaultAccessIdentityResourceId string?

@description('Optional. Checks if Customer provided storage account is required.')
param storageAccountRequired bool = false

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Optional. The site config object.')
param siteConfig resourceInput<'Microsoft.Web/sites@2025-03-01'>.properties.siteConfig = {
  alwaysOn: true
  minTlsVersion: '1.2'
  ftpsState: 'FtpsOnly'
}

@description('Optional. The web site config.')
param configs appSettingsConfigType[]?

@description('Optional. Tags of the resource.')
param tags object?

@description('Optional. Whether or not public network access is allowed for this resource.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string?

@description('Optional. End to End Encryption Setting.')
param e2eEncryptionEnabled bool?

var formattedUserAssignedIdentities = reduce(
  map((managedIdentities.?userAssignedResourceIds ?? []), (id) => { '${id}': {} }),
  {},
  (cur, next) => union(cur, next)
)

var identity = !empty(managedIdentities)
  ? {
      type: (managedIdentities.?systemAssigned ?? false)
        ? (!empty(managedIdentities.?userAssignedResourceIds ?? {}) ? 'SystemAssigned, UserAssigned' : 'SystemAssigned')
        : (!empty(managedIdentities.?userAssignedResourceIds ?? {}) ? 'UserAssigned' : 'None')
      userAssignedIdentities: !empty(formattedUserAssignedIdentities) ? formattedUserAssignedIdentities : null
    }
  : null

resource app 'Microsoft.Web/sites@2025-03-01' = {
  name: name
  location: location
  kind: kind
  tags: tags
  identity: identity
  properties: {
    serverFarmId: serverFarmResourceId
    clientAffinityEnabled: clientAffinityEnabled
    httpsOnly: httpsOnly
    storageAccountRequired: storageAccountRequired
    keyVaultReferenceIdentity: keyVaultAccessIdentityResourceId
    siteConfig: siteConfig
    publicNetworkAccess: !empty(publicNetworkAccess) ? any(publicNetworkAccess) : 'Enabled'
    endToEndEncryptionEnabled: e2eEncryptionEnabled
  }
}

module app_config 'app-service.config.bicep' = [
  for (config, index) in (configs ?? []): {
    name: '${uniqueString(deployment().name, location)}-Site-Config-${index}'
    params: {
      appName: app.name
      name: config.name
      applicationInsightResourceId: config.?applicationInsightResourceId
      storageAccountResourceId: config.?storageAccountResourceId
      storageAccountUseIdentityAuthentication: config.?storageAccountUseIdentityAuthentication
      properties: config.?properties
      currentAppSettings: config.?retainCurrentAppSettings ?? true && config.name == 'appsettings'
        ? list('${app.id}/config/appsettings', '2023-12-01').properties
        : {}
    }
  }
]

@description('The name of the site.')
output name string = app.name

@description('The resource ID of the site.')
output resourceId string = app.id

@description('The resource group the site was deployed into.')
output resourceGroupName string = resourceGroup().name

@description('The principal ID of the system assigned identity.')
output systemAssignedMIPrincipalId string? = app.?identity.?principalId

@description('The location the resource was deployed into.')
output location string = app.location

@description('Default hostname of the app.')
output defaultHostname string = 'https://${name}.azurewebsites.net'

@description('Unique identifier that verifies the custom domains assigned to the app.')
output customDomainVerificationId string = app.properties.customDomainVerificationId

@description('The outbound IP addresses of the app.')
output outboundIpAddresses string = app.properties.outboundIpAddresses

// ================ //
// Definitions      //
// ================ //
@export()
@description('The type of an app settings configuration.')
type appSettingsConfigType = {
  @description('Required. The type of config.')
  name: 'appsettings' | 'logs'

  @description('Optional. If the provided storage account requires Identity based authentication.')
  storageAccountUseIdentityAuthentication: bool?

  @description('Optional. Required if app of kind functionapp. Resource ID of the storage account to manage triggers and logging function executions.')
  storageAccountResourceId: string?

  @description('Optional. Resource ID of the application insight to leverage for this resource.')
  applicationInsightResourceId: string?

  @description('Optional. The retain the current app settings. Defaults to true.')
  retainCurrentAppSettings: bool?

  @description('Optional. The app settings key-value pairs.')
  properties: {
    @description('Required. An app settings key-value pair.')
    *: string
  }?
}
