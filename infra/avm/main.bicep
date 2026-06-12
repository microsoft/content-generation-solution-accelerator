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

// NOTE: Metadata must be compile-time constants. Update usageName manually if you change model parameters.
// Format: 'OpenAI.<DeploymentType>.<ModelName>,<Capacity>'
// Allowed regions: Union of GPT-5.1, gpt-image-1-mini, and gpt-image-1.5 GlobalStandard availability
@allowed([
  'australiaeast'
  'canadaeast'
  'eastus2'
  'japaneast'
  'koreacentral'
  'polandcentral'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
    usageName: [
      'OpenAI.GlobalStandard.gpt-5.1,150'
      'OpenAI.GlobalStandard.gpt-image-1-mini,1'
    ]
  }
})
@description('Required. Location for AI deployments.')
param azureAiServiceLocation string

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

@description('Optional. Image model to deploy: gpt-image-1-mini, gpt-image-1.5, or none to skip.')
@allowed([
  'gpt-image-1-mini'
  'gpt-image-1.5'
  'none'
])
param imageModelChoice string = 'gpt-image-1-mini'

@description('Optional. API version for Azure OpenAI service.')
param azureOpenaiAPIVersion string = '2025-01-01-preview'

@minValue(10)
@description('Optional. AI model deployment token capacity.')
param gptModelCapacity int = 150

@minValue(1)
@description('Optional. Image model deployment capacity (RPM).')
param imageModelCapacity int = 1

@description('Optional. Existing Log Analytics Workspace Resource ID.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. Resource ID of an existing Foundry project.')
param azureExistingAIProjectResourceId string = ''

@description('Optional. Deploy Azure Bastion and Jumpbox resources for private network administration.')
param deployBastionAndJumpbox bool = false

@description('Optional. Jumpbox VM size. Must support accelerated networking and Premium SSD.')
param vmSize string = ''

@description('Optional. Jumpbox VM admin username.')
param vmAdminUsername string = ''

@description('Optional. Jumpbox VM admin password.')
@secure()
param vmAdminPassword string = ''

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

@description('Optional. The existing Container Registry name (without .azurecr.io). Must contain pre-built images: content-gen-app and content-gen-api.')
param acrName string = 'contentgencontainerreg'

@description('Optional. Image Tag.')
param imageTag string = 'latest'

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Created by user name.')
param createdBy string = contains(deployer(), 'userPrincipalName')? split(deployer().userPrincipalName, '@')[0]: deployer().objectId

// ============== //
// Variables      //
// ============== //

var solutionLocation = empty(location) ? resourceGroup().location : location

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

// Extracts subscription, resource group, and workspace name from the resource ID
var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)
var useExistingAiFoundryAiProject = !empty(azureExistingAIProjectResourceId)
var aiFoundryAiServicesResourceGroupName = useExistingAiFoundryAiProject
  ? split(azureExistingAIProjectResourceId, '/')[4]
  : 'rg-${solutionSuffix}'
var aiFoundryAiServicesSubscriptionId = useExistingAiFoundryAiProject
  ? split(azureExistingAIProjectResourceId, '/')[2]
  : subscription().subscriptionId
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
  'gpt-image-1-mini': {
    name: 'gpt-image-1-mini'
    version: '2025-10-06'
    sku: 'GlobalStandard'
  }
  'gpt-image-1.5': {
    name: 'gpt-image-1.5'
    version: '2025-12-16'
    sku: 'GlobalStandard'
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
      capacity: imageModelCapacity
    }
    version: imageModelConfig[imageModelChoice].version
    raiPolicyName: 'Microsoft.Default'
  }
] : []

// Combine deployments based on imageModelChoice
var aiFoundryAiServicesModelDeployment = concat(baseModelDeployments, imageModelDeployment)

var aiFoundryAiProjectDescription = 'Content Generation AI Foundry Project'

// Reference existing resource group to access current tags
resource existingResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  scope: subscription()
  name: resourceGroup().name
}

var existingTags = existingResourceGroup.tags ?? {}

// ============== //
// Resources      //
// ============== //

