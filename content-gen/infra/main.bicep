// ========== main.bicep ========== //
targetScope = 'resourceGroup'

metadata name = 'Intelligent Content Generation Accelerator'
metadata description = '''Solution Accelerator for multimodal marketing content generation using Microsoft Agent Framework.
'''

@minLength(3)
@maxLength(15)
@description('Optional. A unique application/solution name for all resources in this deployment.')
param solutionName string = 'contentgen'

@maxLength(5)
@description('Optional. A unique text value for the solution.')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@allowed([
  'australiaeast'
  'centralus'
  'eastasia'
  'eastus'
  'eastus2'
  'japaneast'
  'northeurope'
  'southeastasia'
  'swedencentral'
  'uksouth'
  'westus'
  'westus3'
])
@metadata({ azd: { type: 'location' } })
@description('Required. Azure region for all services.')
param location string

@minLength(3)
@description('Optional. Secondary location for databases creation.')
param secondaryLocation string = 'uksouth'

@description('Optional. Location for AI deployments. If not specified, uses the main location.')
param azureAiServiceLocation string = ''

@minLength(1)
@allowed([
  'Standard'
  'GlobalStandard'
])
@description('Optional. GPT model deployment type.')
param gptModelDeploymentType string = 'GlobalStandard'

@minLength(1)
@description('Optional. Name of the GPT model to deploy.')
param gptModelName string = 'gpt-5.1'

@description('Optional. Version of the GPT model to deploy.')
param gptModelVersion string = '2025-11-13'

@description('Optional. Image model to deploy: gpt-image-1, gpt-image-1.5, dall-e-3, or none to skip.')
@allowed([
  'gpt-image-1'
  'gpt-image-1.5'
  'dall-e-3'
  'none'
])
param imageModelChoice string = 'gpt-image-1'

@description('Optional. API version for Azure OpenAI service.')
param azureOpenaiAPIVersion string = '2025-01-01-preview'

@description('Optional. API version for Azure AI Agent service.')
param azureAiAgentApiVersion string = '2025-05-01'

@minValue(10)
@description('Optional. AI model deployment token capacity.')
param gptModelCapacity int = 150

@minValue(1)
@description('Optional. Image model deployment capacity (RPM).')
param dalleModelCapacity int = 1

@description('Optional. Existing Log Analytics Workspace Resource ID.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. Resource ID of an existing Foundry project.')
param azureExistingAIProjectResourceId string = ''

@description('Optional. Deploy Azure Bastion and Jumpbox VM for private network administration.')
param deployBastionAndJumpbox bool = false

@description('Optional. The tags to apply to all deployed Azure resources.')
param tags object = {}

@description('Optional. Enable monitoring for applicable resources (WAF-aligned).')
param enableMonitoring bool = false

@description('Optional. Enable Azure AI Foundry mode for multi-agent orchestration.')
param useFoundryMode bool = true

@description('Optional. Enable scalability for applicable resources (WAF-aligned).')
param enableScalability bool = false

@description('Optional. Enable redundancy for applicable resources (WAF-aligned).')
param enableRedundancy bool = false

@description('Optional. Enable private networking for applicable resources (WAF-aligned).')
param enablePrivateNetworking bool = false

@description('Required. The existing Container Registry name (without .azurecr.io). Must contain pre-built images: content-gen-app and content-gen-api.')
param acrName string = 'contentgencontainerreg'

@description('Optional. Image Tag.')
param imageTag string = 'latest'

@description('Optional. Enable/Disable usage telemetry.')
param enableTelemetry bool = true

@description('Optional. Created by user name.')
param createdBy string = contains(deployer(), 'userPrincipalName')? split(deployer().userPrincipalName, '@')[0]: deployer().objectId

// ============== //
// Variables      //
// ============== //

var solutionLocation = empty(location) ? resourceGroup().location : location

// Regions that support GPT-5.1, GPT-Image-1, and text-embedding models with GlobalStandard SKU
// Update this list as Azure expands model availability
var validAiServiceRegions = [
  'australiaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'japaneast'
  'koreacentral'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westus'
  'westus3'
]

