// ========== main.bicep ========== //
targetScope = 'resourceGroup'

metadata name = 'Intelligent Content Generation Accelerator'
metadata description = '''Solution Accelerator for multimodal marketing content generation using Microsoft Agent Framework.
'''

@minLength(3)
@maxLength(15)
@description('Optional. A unique application/solution name for all resources in this deployment.')
param solutionName string = 'contentgen'

@minLength(3)
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

@description('Optional. API version for Azure AI Agent service.')
param azureAiAgentApiVersion string = '2025-05-01'

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

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Frontend image name (without tag).')
param frontendImageName string = 'content-gen-app'

@description('Optional. Backend image name (without tag).')
param backendImageName string = 'content-gen-api'

@description('Optional. Image tag for container deployment. Leave empty to skip ACI deployment.')
param imageTag string

@description('Optional. Azure Container Registry name (unused - ACR name is auto-generated). Declared for parameter file compatibility.')
#disable-next-line no-unused-params
param acrName string = ''

@description('Optional. Created by user name.')
param createdBy string = contains(deployer(), 'userPrincipalName')? split(deployer().userPrincipalName, '@')[0]: deployer().objectId

// ============== //
// Variables      //
// ============== //

var solutionLocation = empty(location) ? resourceGroup().location : location

var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

// ACR name is always auto-generated in custom deployment
var acrResourceName = 'cr${solutionSuffix}'

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
resource avmTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry) {
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
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = if (enableMonitoring && !useExistingLogAnalytics) {
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
    dailyQuotaGb: enableRedundancy ? '10' : null
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
  }
}

// ========== User Assigned Identity ========== //
var userAssignedIdentityResourceName = 'id-${solutionSuffix}'
module userAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.5.0' = {
  name: take('avm.res.managed-identity.user-assigned-identity.${userAssignedIdentityResourceName}', 64)
  params: {
    name: userAssignedIdentityResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// ========== Azure Container Registry ========== //
// CUSTOM DEPLOYMENT: ACR for remote Docker builds (AZD pushes images here)
module containerRegistry 'br/public:avm/res/container-registry/registry:0.9.0' = {
  name: take('avm.res.container-registry.registry.${acrResourceName}', 64)
  params: {
    name: acrResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    acrSku: 'Standard'
    acrAdminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    roleAssignments: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        roleDefinitionIdOrName: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull
        principalType: 'ServicePrincipal'
      }
    ]
  }
}

// ========== Virtual Network and Networking Components ========== //
var deployAdminAccessResources = enablePrivateNetworking && deployBastionAndJumpbox && !empty(vmAdminPassword)
module virtualNetwork 'modules/virtualNetwork.bicep' = if (enablePrivateNetworking) {
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
module bastionHost 'br/public:avm/res/network/bastion-host:0.8.2' = if (deployAdminAccessResources) {
  name: take('avm.res.network.bastion-host.${bastionHostName}', 64)
  params: {
    name: bastionHostName
    skuName: 'Standard'
    location: solutionLocation
    virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId)
      ? [
          {
            name: 'bastionDiagnostics'
            workspaceResourceId: logAnalyticsWorkspaceResourceId
            logCategoriesAndGroups: [
              {
                categoryGroup: 'allLogs'
                enabled: true
              }
            ]
          }
        ]
      : []
    tags: tags
    enableTelemetry: enableTelemetry
    publicIPAddressObject: {
      name: 'pip-${bastionHostName}'
    }
  }
}