#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2025-04-01' = if (enableTelemetry) {
  name: '46d3xbcp.ptn.sa-contentgeneration.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, solutionLocation), 0, 4)}'
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
resource resourceGroupTags 'Microsoft.Resources/tags@2025-04-01' = {
  name: 'default'
  properties: {
    tags: union(
      existingTags,
      tags,
      {
        TemplateName: 'ContentGen'
        Type: enablePrivateNetworking ? 'WAF' : 'Non-WAF'
        CreatedBy: createdBy
      }
    )
  }
}

// ========== Log Analytics Workspace ========== //
var logAnalyticsWorkspaceResourceName = 'log-${solutionSuffix}'
module logAnalyticsWorkspace 'modules/monitoring/log-analytics.bicep' = if (enableMonitoring && !useExistingLogAnalytics) {
  name: take('module.monitoring.log-analytics.${logAnalyticsWorkspaceResourceName}', 64)
  params: {
    name: logAnalyticsWorkspaceResourceName
    tags: tags
    location: solutionLocation
    enableTelemetry: enableTelemetry
    enableRedundancy: enableRedundancy
    replicaLocation: replicaLocation
    enablePrivateNetworking: enablePrivateNetworking
  }
}
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics 
  ? existingLogAnalyticsWorkspaceId 
  : (enableMonitoring ? logAnalyticsWorkspace!.outputs.resourceId : '')

// ========== Application Insights ========== //
var applicationInsightsResourceName = 'appi-${solutionSuffix}'
module applicationInsights 'modules/monitoring/app-insights.bicep' = if (enableMonitoring) {
  name: take('module.monitoring.app-insights.${applicationInsightsResourceName}', 64)
  params: {
    name: applicationInsightsResourceName
    tags: tags
    location: solutionLocation
    enableTelemetry: enableTelemetry
    workspaceResourceId: logAnalyticsWorkspaceResourceId
  }
}

// ========== User Assigned Identity ========== //
var userAssignedIdentityResourceName = 'id-${solutionSuffix}'
module userAssignedIdentity 'modules/identity/user-assigned-identity.bicep' = {
  name: take('module.identity.user-assigned-identity.${userAssignedIdentityResourceName}', 64)
  params: {
    name: userAssignedIdentityResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// ========== Virtual Network and Networking Components ========== //
var deployAdminAccessResources = enablePrivateNetworking && deployBastionAndJumpbox && !empty(vmAdminPassword)
module virtualNetwork 'modules/networking/virtual-network.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtualNetwork.${solutionSuffix}', 64)
  params: {
    vnetName: 'vnet-${solutionSuffix}'
    addressPrefixes: ['10.0.0.0/20'] // 4096 addresses (enough for 8 /23 subnets or 16 /24)
    location: solutionLocation
    deployBastionAndJumpbox: deployAdminAccessResources
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceResourceId
    resourceSuffix: solutionSuffix
    enableTelemetry: enableTelemetry
  }
}