// Map regions to recommended AI service regions (for when main region lacks model support)
var aiServiceRegionFallback = {
  australiaeast: 'australiaeast'
  australiasoutheast: 'australiaeast'
  brazilsouth: 'eastus2'
  canadacentral: 'eastus2'
  canadaeast: 'eastus2'
  centralindia: 'uksouth'
  centralus: 'eastus2'
  eastasia: 'japaneast'
  eastus: 'eastus'
  eastus2: 'eastus2'
  francecentral: 'francecentral'
  germanywestcentral: 'swedencentral'
  japaneast: 'japaneast'
  japanwest: 'japaneast'
  koreacentral: 'koreacentral'
  koreasouth: 'koreacentral'
  northcentralus: 'eastus2'
  northeurope: 'swedencentral'
  norwayeast: 'swedencentral'
  polandcentral: 'swedencentral'
  qatarcentral: 'uaenorth'
  southafricanorth: 'uksouth'
  southcentralus: 'eastus2'
  southeastasia: 'japaneast'
  southindia: 'uksouth'
  swedencentral: 'swedencentral'
  switzerlandnorth: 'switzerlandnorth'
  uaenorth: 'uaenorth'
  uksouth: 'uksouth'
  ukwest: 'uksouth'
  westcentralus: 'westus'
  westeurope: 'swedencentral'
  westindia: 'uksouth'
  westus: 'westus'
  westus2: 'westus'
  westus3: 'westus3'
}

// Determine effective AI service location:
// 1. If explicitly set via parameter, use that (user override)
// 2. If main location is valid for AI services, use it
// 3. Otherwise, use the fallback mapping
var requestedAiLocation = empty(azureAiServiceLocation) ? solutionLocation : azureAiServiceLocation
var aiServiceLocation = contains(validAiServiceRegions, requestedAiLocation) 
  ? requestedAiLocation 
  : (aiServiceRegionFallback[?solutionLocation] ?? 'eastus2')

// acrName is required - points to existing ACR with pre-built images
var acrResourceName = acrName
var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var cosmosDbZoneRedundantHaRegionPairs = {
  australiaeast: 'uksouth'
  centralus: 'eastus2'
  eastasia: 'southeastasia'
  eastus: 'centralus'
  eastus2: 'centralus'
  japaneast: 'australiaeast'
  northeurope: 'westeurope'
  southeastasia: 'eastasia'
  uksouth: 'westeurope'
  westus: 'westus3'
  westus3: 'westus'
}
var cosmosDbHaLocation = cosmosDbZoneRedundantHaRegionPairs[?resourceGroup().location] ?? secondaryLocation

var replicaRegionPairs = {
  australiaeast: 'australiasoutheast'
  centralus: 'westus'
  eastasia: 'japaneast'
  eastus: 'centralus'
  eastus2: 'centralus'
  japaneast: 'eastasia'
  northeurope: 'westeurope'
  southeastasia: 'eastasia'
  uksouth: 'westeurope'
  westus: 'westus3'
  westus3: 'westus'
}
var replicaLocation = replicaRegionPairs[?resourceGroup().location] ?? secondaryLocation

var azureSearchIndex = 'products'
var aiSearchName = 'srch-${solutionSuffix}'
var aiSearchConnectionName = 'foundry-search-connection-${solutionSuffix}'

// Extracts subscription, resource group, and workspace name from the resource ID
var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)
var useExistingAiFoundryAiProject = !empty(azureExistingAIProjectResourceId)
var aiFoundryAiServicesResourceGroupName = useExistingAiFoundryAiProject
  ? split(azureExistingAIProjectResourceId, '/')[4]
  : 'rg-${solutionSuffix}'
// var aiFoundryAiServicesSubscriptionId = useExistingAiFoundryAiProject
//   ? split(azureExistingAIProjectResourceId, '/')[2]
//   : subscription().id
var aiFoundryAiServicesResourceName = useExistingAiFoundryAiProject
  ? split(azureExistingAIProjectResourceId, '/')[8]
  : 'aif-${solutionSuffix}'
var aiFoundryAiProjectResourceName = useExistingAiFoundryAiProject
  ? split(azureExistingAIProjectResourceId, '/')[10]
  : 'proj-${solutionSuffix}'

