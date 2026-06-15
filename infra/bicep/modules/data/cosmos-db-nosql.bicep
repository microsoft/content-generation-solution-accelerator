// ============================================================================
// Module: Cosmos DB (NoSQL)
// Description: Vanilla Bicep module for an Azure Cosmos DB account (SQL/NoSQL API)
//              used for conversation history and product metadata.
// Resource: Microsoft.DocumentDB/databaseAccounts@2024-11-15
// ============================================================================

@description('Required. Name of the Cosmos DB account.')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Name of the SQL database.')
param databaseName string

@description('Required. Containers to create in the SQL database. Each item: { name, paths }.')
param containers array

@description('Required. Principal ID of the managed identity to grant data contributor.')
param principalId string

@description('Required. Principal ID of the deploying user/service principal.')
param deployerPrincipalId string

var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002' // Built-in Cosmos DB Data Contributor

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: name
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    enableAutomaticFailover: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    publicNetworkAccess: 'Enabled'
    networkAclBypass: 'AzureServices'
  }
}

resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmos
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource sqlContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = [
  for container in containers: {
    parent: sqlDatabase
    name: container.name
    properties: {
      resource: {
        id: container.name
        partitionKey: {
          paths: container.paths
          kind: 'Hash'
        }
      }
    }
  }
]

resource dataContributorRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, 'contentgen-data-contributor')
  properties: {
    roleName: 'contentgen-data-contributor'
    type: 'CustomRole'
    assignableScopes: [
      cosmos.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
      }
    ]
  }
}

resource identityRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, principalId, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: principalId
    scope: cosmos.id
  }
}

resource deployerRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, deployerPrincipalId, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: deployerPrincipalId
    scope: cosmos.id
  }
}

@description('Resource ID of the Cosmos DB account.')
output resourceId string = cosmos.id

@description('Name of the Cosmos DB account.')
output name string = cosmos.name
