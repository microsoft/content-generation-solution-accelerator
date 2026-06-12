// ============================================================================
// Module: Cosmos DB (NoSQL)
// Description: AVM wrapper for an Azure Cosmos DB account (SQL/NoSQL API)
//              used for conversation history and product metadata.
// AVM Module: avm/res/document-db/database-account:0.19.0
// ============================================================================

@description('Required. Name of the Cosmos DB account.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Required. Name of the SQL database.')
param databaseName string

@description('Required. Containers to create in the SQL database.')
param containers array

@description('Required. Principal ID of the managed identity to grant data contributor.')
param principalId string

@description('Required. Principal ID of the deploying user/service principal.')
param deployerPrincipalId string

@description('Optional. Enable redundancy (zone redundancy + automatic failover).')
param enableRedundancy bool = false

@description('Optional. High-availability failover region used when redundancy is enabled.')
param haLocation string = ''

@description('Optional. Enable private networking (disables public access, adds private endpoint).')
param enablePrivateNetworking bool = false

@description('Optional. Subnet resource ID for the private endpoint.')
param subnetResourceId string = ''

@description('Optional. Resource ID of the Cosmos DB private DNS zone.')
param cosmosDnsZoneResourceId string = ''

@description('Optional. Diagnostic settings for monitoring.')
param diagnosticSettings array = []

module cosmos 'br/public:avm/res/document-db/database-account:0.19.0' = {
  name: take('avm.res.document-db.database-account.${name}', 64)
  params: {
    name: name
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    sqlDatabases: [
      {
        name: databaseName
        containers: containers
      }
    ]
    sqlRoleDefinitions: [
      {
        roleName: 'contentgen-data-contributor'
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
      }
    ]
    sqlRoleAssignments: [
      {
        principalId: principalId
        roleDefinitionId: '00000000-0000-0000-0000-000000000002' // Built-in Cosmos DB Data Contributor
      }
      {
        principalId: deployerPrincipalId
        roleDefinitionId: '00000000-0000-0000-0000-000000000002' // Built-in Cosmos DB Data Contributor to the deployer
      }
    ]
    diagnosticSettings: !empty(diagnosticSettings) ? diagnosticSettings : null
    networkRestrictions: {
      networkAclBypass: 'AzureServices'
      publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    }
    zoneRedundant: enableRedundancy
    capabilitiesToAdd: enableRedundancy ? null : ['EnableServerless']
    enableAutomaticFailover: enableRedundancy
    failoverLocations: enableRedundancy
      ? [
          {
            failoverPriority: 0
            isZoneRedundant: true
            locationName: location
          }
          {
            failoverPriority: 1
            isZoneRedundant: true
            locationName: haLocation
          }
        ]
      : [
          {
            locationName: location
            failoverPriority: 0
            isZoneRedundant: false
          }
        ]
    privateEndpoints: enablePrivateNetworking
      ? [
          {
            service: 'Sql'
            subnetResourceId: subnetResourceId
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                { privateDnsZoneResourceId: cosmosDnsZoneResourceId }
              ]
            }
          }
        ]
      : null
  }
}

@description('Resource ID of the Cosmos DB account.')
output resourceId string = cosmos.outputs.resourceId

@description('Name of the Cosmos DB account.')
output name string = cosmos.outputs.name