// Base model deployments (GPT only - no embeddings needed for content generation)
var baseModelDeployments = [
  {
    format: 'OpenAI'
    name: gptModelName
    model: gptModelName
    sku: {
      name: gptModelDeploymentType
      capacity: gptModelCapacity
    }
    version: gptModelVersion
    raiPolicyName: 'Microsoft.Default'
  }
]

// Image model configuration based on choice
var imageModelConfig = {
  'gpt-image-1': {
    name: 'gpt-image-1'
    version: '2025-04-15'
    sku: 'GlobalStandard'
  }
  'gpt-image-1.5': {
    name: 'gpt-image-1.5'
    version: '2025-12-16'
    sku: 'GlobalStandard'
  }
  'dall-e-3': {
    name: 'dall-e-3'
    version: '3.0'
    sku: 'Standard'
  }
  none: {
    name: ''
    version: ''
    sku: ''
  }
}

// Image model deployment (optional)
var imageModelDeployment = imageModelChoice != 'none' ? [
  {
    format: 'OpenAI'
    name: imageModelConfig[imageModelChoice].name
    model: imageModelConfig[imageModelChoice].name
    sku: {
      name: imageModelConfig[imageModelChoice].sku
      capacity: dalleModelCapacity
    }
    version: imageModelConfig[imageModelChoice].version
    raiPolicyName: 'Microsoft.Default'
  }
] : []

// Combine deployments based on imageModelChoice
var aiFoundryAiServicesModelDeployment = concat(baseModelDeployments, imageModelDeployment)

var aiFoundryAiProjectDescription = 'Content Generation AI Foundry Project'

// ============== //
// Resources      //
// ============== //

#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry) {
  name: '46d3xbcp.ptn.sa-contentgen.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, solutionLocation), 0, 4)}'
  properties: {
    mode: 'Incremental'
    template: {
      '$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
      contentVersion: '1.0.0.0'
      resources: []
      outputs: {
        telemetry: {
          type: 'String'
          value: 'For more information, see https://aka.ms/avm/TelemetryInfo'
        }
      }
    }
  }
}

// ========== Resource Group Tag ========== //
resource resourceGroupTags 'Microsoft.Resources/tags@2021-04-01' = {
  name: 'default'
  properties: {
    tags: {
      ...resourceGroup().tags
      ... tags
      TemplateName: 'ContentGen'
      Type: enablePrivateNetworking ? 'WAF' : 'Non-WAF'
      CreatedBy: createdBy
    }
  }
}

// ========== Log Analytics Workspace ========== //
var logAnalyticsWorkspaceResourceName = 'log-${solutionSuffix}'
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.14.2' = if (enableMonitoring && !useExistingLogAnalytics) {
  name: take('avm.res.operational-insights.workspace.${logAnalyticsWorkspaceResourceName}', 64)
  params: {
    name: logAnalyticsWorkspaceResourceName
    tags: tags
    location: solutionLocation
    enableTelemetry: enableTelemetry
    skuName: 'PerGB2018'
    dataRetention: 365
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
    diagnosticSettings: [{ useThisWorkspace: true }]
    dailyQuotaGb: enableRedundancy ? 10 : null
    replication: enableRedundancy
      ? {
          enabled: true
          location: replicaLocation
        }
      : null
    publicNetworkAccessForIngestion: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    publicNetworkAccessForQuery: enablePrivateNetworking ? 'Disabled' : 'Enabled'
  }
}
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics 
  ? existingLogAnalyticsWorkspaceId 
  : (enableMonitoring ? logAnalyticsWorkspace!.outputs.resourceId : '')

// ========== Application Insights ========== //
var applicationInsightsResourceName = 'appi-${solutionSuffix}'
module applicationInsights 'br/public:avm/res/insights/component:0.7.1' = if (enableMonitoring) {
  name: take('avm.res.insights.component.${applicationInsightsResourceName}', 64)
  params: {
    name: applicationInsightsResourceName
    tags: tags
    location: solutionLocation
    enableTelemetry: enableTelemetry
    retentionInDays: 365
    kind: 'web'
    disableIpMasking: false
    flowType: 'Bluefield'
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
  }
}

