// ========== main.bicep ========== //
// Vanilla Bicep (Docker) flavor — lean, non-WAF deployment.
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

@description('Optional. The tags to apply to all deployed Azure resources.')
param tags object = {}

@description('Optional. Enable Azure AI Foundry mode for multi-agent orchestration.')
param useFoundryMode bool = true

@description('Optional. Unused in the Docker (bicep) flavor; a dedicated Container Registry is created during deployment. Retained for parameter-file compatibility.')
#disable-next-line no-unused-params
param acrName string = ''

@description('Optional. Frontend image name (built and pushed by AZD).')
param frontendImageName string = 'content-gen-app'

@description('Optional. Backend image name (built and pushed by AZD).')
param backendImageName string = 'content-gen-api'

@description('Optional. Image tag. ACI is only deployed when a real tag (not empty / not "none") is provided.')
param imageTag string = ''

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Created by user name.')
param createdBy string = contains(deployer(), 'userPrincipalName')? split(deployer().userPrincipalName, '@')[0]: deployer().objectId

// ============== //
// Variables      //
// ============== //

var solutionLocation = empty(location) ? resourceGroup().location : location

// Docker (bicep) flavor creates its own Azure Container Registry for remote builds
var acrResourceName = 'cr${solutionSuffix}'
var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

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
        Type: 'Non-WAF'
        CreatedBy: createdBy
      }
    )
  }
}

// ========== Log Analytics Workspace ========== //
var logAnalyticsWorkspaceResourceName = 'log-${solutionSuffix}'
module logAnalyticsWorkspace './bicep/modules/monitoring/log-analytics.bicep' = if (!useExistingLogAnalytics) {
  name: take('module.monitoring.log-analytics.${logAnalyticsWorkspaceResourceName}', 64)
  params: {
    name: logAnalyticsWorkspaceResourceName
    tags: tags
    location: solutionLocation
    enableTelemetry: enableTelemetry
  }
}
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics
  ? existingLogAnalyticsWorkspaceId
  : logAnalyticsWorkspace!.outputs.resourceId