// Jumpbox Virtual Machine
var jumpboxUniqueToken = take(uniqueString(resourceGroup().id, solutionSuffix), 10)
var jumpboxVmName = take('vm-${jumpboxUniqueToken}', 15)
module jumpboxVM 'br/public:avm/res/compute/virtual-machine:0.21.0' = if (deployAdminAccessResources) {
  name: take('avm.res.compute.virtual-machine.${jumpboxVmName}', 64)
  params: {
    name: take(jumpboxVmName, 15)
    enableTelemetry: enableTelemetry
    computerName: take(jumpboxVmName, 15)
    osType: 'Windows'
    vmSize: empty(vmSize) ? 'Standard_D2s_v5' : vmSize
    adminUsername: empty(vmAdminUsername) ? 'JumpboxAdminUser' : vmAdminUsername
    adminPassword: vmAdminPassword
    managedIdentities: {
      userAssignedResourceIds: [
        userAssignedIdentity.outputs.resourceId
      ]
    }
    availabilityZone: contains(zoneSupportedJumpboxLocations, solutionLocation) ? 1 : -1
    imageReference: {
      publisher: 'microsoft-dsvm'
      offer: 'dsvm-win-2022'
      sku: 'winserver-2022'
      version: 'latest'
    }
    nicConfigurations: [
      {
        name: 'nic-${jumpboxVmName}'
        enableAcceleratedNetworking: true
        ipConfigurations: [
          {
            name: 'ipconfig01'
            subnetResourceId: virtualNetwork!.outputs.jumpboxSubnetResourceId
          }
        ]
      }
    ]
    osDisk: {
      caching: 'ReadWrite'
      diskSizeGB: 128
      managedDisk: {
        storageAccountType: 'Premium_LRS'
      }
    }
    encryptionAtHost: false // Some Azure subscriptions do not support encryption at host
    location: solutionLocation
    tags: tags
  }
  dependsOn: (enableMonitoring && !useExistingLogAnalytics) ? [logAnalyticsWorkspace] : []
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
module aiFoundryAiServices 'br/public:avm/res/cognitive-services/account:0.14.1'  = if (!useExistingAiFoundryAiProject) {
  name: take('avm.res.cognitive-services.account.${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: aiFoundryAiServicesResourceName
    location: azureAiServiceLocation
    tags: tags
    enableTelemetry: enableTelemetry
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
module aiServicesPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.1' = if (!useExistingAiFoundryAiProject && enablePrivateNetworking) {
  name: take('pep-ai-services-${aiFoundryAiServicesResourceName}', 64)
  params: {
    name: 'pep-${aiFoundryAiServicesResourceName}'
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
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
module existingAiServicesRoleAssignments 'modules/deploy_foundry_role_assignment.bicep' = if (useExistingAiFoundryAiProject) {
  name: take('module.foundry-role-assignment.${aiFoundryAiServicesResourceName}', 64)
  scope: resourceGroup(aiFoundryAiServicesSubscriptionId, aiFoundryAiServicesResourceGroupName)
  params: {
    aiServicesName: aiFoundryAiServicesResourceName
    principalId: userAssignedIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// ========== Model Deployments for Existing AI Services ========== //
module existingAiServicesModelDeployments 'modules/deploy_ai_model.bicep' = if (useExistingAiFoundryAiProject) {
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
module aiSearch 'br/public:avm/res/search/search-service:0.12.0' = {
  name: take('avm.res.search.search-service.${aiSearchName}', 64)
  params: {
    name: aiSearchName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    sku: enableScalability ? 'standard' : 'basic'
    replicaCount: enableRedundancy ? 3 : 1
    partitionCount: 1
    hostingMode: 'Default'
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
resource aiSearchFoundryConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-09-01' = if (!useExistingAiFoundryAiProject) {
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

module storageAccount 'br/public:avm/res/storage/storage-account:0.31.1' = {
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
    privateEndpoints: enablePrivateNetworking
      ? [
          {
            service: 'blob'
            subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                { privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.storageBlob]!.outputs.resourceId }
              ]
            }
          }
        ]
      : null
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
    privateEndpoints: enablePrivateNetworking
      ? [
          {
            service: 'Sql'
            subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                { privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cosmosDB]!.outputs.resourceId }
              ]
            }
          }
        ]
      : null
  }
}

// ========== App Service Plan ========== //
var webServerFarmResourceName = 'asp-${solutionSuffix}'
module webServerFarm 'br/public:avm/res/web/serverfarm:0.7.0' = {
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
    skuCapacity: enableRedundancy ? 2 : 1
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
    tags: union(tags, { 'azd-service-name': 'frontend' })
    location: solutionLocation
    kind: 'app,linux'
    serverFarmResourceId: webServerFarm.outputs.resourceId
    managedIdentities: { userAssignedResourceIds: [userAssignedIdentity!.outputs.resourceId] }
    siteConfig: {
      // Node.js runtime for frontend server (code deployment via AZD)
      linuxFxVersion: 'NODE|22-lts'
      minTlsVersion: '1.2'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
      appCommandLine: 'node server.js'
    }
    virtualNetworkSubnetId: enablePrivateNetworking ? virtualNetwork!.outputs.webSubnetResourceId : null
    configs: concat(
      [
        {
          // Frontend server proxies to ACI backend
          name: 'appsettings'
          properties: {
            WEBSITES_PORT: '8080'
            BACKEND_URL: aciBackendUrl
            AZURE_CLIENT_ID: userAssignedIdentity.outputs.clientId
            SCM_DO_BUILD_DURING_DEPLOYMENT: 'true' // Run npm install during deployment
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
    publicNetworkAccess: 'Enabled'
  }
}

// ========== Container Instance (Backend API) ========== //
// CUSTOM DEPLOYMENT: Inline ACI definition with managed identity auth for ACR
var containerInstanceName = 'aci-${solutionSuffix}'
var backendImageUrl = '${containerRegistry.outputs.loginServer}/${backendImageName}:${imageTag}'
var aciPort = 8000
var isPrivateNetworking = enablePrivateNetworking
// Construct identity resource ID from known values (required for deployment-time calculation)
var userAssignedIdentityResourceIdForACI = '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/${userAssignedIdentityResourceName}'
// Deploy ACI only when imageTag is set to a real tag (not 'none')
var shouldDeployACI = !empty(imageTag) && imageTag != 'none'

#disable-next-line no-deployments-resources
resource aciTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry && shouldDeployACI) {
  name: '46d3xbcp.res.containerinstance.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, solutionLocation), 0, 4)}'
  properties: {
    mode: 'Incremental'
    template: {
      '$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
      contentVersion: '1.0.0.0'
      resources: []
    }
  }
}

resource containerInstance 'Microsoft.ContainerInstance/containerGroups@2025-09-01' = if (shouldDeployACI) {
  name: containerInstanceName
  location: solutionLocation
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceIdForACI}': {}
    }
  }
  properties: {
    containers: [
      {
        name: containerInstanceName
        properties: {
          image: backendImageUrl
          resources: {
            requests: {
              cpu: 2
              memoryInGB: 4
            }
          }
          ports: [
            {
              port: aciPort
              protocol: 'TCP'
            }
          ]
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
    ]
    osType: 'Linux'
    restartPolicy: 'Always'
    subnetIds: isPrivateNetworking ? [
      {
        id: virtualNetwork!.outputs.aciSubnetResourceId
      }
    ] : null
    ipAddress: {
      type: isPrivateNetworking ? 'Private' : 'Public'
      ports: [
        {
          port: aciPort
          protocol: 'TCP'
        }
      ]
      dnsNameLabel: isPrivateNetworking ? null : containerInstanceName
    }
    // Managed identity auth for ACR (instead of anonymous pull)
    imageRegistryCredentials: [
      {
        server: containerRegistry.outputs.loginServer
        identity: userAssignedIdentityResourceIdForACI
      }
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

@description('Contains AI Agent Endpoint')
output AZURE_AI_AGENT_ENDPOINT string = aiFoundryAiProjectEndpoint

@description('Contains AI Agent API Version')
output AZURE_AI_AGENT_API_VERSION string = azureAiAgentApiVersion

@description('Contains Application Insights Connection String')
output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = (enableMonitoring && !useExistingLogAnalytics) ? applicationInsights!.outputs.connectionString : ''

@description('Contains the location used for AI Services deployment')
output AZURE_ENV_AI_SERVICE_LOCATION string = azureAiServiceLocation

@description('Contains Container Instance Name')
output CONTAINER_INSTANCE_NAME string = shouldDeployACI ? containerInstance!.name : ''

@description('Contains Container Instance IP Address')
output CONTAINER_INSTANCE_IP string = shouldDeployACI ? containerInstance!.properties.ipAddress.ip : ''

@description('Contains Container Instance FQDN (only for non-private networking)')
output CONTAINER_INSTANCE_FQDN string = (shouldDeployACI && !isPrivateNetworking) ? containerInstance!.properties.ipAddress.fqdn : ''

@description('Contains ACR Name')
output AZURE_ENV_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

@description('Contains flag for Azure AI Foundry usage')
output USE_FOUNDRY bool = useFoundryMode ? true : false

@description('Contains Azure AI Project Endpoint')
output AZURE_AI_PROJECT_ENDPOINT string = aiFoundryAiProjectEndpoint

@description('Contains Azure AI Model Deployment Name')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = gptModelName

@description('Contains Azure AI Image Model Deployment Name (empty if none selected)')
output AZURE_AI_IMAGE_MODEL_DEPLOYMENT string = imageModelConfig[imageModelChoice].name

@description('Contains Managed Identity Client ID')
output AZURE_CLIENT_ID string = userAssignedIdentity.outputs.clientId

@description('Frontend image name')
output FRONTEND_IMAGE_NAME string = frontendImageName

@description('Backend image name')
output BACKEND_IMAGE_NAME string = backendImageName

@description('Image tag')
output AZURE_ENV_IMAGE_TAG string = imageTag