// ========== User Assigned Identity ========== //
var userAssignedIdentityResourceName = 'id-${solutionSuffix}'
module userAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.3' = {
  name: take('avm.res.managed-identity.user-assigned-identity.${userAssignedIdentityResourceName}', 64)
  params: {
    name: userAssignedIdentityResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// ========== Virtual Network and Networking Components ========== //
module virtualNetwork 'modules/virtualNetwork.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtualNetwork.${solutionSuffix}', 64)
  params: {
    vnetName: 'vnet-${solutionSuffix}'
    vnetLocation: solutionLocation
    vnetAddressPrefixes: ['10.0.0.0/20']
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceResourceId
    enableTelemetry: enableTelemetry
    resourceSuffix: solutionSuffix
    deployBastionAndJumpbox: deployBastionAndJumpbox
  }
  dependsOn: enableMonitoring ? [logAnalyticsWorkspace] : []
}

// ========== Private DNS Zones ========== //
// Only create DNS zones for resources that need private endpoints:
// - Cognitive Services (for AI Services)
// - OpenAI (for Azure OpenAI endpoints)
// - Blob Storage
// - Cosmos DB (Documents)
var privateDnsZones = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.blob.${environment().suffixes.storage}'
  'privatelink.documents.azure.com'
]

var dnsZoneIndex = {
  cognitiveServices: 0
  openAI: 1
  storageBlob: 2
  cosmosDB: 3
}

@batchSize(5)
module avmPrivateDnsZones 'br/public:avm/res/network/private-dns-zone:0.8.0' = [
  for (zone, i) in privateDnsZones: if (enablePrivateNetworking) {
    name: take('avm.res.network.private-dns-zone.${replace(zone, '.', '-')}', 64)
    params: {
      name: zone
      tags: tags
      enableTelemetry: enableTelemetry
      virtualNetworkLinks: [
        {
          virtualNetworkResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.resourceId : ''
          registrationEnabled: false
        }
      ]
    }
  }
]

// ========== AI Foundry: AI Services ========== //
module aiFoundryAiServices 'br/public:avm/res/cognitive-services/account:0.14.0' = if (!useExistingAiFoundryAiProject) {
  name: take('avm.res.cognitive-services.account.${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: aiFoundryAiServicesResourceName
    location: aiServiceLocation
    tags: tags
    sku: 'S0'
    kind: 'AIServices'
    disableLocalAuth: true
    allowProjectManagement: true
    customSubDomainName: aiFoundryAiServicesResourceName
    restrictOutboundNetworkAccess: false
    deployments: [
      for deployment in aiFoundryAiServicesModelDeployment: {
        name: deployment.name
        model: {
          format: deployment.format
          name: deployment.name
          version: deployment.version
        }
        raiPolicyName: deployment.raiPolicyName
        sku: {
          name: deployment.sku.name
          capacity: deployment.sku.capacity
        }
      }
    ]
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    managedIdentities: { 
      userAssignedResourceIds: [userAssignedIdentity!.outputs.resourceId] 
    }
    roleAssignments: [
      {
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
        principalId: userAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
        principalId: userAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
        principalId: userAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User for deployer
        principalId: deployer().objectId
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    // Note: Private endpoint is created separately to avoid timing issues with model deployments
  }
}

// Create private endpoint for AI Services AFTER the account is fully provisioned
module aiServicesPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.0' = if (!useExistingAiFoundryAiProject && enablePrivateNetworking) {
  name: take('pep-ai-services-${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: 'pep-${aiFoundryAiServicesResourceName}'
    location: solutionLocation
    tags: tags
    subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
    privateLinkServiceConnections: [
      {
        name: 'pep-${aiFoundryAiServicesResourceName}'
        properties: {
          privateLinkServiceId: aiFoundryAiServices!.outputs.resourceId
          groupIds: ['account']
        }
      }
    ]
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        { 
          name: 'cognitiveservices'
          privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cognitiveServices]!.outputs.resourceId 
        }
        { 
          name: 'openai'
          privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.openAI]!.outputs.resourceId 
        }
      ]
    }
  }
}