// Azure Bastion Host
var bastionHostName = 'bas-${solutionSuffix}'
var zoneSupportedJumpboxLocations = [
  'australiaeast'
  'centralus'
  'eastus'
  'eastus2'
  'japaneast'
  'northeurope'
  'southeastasia'
  'swedencentral'
  'uksouth'
  'westus3'
]
module bastionHost 'modules/networking/bastion-host.bicep' = if (deployAdminAccessResources) {
  name: take('module.networking.bastion-host.${bastionHostName}', 64)
  params: {
    name: bastionHostName
    location: solutionLocation
    virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// Jumpbox Virtual Machine
var jumpboxUniqueToken = take(uniqueString(resourceGroup().id, solutionSuffix), 10)
var jumpboxVmName = take('vm-${jumpboxUniqueToken}', 15)
module jumpboxVM 'modules/compute/virtual-machine.bicep' = if (deployAdminAccessResources) {
  name: take('module.compute.virtual-machine.${jumpboxVmName}', 64)
  params: {
    name: take(jumpboxVmName, 15)
    enableTelemetry: enableTelemetry
    vmSize: empty(vmSize) ? 'Standard_D2s_v5' : vmSize
    adminUsername: empty(vmAdminUsername) ? 'JumpboxAdminUser' : vmAdminUsername
    adminPassword: vmAdminPassword
    userAssignedIdentityResourceId: userAssignedIdentity.outputs.resourceId
    subnetResourceId: virtualNetwork!.outputs.jumpboxSubnetResourceId
    availabilityZone: contains(zoneSupportedJumpboxLocations, solutionLocation) ? 1 : -1
    enableMonitoring: enableMonitoring
    dataCollectionRuleResourceId: (deployAdminAccessResources && enableMonitoring) ? jumpboxDcr!.outputs.resourceId : ''
    location: solutionLocation
    tags: tags
  }
  dependsOn: (enableMonitoring && !useExistingLogAnalytics) ? [logAnalyticsWorkspace, jumpboxDcr] : (enableMonitoring ? [jumpboxDcr] : [])
}

// ========== Data Collection Rule for Jumpbox Security Event Logs (SFI-AzTBv17) ========== //
var jumpboxDcrName = take('dcr-${jumpboxVmName}', 64)
var dcrLogAnalyticsDestinationName = 'la-${logAnalyticsWorkspaceResourceName}-destination'
module jumpboxDcr 'modules/monitoring/data-collection-rule.bicep' = if (deployAdminAccessResources && enableMonitoring) {
  name: take('module.monitoring.data-collection-rule.${jumpboxDcrName}', 64)
  params: {
    name: jumpboxDcrName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    destinationName: dcrLogAnalyticsDestinationName
  }
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
module avmPrivateDnsZones 'modules/networking/private-dns-zone.bicep' = [
  for (zone, i) in privateDnsZones: if (enablePrivateNetworking) {
    name: take('module.networking.private-dns-zone.${replace(zone, '.', '-')}', 64)
    params: {
      name: zone
      tags: tags
      enableTelemetry: enableTelemetry
      virtualNetworkResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.resourceId : ''
    }
  }
]

// ========== AI Foundry: AI Services ========== //
module aiFoundryAiServices 'modules/ai/ai-foundry-services.bicep'  = if (!useExistingAiFoundryAiProject) {
  name: take('module.ai.ai-foundry-services.${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: aiFoundryAiServicesResourceName
    location: azureAiServiceLocation
    tags: tags
    enableTelemetry: enableTelemetry
    modelDeployments: aiFoundryAiServicesModelDeployment
    principalId: userAssignedIdentity.outputs.principalId
    deployerPrincipalId: deployer().objectId
    userAssignedIdentityResourceId: userAssignedIdentity!.outputs.resourceId
    enableMonitoring: enableMonitoring
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    enablePrivateNetworking: enablePrivateNetworking
  }
}

// Create private endpoint for AI Services AFTER the account is fully provisioned
module aiServicesPrivateEndpoint 'modules/networking/private-endpoint.bicep' = if (!useExistingAiFoundryAiProject && enablePrivateNetworking) {
  name: take('module.networking.private-endpoint.${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: 'pep-${aiFoundryAiServicesResourceName}'
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
    targetResourceId: aiFoundryAiServices!.outputs.resourceId
    groupIds: ['account']
    privateDnsZoneConfigs: [
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

module aiFoundryAiServicesProject 'modules/ai/ai-foundry-project.bicep' = if (!useExistingAiFoundryAiProject) {
  name: take('module.ai-project.${aiFoundryAiProjectResourceName}', 64)
  params: {
    name: aiFoundryAiProjectResourceName
    location: azureAiServiceLocation
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

// ========== Role Assignments for Existing AI Services ========== //
module existingAiServicesRoleAssignments 'modules/ai/existing-services-roles.bicep' = if (useExistingAiFoundryAiProject) {
  name: take('module.foundry-role-assignment.${aiFoundryAiServicesResourceName}', 64)
  scope: resourceGroup(aiFoundryAiServicesSubscriptionId, aiFoundryAiServicesResourceGroupName)
  params: {
    aiServicesName: aiFoundryAiServicesResourceName
    principalId: userAssignedIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// ========== Model Deployments for Existing AI Services ========== //
module existingAiServicesModelDeployments 'modules/ai/ai-foundry-model-deployment.bicep' = if (useExistingAiFoundryAiProject) {
  name: take('module.model-deployments-existing.${aiFoundryAiServicesResourceName}', 64)
  scope: resourceGroup(aiFoundryAiServicesSubscriptionId, aiFoundryAiServicesResourceGroupName)
  params: {
    aiServicesName: aiFoundryAiServicesResourceName
    deployments: [
      for deployment in aiFoundryAiServicesModelDeployment: {
        name: deployment.name
        format: deployment.format
        model: deployment.model
        sku: {
          name: deployment.sku.name
          capacity: deployment.sku.capacity
        }
        version: deployment.version
        raiPolicyName: deployment.raiPolicyName
      }
    ]
  }
  dependsOn: [
    existingAiServicesRoleAssignments
  ]
}

// ========== AI Search ========== //
module aiSearch 'modules/ai/ai-search.bicep' = {
  name: take('module.ai.ai-search.${aiSearchName}', 64)
  params: {
    name: aiSearchName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    sku: enableScalability ? 'standard' : 'basic'
    replicaCount: enableRedundancy ? 3 : 1
    principalId: userAssignedIdentity.outputs.principalId
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []
  }
}

// ========== Storage Account ========== //
var storageAccountName = 'st${solutionSuffix}'
var productImagesContainer = 'product-images'
var generatedImagesContainer = 'generated-images'

module storageAccount 'modules/data/storage-account.bicep' = {
  name: take('module.data.storage-account.${storageAccountName}', 64)
  params: {
    name: storageAccountName
    location: solutionLocation
    skuName: enableRedundancy ? 'Standard_ZRS' : 'Standard_LRS'
    enableTelemetry: enableTelemetry
    tags: tags
    containers: [
      {
        name: productImagesContainer
        publicAccess: 'None'
      }
      {
        name: generatedImagesContainer
        publicAccess: 'None'
      }
    ]
    principalId: userAssignedIdentity.outputs.principalId
    enablePrivateNetworking: enablePrivateNetworking
    subnetResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.pepsSubnetResourceId : ''
    blobDnsZoneResourceId: enablePrivateNetworking ? avmPrivateDnsZones[dnsZoneIndex.storageBlob]!.outputs.resourceId : ''
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []
  }
}

// ========== Cosmos DB ========== //
var cosmosDBResourceName = 'cosmos-${solutionSuffix}'
var cosmosDBDatabaseName = 'content_generation_db'
var cosmosDBConversationsContainer = 'conversations'
var cosmosDBProductsContainer = 'products'

module cosmosDB 'modules/data/cosmos-db-nosql.bicep' = {
  name: take('module.data.cosmos-db-nosql.${cosmosDBResourceName}', 64)
  params: {
    name: 'cosmos-${solutionSuffix}'
    location: secondaryLocation
    tags: tags
    enableTelemetry: enableTelemetry
    databaseName: cosmosDBDatabaseName
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
    principalId: userAssignedIdentity.outputs.principalId
    deployerPrincipalId: deployer().objectId
    enableRedundancy: enableRedundancy
    haLocation: cosmosDbHaLocation
    enablePrivateNetworking: enablePrivateNetworking
    subnetResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.pepsSubnetResourceId : ''
    cosmosDnsZoneResourceId: enablePrivateNetworking ? avmPrivateDnsZones[dnsZoneIndex.cosmosDB]!.outputs.resourceId : ''
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []
  }
}

// ========== App Service Plan ========== //
var webServerFarmResourceName = 'asp-${solutionSuffix}'
module webServerFarm 'modules/compute/app-service-plan.bicep' = {
  name: take('module.compute.app-service-plan.${webServerFarmResourceName}', 64)
  params: {
    name: webServerFarmResourceName
    tags: tags
    enableTelemetry: enableTelemetry
    location: solutionLocation
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []
    skuName: enableScalability || enableRedundancy ? 'P1v3' : 'B1'
    skuCapacity: enableRedundancy ? 2 : 1
    zoneRedundant: enableRedundancy ? true : false
  }
}

// ========== Web App ========== //
var webSiteResourceName = 'app-${solutionSuffix}'
// Backend URL: Use actual ACI IP/FQDN from deployment outputs
// This also creates an implicit dependency ensuring ACI deploys before the web app
var aciBackendUrl = enablePrivateNetworking
  ? 'http://${containerInstance.outputs.ipAddress}:8000'
  : 'http://${containerInstance.outputs.fqdn}:8000'
module webSite 'modules/compute/app-service.bicep' = {
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
    configs: concat(
      [
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
      ],
      enableMonitoring
        ? [
            {
              name: 'logs'
              properties: {}
            }
          ]
        : []
    )
    enableMonitoring: enableMonitoring
    enableTelemetry: enableTelemetry
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
    vnetRouteAllEnabled: enablePrivateNetworking
    vnetImagePullEnabled: enablePrivateNetworking
    e2eEncryptionEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

// ========== Container Instance (Backend API) ========== //
var containerInstanceName = 'aci-${solutionSuffix}'
module containerInstance 'modules/compute/container-instance.bicep' = {
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
    userAssignedIdentityResourceId: userAssignedIdentity.outputs.resourceId
    enableTelemetry: enableTelemetry
    environmentVariables: [
      // Azure OpenAI Settings
      { name: 'AZURE_OPENAI_ENDPOINT', value: 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' }
      { name: 'AZURE_ENV_GPT_MODEL_NAME', value: gptModelName }
      { name: 'AZURE_ENV_IMAGE_MODEL_NAME', value: imageModelConfig[imageModelChoice].name }
      { name: 'AZURE_OPENAI_GPT_IMAGE_ENDPOINT', value: imageModelChoice != 'none' ? 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' : '' }
      { name: 'AZURE_ENV_OPENAI_API_VERSION', value: azureOpenaiAPIVersion }
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
      // Logging Settings
      { name: 'AZURE_BASIC_LOGGING_LEVEL', value: 'INFO' }
      { name: 'AZURE_PACKAGE_LOGGING_LEVEL', value: 'WARNING' }
      { name: 'AZURE_LOGGING_PACKAGES', value: '' }
      // Application Insights
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: enableMonitoring ? applicationInsights!.outputs.connectionString : '' }
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

@description('Contains AI Foundry Resource ID')
output AI_FOUNDRY_RESOURCE_ID string = useExistingAiFoundryAiProject ? '' : aiFoundryAiServices!.outputs.resourceId

@description('Contains existing AI project resource ID.')
output AZURE_EXISTING_AIPROJECT_RESOURCE_ID string = azureExistingAIProjectResourceId

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
output AZURE_ENV_GPT_MODEL_NAME string = gptModelName

@description('Contains Image Model (empty if none selected)')
output AZURE_ENV_IMAGE_MODEL_NAME string = imageModelConfig[imageModelChoice].name

@description('Contains Azure OpenAI GPT/Image endpoint URL (empty if no image model selected)')
output AZURE_OPENAI_GPT_IMAGE_ENDPOINT string = imageModelChoice != 'none' ? 'https://${aiFoundryAiServicesResourceName}.openai.azure.com/' : ''

@description('Contains Azure OpenAI API Version')
output AZURE_ENV_OPENAI_API_VERSION string = azureOpenaiAPIVersion

@description('Contains OpenAI Resource')
output AZURE_OPENAI_RESOURCE string = aiFoundryAiServicesResourceName

@description('Contains Application Insights Connection String')
output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = (enableMonitoring && !useExistingLogAnalytics) ? applicationInsights!.outputs.connectionString : ''

@description('Contains the location used for AI Services deployment')
output AZURE_ENV_AI_SERVICE_LOCATION string = azureAiServiceLocation

@description('Contains Container Instance Name')
output CONTAINER_INSTANCE_NAME string = containerInstance.outputs.name

@description('Contains Container Instance FQDN (only for non-private networking)')
output CONTAINER_INSTANCE_FQDN string = enablePrivateNetworking ? '' : containerInstance.outputs.fqdn

@description('Contains ACR Name')
output AZURE_ENV_CONTAINER_REGISTRY_NAME string = acrResourceName

@description('Contains flag for Azure AI Foundry usage')
output USE_FOUNDRY bool = useFoundryMode ? true : false

@description('Contains Azure AI Project Endpoint')
output AZURE_AI_PROJECT_ENDPOINT string = aiFoundryAiProjectEndpoint

@description('Contains Azure AI Model Deployment Name')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = gptModelName

@description('Contains Azure AI Image Model Deployment Name (empty if none selected)')
output AZURE_AI_IMAGE_MODEL_DEPLOYMENT string = imageModelConfig[imageModelChoice].name