// ========== Application Insights ========== //
var applicationInsightsResourceName = 'appi-${solutionSuffix}'
module applicationInsights './bicep/modules/monitoring/app-insights.bicep' = {
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
module userAssignedIdentity './bicep/modules/identity/user-assigned-identity.bicep' = {
  name: take('module.identity.user-assigned-identity.${userAssignedIdentityResourceName}', 64)
  params: {
    name: userAssignedIdentityResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// ========== Azure Container Registry ========== //
// Docker (bicep) flavor: ACR for remote Docker builds (AZD pushes images here).
module containerRegistry './bicep/modules/compute/container-registry.bicep' = {
  name: take('module.compute.container-registry.${acrResourceName}', 64)
  params: {
    name: acrResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    principalId: userAssignedIdentity.outputs.principalId
  }
}

// ========== AI Foundry: AI Services ========== //
module aiFoundryAiServices './bicep/modules/ai/ai-foundry-services.bicep'  = if (!useExistingAiFoundryAiProject) {
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
  }
}

module aiFoundryAiServicesProject './bicep/modules/ai/ai-foundry-project.bicep' = if (!useExistingAiFoundryAiProject) {
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
module existingAiServicesRoleAssignments './bicep/modules/ai/existing-services-roles.bicep' = if (useExistingAiFoundryAiProject) {
  name: take('module.foundry-role-assignment.${aiFoundryAiServicesResourceName}', 64)
  scope: resourceGroup(aiFoundryAiServicesSubscriptionId, aiFoundryAiServicesResourceGroupName)
  params: {
    aiServicesName: aiFoundryAiServicesResourceName
    principalId: userAssignedIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// ========== Model Deployments for Existing AI Services ========== //
module existingAiServicesModelDeployments './bicep/modules/ai/ai-foundry-model-deployment.bicep' = if (useExistingAiFoundryAiProject) {
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
module aiSearch './bicep/modules/ai/ai-search.bicep' = {
  name: take('module.ai.ai-search.${aiSearchName}', 64)
  params: {
    name: aiSearchName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    sku: 'basic'
    replicaCount: 1
    principalId: userAssignedIdentity.outputs.principalId
  }
}

// ========== Storage Account ========== //
var storageAccountName = 'st${solutionSuffix}'
var productImagesContainer = 'product-images'
var generatedImagesContainer = 'generated-images'

module storageAccount './bicep/modules/data/storage-account.bicep' = {
  name: take('module.data.storage-account.${storageAccountName}', 64)
  params: {
    name: storageAccountName
    location: solutionLocation
    skuName: 'Standard_LRS'
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
  }
}

// ========== Cosmos DB ========== //
var cosmosDBResourceName = 'cosmos-${solutionSuffix}'
var cosmosDBDatabaseName = 'content_generation_db'
var cosmosDBConversationsContainer = 'conversations'
var cosmosDBProductsContainer = 'products'

module cosmosDB './bicep/modules/data/cosmos-db-nosql.bicep' = {
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
  }
}

// ========== App Service Plan ========== //
var webServerFarmResourceName = 'asp-${solutionSuffix}'
module webServerFarm './bicep/modules/compute/app-service-plan.bicep' = {
  name: take('module.compute.app-service-plan.${webServerFarmResourceName}', 64)
  params: {
    name: webServerFarmResourceName
    tags: tags
    enableTelemetry: enableTelemetry
    location: solutionLocation
    skuName: 'B1'
    skuCapacity: 1
  }
}

// ========== Web App ========== //
var webSiteResourceName = 'app-${solutionSuffix}'
// Backend URL: Use actual ACI FQDN from deployment outputs
// This also creates an implicit dependency ensuring ACI deploys before the web app
var aciBackendUrl = shouldDeployACI
  ? 'http://${containerInstance!.properties.ipAddress.fqdn}:8000'
  : ''
module webSite './bicep/modules/compute/app-service.bicep' = {
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
    configs: [
      {
        // Frontend server proxies to ACI backend
        name: 'appsettings'
        properties: {
          WEBSITES_PORT: '8080'
          BACKEND_URL: aciBackendUrl
          AZURE_CLIENT_ID: userAssignedIdentity.outputs.clientId
          SCM_DO_BUILD_DURING_DEPLOYMENT: 'true' // Run npm install during deployment
        }
        applicationInsightResourceId: applicationInsights.outputs.resourceId
      }
      {
        name: 'logs'
        properties: {}
      }
    ]
    enableTelemetry: enableTelemetry
    e2eEncryptionEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

// ========== Container Instance (Backend API) ========== //
// Docker (bicep) flavor: inline ACI definition with managed identity auth for the created ACR.
var containerInstanceName = 'aci-${solutionSuffix}'
var backendImageUrl = '${containerRegistry.outputs.loginServer}/${backendImageName}:${imageTag}'
var aciPort = 8000
// Construct identity resource ID from known values (required for deployment-time calculation)
var userAssignedIdentityResourceIdForACI = '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/${userAssignedIdentityResourceName}'
// Deploy ACI only when imageTag is set to a real tag (not 'none')
var shouldDeployACI = !empty(imageTag) && imageTag != 'none'

#disable-next-line no-deployments-resources
resource aciTelemetry 'Microsoft.Resources/deployments@2025-04-01' = if (enableTelemetry && shouldDeployACI) {
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
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsights.outputs.connectionString }
          ]
        }
      }
    ]
    osType: 'Linux'
    restartPolicy: 'Always'
    ipAddress: {
      type: 'Public'
      ports: [
        {
          port: aciPort
          protocol: 'TCP'
        }
      ]
      dnsNameLabel: containerInstanceName
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
output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = applicationInsights.outputs.connectionString

@description('Contains the location used for AI Services deployment')
output AZURE_ENV_AI_SERVICE_LOCATION string = azureAiServiceLocation

@description('Contains Container Instance Name')
output CONTAINER_INSTANCE_NAME string = shouldDeployACI ? containerInstance!.name : ''

@description('Contains Container Instance FQDN')
output CONTAINER_INSTANCE_FQDN string = shouldDeployACI ? containerInstance!.properties.ipAddress.fqdn : ''

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
 