module aiFoundryAiServicesProject 'modules/ai-project.bicep' = if (!useExistingAiFoundryAiProject) {
  name: take('module.ai-project.${aiFoundryAiProjectResourceName}', 64)
  params: {
    name: aiFoundryAiProjectResourceName
    location: aiServiceLocation
    tags: tags
    desc: aiFoundryAiProjectDescription
    aiServicesName: aiFoundryAiServicesResourceName
    azureExistingAIProjectResourceId: azureExistingAIProjectResourceId
  }
  dependsOn: [
    aiFoundryAiServices
  ]
}

var aiFoundryAiProjectEndpoint = useExistingAiFoundryAiProject
  ? 'https://${aiFoundryAiServicesResourceName}.services.ai.azure.com/api/projects/${aiFoundryAiProjectResourceName}'
  : aiFoundryAiServicesProject!.outputs.apiEndpoint

// ========== AI Search ========== //
module aiSearch 'br/public:avm/res/search/search-service:0.11.1' = {
  name: take('avm.res.search.search-service.${aiSearchName}', 64)
  params: {
    name: aiSearchName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    sku: enableScalability ? 'standard' : 'basic'
    replicaCount: enableRedundancy ? 2 : 1
    partitionCount: 1
    hostingMode: 'default'
    semanticSearch: 'free'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    roleAssignments: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
      }
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    // AI Search remains publicly accessible - accessed from ACI via managed identity
    publicNetworkAccess: 'Enabled'
  }
}

// ========== AI Search Connection to AI Services ========== //
resource aiSearchFoundryConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = if (!useExistingAiFoundryAiProject) {
  name: '${aiFoundryAiServicesResourceName}/${aiFoundryAiProjectResourceName}/${aiSearchConnectionName}'
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${aiSearchName}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiVersion: '2024-05-01-preview'
      ResourceId: aiSearch.outputs.resourceId
    }
  }
  dependsOn: [aiFoundryAiServicesProject]
}

// ========== Storage Account ========== //
var storageAccountName = 'st${solutionSuffix}'
var productImagesContainer = 'product-images'
var generatedImagesContainer = 'generated-images'
var dataContainer = 'data'

module storageAccount 'br/public:avm/res/storage/storage-account:0.30.0' = {
  name: take('avm.res.storage.storage-account.${storageAccountName}', 64)
  params: {
    name: storageAccountName
    location: solutionLocation
    skuName: enableRedundancy ? 'Standard_ZRS' : 'Standard_LRS'
    managedIdentities: { systemAssigned: true }
    minimumTlsVersion: 'TLS1_2'
    enableTelemetry: enableTelemetry
    tags: tags
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    blobServices: {
      containerDeleteRetentionPolicyEnabled: true
      containerDeleteRetentionPolicyDays: 7
      deleteRetentionPolicyEnabled: true
      deleteRetentionPolicyDays: 7
      containers: [
        {
          name: productImagesContainer
          publicAccess: 'None'
        }
        {
          name: generatedImagesContainer
          publicAccess: 'None'
        }
        {
          name: dataContainer
          publicAccess: 'None'
        }
      ]
    }
    roleAssignments: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
      }
    ]
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: enablePrivateNetworking ? 'Deny' : 'Allow'
    }
    allowBlobPublicAccess: false
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    privateEndpoints: enablePrivateNetworking ? [
      {
        service: 'blob'
        subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.storageBlob]!.outputs.resourceId }
          ]
        }
      }
    ] : null
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
  }
}

// ========== Cosmos DB ========== //
var cosmosDBResourceName = 'cosmos-${solutionSuffix}'
var cosmosDBDatabaseName = 'content_generation_db'
var cosmosDBConversationsContainer = 'conversations'
var cosmosDBProductsContainer = 'products'

module cosmosDB 'br/public:avm/res/document-db/database-account:0.18.0' = {
  name: take('avm.res.document-db.database-account.${cosmosDBResourceName}', 64)
  params: {
    name: 'cosmos-${solutionSuffix}'
    location: secondaryLocation
    tags: tags
    enableTelemetry: enableTelemetry
    sqlDatabases: [
      {
        name: cosmosDBDatabaseName
        containers: [
          {
            name: cosmosDBConversationsContainer
            paths: [
              '/userId'
            ]
          }
          {
            name: cosmosDBProductsContainer
            paths: [
              '/category'
            ]
          }
        ]
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
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionId: '00000000-0000-0000-0000-000000000002' // Built-in Cosmos DB Data Contributor
      }
      {
        principalId: deployer().objectId
        roleDefinitionId: '00000000-0000-0000-0000-000000000002' // Built-in Cosmos DB Data Contributor to the deployer
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
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
            locationName: secondaryLocation
          }
          {
            failoverPriority: 1
            isZoneRedundant: true
            locationName: cosmosDbHaLocation
          }
        ]
      : [
          {
            locationName: secondaryLocation
            failoverPriority: 0
            isZoneRedundant: false
          }
        ]
    privateEndpoints: enablePrivateNetworking ? [
      {
        service: 'Sql'
        subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cosmosDB]!.outputs.resourceId }
          ]
        }
      }
    ] : null
  }
}

// ========== App Service Plan ========== //
var webServerFarmResourceName = 'asp-${solutionSuffix}'
module webServerFarm 'br/public:avm/res/web/serverfarm:0.5.0' = {
  name: take('avm.res.web.serverfarm.${webServerFarmResourceName}', 64)
  params: {
    name: webServerFarmResourceName
    tags: tags
    enableTelemetry: enableTelemetry
    location: solutionLocation
    reserved: true
    kind: 'linux'
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    skuName: enableScalability || enableRedundancy ? 'P1v3' : 'B1'
    skuCapacity: 1
    zoneRedundant: enableRedundancy ? true : false
  }
  scope: resourceGroup(resourceGroup().name)
}

// ========== Web App ========== //
var webSiteResourceName = 'app-${solutionSuffix}'
// Backend URL: Use ACI IP (private or public) or FQDN depending on networking mode
var aciPrivateIpFallback = '10.0.4.4'
var aciPublicFqdnFallback = '${containerInstanceName}.${solutionLocation}.azurecontainer.io'
// For private networking use IP, for public use FQDN
var aciBackendUrl = enablePrivateNetworking 
  ? 'http://${aciPrivateIpFallback}:8000'
  : 'http://${aciPublicFqdnFallback}:8000'
module webSite 'modules/web-sites.bicep' = {
  name: take('module.web-sites.${webSiteResourceName}', 64)
  params: {
    name: webSiteResourceName
    tags: tags
    location: solutionLocation
    kind: 'app,linux,container'
    serverFarmResourceId: webServerFarm.outputs.resourceId
    managedIdentities: { userAssignedResourceIds: [userAssignedIdentity!.outputs.resourceId] }
    siteConfig: {
      // Frontend container - same for both modes
      linuxFxVersion: 'DOCKER|${acrResourceName}.azurecr.io/content-gen-app:${imageTag}'
      minTlsVersion: '1.2'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
    }
    virtualNetworkSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.webSubnetResourceId : null
    configs: concat([
      {
        // Frontend container proxies to ACI backend (both modes)
        name: 'appsettings'
        properties: {
          DOCKER_REGISTRY_SERVER_URL: 'https://${acrResourceName}.azurecr.io'
          BACKEND_URL: aciBackendUrl
          AZURE_CLIENT_ID: userAssignedIdentity.outputs.clientId
        }
        applicationInsightResourceId: enableMonitoring ? applicationInsights!.outputs.resourceId : null
      }
    ], enableMonitoring ? [
      {
        name: 'logs'
        properties: {}
      }
    ] : [])
    enableMonitoring: enableMonitoring
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    vnetRouteAllEnabled: enablePrivateNetworking
    vnetImagePullEnabled: enablePrivateNetworking
    publicNetworkAccess: 'Enabled'
  }
}

// ========== Container Instance (Backend API) ========== //
var containerInstanceName = 'aci-${solutionSuffix}'
module containerInstance 'modules/container-instance.bicep' = {
  name: take('module.container-instance.${containerInstanceName}', 64)
  params: {
    name: containerInstanceName
    location: solutionLocation
    tags: tags
    containerImage: '${acrResourceName}.azurecr.io/content-gen-api:${imageTag}'
    cpu: 2
    memoryInGB: 4
    port: 8000
    // Only pass subnetResourceId when private networking is enabled
    subnetResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.aciSubnetResourceId : ''
    registryServer: '${acrResourceName}.azurecr.io'
    userAssignedIdentityResourceId: userAssignedIdentity.outputs.resourceId
    enableTelemetry: enableTelemetry
    environmentVariables: [
      // Azure OpenAI Settings
      { name: 'AZURE_OPENAI_ENDPOINT', value: 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' }
      { name: 'AZURE_OPENAI_GPT_MODEL', value: gptModelName }
      { name: 'AZURE_OPENAI_IMAGE_MODEL', value: imageModelConfig[imageModelChoice].name }
      { name: 'AZURE_OPENAI_GPT_IMAGE_ENDPOINT', value: imageModelChoice != 'none' ? 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' : '' }
      { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenaiAPIVersion }
      // Azure Cosmos DB Settings
      { name: 'AZURE_COSMOS_ENDPOINT', value: 'https://cosmos-${solutionSuffix}.documents.azure.com:443/' }
      { name: 'AZURE_COSMOS_DATABASE_NAME', value: cosmosDBDatabaseName }
      { name: 'AZURE_COSMOS_PRODUCTS_CONTAINER', value: cosmosDBProductsContainer }
      { name: 'AZURE_COSMOS_CONVERSATIONS_CONTAINER', value: cosmosDBConversationsContainer }
      // Azure Blob Storage Settings
      { name: 'AZURE_BLOB_ACCOUNT_NAME', value: storageAccountName }
      { name: 'AZURE_BLOB_PRODUCT_IMAGES_CONTAINER', value: productImagesContainer }
      { name: 'AZURE_BLOB_GENERATED_IMAGES_CONTAINER', value: generatedImagesContainer }
      // Azure AI Search Settings
      { name: 'AZURE_AI_SEARCH_ENDPOINT', value: 'https://${aiSearchName}.search.windows.net' }
      { name: 'AZURE_AI_SEARCH_PRODUCTS_INDEX', value: azureSearchIndex }
      { name: 'AZURE_AI_SEARCH_IMAGE_INDEX', value: 'product-images' }
      // App Settings
      { name: 'AZURE_CLIENT_ID', value: userAssignedIdentity.outputs.clientId }
      { name: 'PORT', value: '8000' }
      { name: 'WORKERS', value: '4' }
      { name: 'RUNNING_IN_PRODUCTION', value: 'true' }
      // Azure AI Foundry Settings
      { name: 'USE_FOUNDRY', value: useFoundryMode ? 'true' : 'false' }
      { name: 'AZURE_AI_PROJECT_ENDPOINT', value: aiFoundryAiProjectEndpoint }
      { name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME', value: gptModelName }
      { name: 'AZURE_AI_IMAGE_MODEL_DEPLOYMENT', value: imageModelConfig[imageModelChoice].name }
    ]
  }
}

// ========== Outputs ========== //
@description('Contains App Service Name')
output APP_SERVICE_NAME string = webSite.outputs.name

@description('Contains WebApp URL')
output WEB_APP_URL string = 'https://${webSite.outputs.name}.azurewebsites.net'

@description('Contains Storage Account Name')
output AZURE_BLOB_ACCOUNT_NAME string = storageAccount.outputs.name

@description('Contains Product Images Container')
output AZURE_BLOB_PRODUCT_IMAGES_CONTAINER string = productImagesContainer

@description('Contains Generated Images Container')
output AZURE_BLOB_GENERATED_IMAGES_CONTAINER string = generatedImagesContainer

@description('Contains CosmosDB Account Name')
output COSMOSDB_ACCOUNT_NAME string = cosmosDB.outputs.name

@description('Contains CosmosDB Endpoint URL')
output AZURE_COSMOS_ENDPOINT string = 'https://cosmos-${solutionSuffix}.documents.azure.com:443/'

@description('Contains CosmosDB Database Name')
output AZURE_COSMOS_DATABASE_NAME string = cosmosDBDatabaseName

@description('Contains CosmosDB Products Container')
output AZURE_COSMOS_PRODUCTS_CONTAINER string = cosmosDBProductsContainer

@description('Contains CosmosDB Conversations Container')
output AZURE_COSMOS_CONVERSATIONS_CONTAINER string = cosmosDBConversationsContainer

@description('Contains Resource Group Name')
output RESOURCE_GROUP_NAME string = resourceGroup().name

@description('Contains AI Foundry Name')
output AI_FOUNDRY_NAME string = aiFoundryAiProjectResourceName

@description('Contains AI Foundry RG Name')
output AI_FOUNDRY_RG_NAME string = aiFoundryAiServicesResourceGroupName

@description('Contains AI Foundry Resource ID')
output AI_FOUNDRY_RESOURCE_ID string = useExistingAiFoundryAiProject ? '' : aiFoundryAiServices!.outputs.resourceId

@description('Contains existing AI project resource ID.')
output AZURE_EXISTING_AI_PROJECT_RESOURCE_ID string = azureExistingAIProjectResourceId

@description('Contains AI Search Service Endpoint URL')
output AZURE_AI_SEARCH_ENDPOINT string = 'https://${aiSearch.outputs.name}.search.windows.net/'

@description('Contains AI Search Service Name')
output AI_SEARCH_SERVICE_NAME string = aiSearch.outputs.name

@description('Contains AI Search Product Index')
output AZURE_AI_SEARCH_PRODUCTS_INDEX string = azureSearchIndex

@description('Contains AI Search Image Index')
output AZURE_AI_SEARCH_IMAGE_INDEX string = 'product-images'

@description('Contains Azure OpenAI endpoint URL')
output AZURE_OPENAI_ENDPOINT string = 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/'

@description('Contains GPT Model')
output AZURE_OPENAI_GPT_MODEL string = gptModelName

@description('Contains Image Model (empty if none selected)')
output AZURE_OPENAI_IMAGE_MODEL string = imageModelConfig[imageModelChoice].name

@description('Contains Azure OpenAI GPT/Image endpoint URL (empty if no image model selected)')
output AZURE_OPENAI_GPT_IMAGE_ENDPOINT string = imageModelChoice != 'none' ? 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' : ''

@description('Contains Azure OpenAI API Version')
output AZURE_OPENAI_API_VERSION string = azureOpenaiAPIVersion

@description('Contains OpenAI Resource')
output AZURE_OPENAI_RESOURCE string = aiFoundryAiServicesResourceName

@description('Contains AI Agent Endpoint')
output AZURE_AI_AGENT_ENDPOINT string = aiFoundryAiProjectEndpoint

@description('Contains AI Agent API Version')
output AZURE_AI_AGENT_API_VERSION string = azureAiAgentApiVersion

@description('Contains Application Insights Connection String')
output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = (enableMonitoring && !useExistingLogAnalytics) ? applicationInsights!.outputs.connectionString : ''

@description('Contains the location used for AI Services deployment')
output AI_SERVICE_LOCATION string = aiServiceLocation

@description('Contains Container Instance Name')
output CONTAINER_INSTANCE_NAME string = containerInstance.outputs.name

@description('Contains Container Instance IP Address')
output CONTAINER_INSTANCE_IP string = containerInstance.outputs.ipAddress

@description('Contains Container Instance FQDN (only for non-private networking)')
output CONTAINER_INSTANCE_FQDN string = enablePrivateNetworking ? '' : containerInstance.outputs.fqdn

@description('Contains ACR Name')
output ACR_NAME string = acrResourceName

@description('Contains flag for Azure AI Foundry usage')
output USE_FOUNDRY bool = useFoundryMode ? true : false

@description('Contains Azure AI Project Endpoint')
output AZURE_AI_PROJECT_ENDPOINT string = aiFoundryAiProjectEndpoint

@description('Contains Azure AI Model Deployment Name')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = gptModelName

@description('Contains Azure AI Image Model Deployment Name (empty if none selected)')
output AZURE_AI_IMAGE_MODEL_DEPLOYMENT string = imageModelConfig[imageModelChoice].name
