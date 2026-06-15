// ============================================================================
// main.bicep — Deployment Router
// Description: Routes deployment to the appropriate infrastructure flavor.
//   - 'bicep'   → Vanilla Bicep / AVM-wrapper modules (Docker build, creates ACR)
//   - 'avm'     → AVM-based modules (uses existing ACR with pre-built images)
//   - 'avm-waf' → AVM-based modules with WAF-aligned features
//                 (monitoring, private networking, scalability, redundancy)
// ============================================================================
targetScope = 'resourceGroup'

metadata name = 'Intelligent Content Generation Accelerator'
metadata description = '''Solution Accelerator for multimodal marketing content generation using Microsoft Agent Framework.
'''

// ============================================================================
// Routing Parameter
// ============================================================================

@allowed([
  'bicep'
  'avm'
  'avm-waf'
])
@description('Required. Deployment flavor: bicep (Docker build, creates ACR), avm (AVM, existing ACR), or avm-waf (AVM WAF-aligned).')
param deploymentFlavor string = 'avm'

// ============================================================================
// Parameters — shared across all flavors
// ============================================================================

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

@description('Optional. Enable Azure AI Foundry mode for multi-agent orchestration.')
param useFoundryMode bool = true

@description('Optional. The tags to apply to all deployed Azure resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Created by user name.')
param createdBy string = contains(deployer(), 'userPrincipalName') ? split(deployer().userPrincipalName, '@')[0] : deployer().objectId

// ============================================================================
// Parameters — WAF / feature flags (AVM flavors)
// ============================================================================

@description('Optional. Enable monitoring for applicable resources (WAF-aligned).')
param enableMonitoring bool = false

@description('Optional. Enable scalability for applicable resources (WAF-aligned).')
param enableScalability bool = false

@description('Optional. Enable redundancy for applicable resources (WAF-aligned).')
param enableRedundancy bool = false

@description('Optional. Enable private networking for applicable resources (WAF-aligned).')
param enablePrivateNetworking bool = false

@description('Optional. Deploy Azure Bastion and Jumpbox resources for private network administration.')
param deployBastionAndJumpbox bool = false

@description('Optional. Jumpbox VM size. Must support accelerated networking and Premium SSD.')
param vmSize string = ''

@description('Optional. Jumpbox VM admin username.')
param vmAdminUsername string = ''

@secure()
@description('Optional. Jumpbox VM admin password.')
param vmAdminPassword string = ''

// ============================================================================
// Parameters — Container image (bicep + avm flavors)
// ============================================================================

@description('Optional. The Container Registry name (without .azurecr.io). Used by the avm flavor to reference an existing registry with pre-built images.')
param acrName string = 'contentgencontainerreg'

@description('Optional. Image tag.')
param imageTag string = 'latest'

@description('Optional. Frontend image name (bicep flavor builds and pushes this).')
param frontendImageName string = 'content-gen-app'

@description('Optional. Backend image name (bicep flavor builds and pushes this).')
param backendImageName string = 'content-gen-api'

// ============================================================================
// Derived Variables
// ============================================================================

var isAvm = deploymentFlavor == 'avm' || deploymentFlavor == 'avm-waf'
var isBicep = deploymentFlavor == 'bicep'

// ============================================================================
// Module: AVM Deployment (avm and avm-waf)
// ============================================================================

module avmDeployment './avm/main.bicep' = if (isAvm) {
  name: take('module.avm.${solutionName}', 64)
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    secondaryLocation: secondaryLocation
    azureAiServiceLocation: azureAiServiceLocation
    gptModelDeploymentType: gptModelDeploymentType
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    imageModelChoice: imageModelChoice
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    gptModelCapacity: gptModelCapacity
    imageModelCapacity: imageModelCapacity
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    azureExistingAIProjectResourceId: azureExistingAIProjectResourceId
    useFoundryMode: useFoundryMode
    deployBastionAndJumpbox: deployBastionAndJumpbox
    vmSize: vmSize
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    tags: tags
    enableMonitoring: enableMonitoring
    enableScalability: enableScalability
    enableRedundancy: enableRedundancy
    enablePrivateNetworking: enablePrivateNetworking
    acrName: acrName
    imageTag: imageTag
    enableTelemetry: enableTelemetry
    createdBy: createdBy
  }
}

// ============================================================================
// Module: Bicep Deployment (Docker build, creates ACR)
// ============================================================================

module bicepDeployment './bicep/main.bicep' = if (isBicep) {
  name: take('module.bicep.${solutionName}', 64)
  params: {
    solutionName: solutionName
    solutionUniqueText: solutionUniqueText
    location: location
    secondaryLocation: secondaryLocation
    azureAiServiceLocation: azureAiServiceLocation
    gptModelDeploymentType: gptModelDeploymentType
    gptModelName: gptModelName
    gptModelVersion: gptModelVersion
    imageModelChoice: imageModelChoice
    azureOpenaiAPIVersion: azureOpenaiAPIVersion
    gptModelCapacity: gptModelCapacity
    imageModelCapacity: imageModelCapacity
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    azureExistingAIProjectResourceId: azureExistingAIProjectResourceId
    useFoundryMode: useFoundryMode
    tags: tags
    imageTag: imageTag
    frontendImageName: frontendImageName
    backendImageName: backendImageName
    enableTelemetry: enableTelemetry
    createdBy: createdBy
  }
}

// ============================================================================
// Outputs — Coalesced from whichever flavor was deployed
// ============================================================================

@description('Deployment flavor used.')
output DEPLOYMENT_FLAVOR string = deploymentFlavor

@description('Contains App Service Name')
output APP_SERVICE_NAME string = isAvm ? avmDeployment!.outputs.APP_SERVICE_NAME : bicepDeployment!.outputs.APP_SERVICE_NAME

@description('Contains WebApp URL')
output WEB_APP_URL string = isAvm ? avmDeployment!.outputs.WEB_APP_URL : bicepDeployment!.outputs.WEB_APP_URL

@description('Contains Storage Account Name')
output AZURE_BLOB_ACCOUNT_NAME string = isAvm ? avmDeployment!.outputs.AZURE_BLOB_ACCOUNT_NAME : bicepDeployment!.outputs.AZURE_BLOB_ACCOUNT_NAME

@description('Contains Product Images Container')
output AZURE_BLOB_PRODUCT_IMAGES_CONTAINER string = isAvm ? avmDeployment!.outputs.AZURE_BLOB_PRODUCT_IMAGES_CONTAINER : bicepDeployment!.outputs.AZURE_BLOB_PRODUCT_IMAGES_CONTAINER

@description('Contains Generated Images Container')
output AZURE_BLOB_GENERATED_IMAGES_CONTAINER string = isAvm ? avmDeployment!.outputs.AZURE_BLOB_GENERATED_IMAGES_CONTAINER : bicepDeployment!.outputs.AZURE_BLOB_GENERATED_IMAGES_CONTAINER

@description('Contains Cosmos DB Account Name')
output COSMOSDB_ACCOUNT_NAME string = isAvm ? avmDeployment!.outputs.COSMOSDB_ACCOUNT_NAME : bicepDeployment!.outputs.COSMOSDB_ACCOUNT_NAME

@description('Contains Cosmos DB Endpoint')
output AZURE_COSMOS_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_COSMOS_ENDPOINT : bicepDeployment!.outputs.AZURE_COSMOS_ENDPOINT

@description('Contains Cosmos DB Database Name')
output AZURE_COSMOS_DATABASE_NAME string = isAvm ? avmDeployment!.outputs.AZURE_COSMOS_DATABASE_NAME : bicepDeployment!.outputs.AZURE_COSMOS_DATABASE_NAME

@description('Contains Cosmos DB Products Container')
output AZURE_COSMOS_PRODUCTS_CONTAINER string = isAvm ? avmDeployment!.outputs.AZURE_COSMOS_PRODUCTS_CONTAINER : bicepDeployment!.outputs.AZURE_COSMOS_PRODUCTS_CONTAINER

@description('Contains Cosmos DB Conversations Container')
output AZURE_COSMOS_CONVERSATIONS_CONTAINER string = isAvm ? avmDeployment!.outputs.AZURE_COSMOS_CONVERSATIONS_CONTAINER : bicepDeployment!.outputs.AZURE_COSMOS_CONVERSATIONS_CONTAINER

@description('Contains Resource Group Name')
output RESOURCE_GROUP_NAME string = resourceGroup().name

@description('Contains AI Foundry Resource ID')
output AI_FOUNDRY_RESOURCE_ID string = isAvm ? avmDeployment!.outputs.AI_FOUNDRY_RESOURCE_ID : bicepDeployment!.outputs.AI_FOUNDRY_RESOURCE_ID

@description('Contains Existing AI Project Resource ID')
output AZURE_EXISTING_AIPROJECT_RESOURCE_ID string = isAvm ? avmDeployment!.outputs.AZURE_EXISTING_AIPROJECT_RESOURCE_ID : bicepDeployment!.outputs.AZURE_EXISTING_AIPROJECT_RESOURCE_ID

@description('Contains AI Search Endpoint')
output AZURE_AI_SEARCH_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_AI_SEARCH_ENDPOINT : bicepDeployment!.outputs.AZURE_AI_SEARCH_ENDPOINT

@description('Contains AI Search Service Name')
output AI_SEARCH_SERVICE_NAME string = isAvm ? avmDeployment!.outputs.AI_SEARCH_SERVICE_NAME : bicepDeployment!.outputs.AI_SEARCH_SERVICE_NAME

@description('Contains AI Search Products Index')
output AZURE_AI_SEARCH_PRODUCTS_INDEX string = isAvm ? avmDeployment!.outputs.AZURE_AI_SEARCH_PRODUCTS_INDEX : bicepDeployment!.outputs.AZURE_AI_SEARCH_PRODUCTS_INDEX

@description('Contains AI Search Image Index')
output AZURE_AI_SEARCH_IMAGE_INDEX string = isAvm ? avmDeployment!.outputs.AZURE_AI_SEARCH_IMAGE_INDEX : bicepDeployment!.outputs.AZURE_AI_SEARCH_IMAGE_INDEX

@description('Contains Azure OpenAI Endpoint')
output AZURE_OPENAI_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_ENDPOINT : bicepDeployment!.outputs.AZURE_OPENAI_ENDPOINT

@description('Contains GPT Model Name')
output AZURE_ENV_GPT_MODEL_NAME string = isAvm ? avmDeployment!.outputs.AZURE_ENV_GPT_MODEL_NAME : bicepDeployment!.outputs.AZURE_ENV_GPT_MODEL_NAME

@description('Contains Image Model Name')
output AZURE_ENV_IMAGE_MODEL_NAME string = isAvm ? avmDeployment!.outputs.AZURE_ENV_IMAGE_MODEL_NAME : bicepDeployment!.outputs.AZURE_ENV_IMAGE_MODEL_NAME

@description('Contains Azure OpenAI GPT/Image endpoint URL (empty if no image model selected)')
output AZURE_OPENAI_GPT_IMAGE_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_GPT_IMAGE_ENDPOINT : bicepDeployment!.outputs.AZURE_OPENAI_GPT_IMAGE_ENDPOINT

@description('Contains Azure OpenAI API Version')
output AZURE_ENV_OPENAI_API_VERSION string = isAvm ? avmDeployment!.outputs.AZURE_ENV_OPENAI_API_VERSION : bicepDeployment!.outputs.AZURE_ENV_OPENAI_API_VERSION

@description('Contains OpenAI Resource')
output AZURE_OPENAI_RESOURCE string = isAvm ? avmDeployment!.outputs.AZURE_OPENAI_RESOURCE : bicepDeployment!.outputs.AZURE_OPENAI_RESOURCE

@description('Contains Application Insights Connection String')
output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = isAvm ? avmDeployment!.outputs.AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING : bicepDeployment!.outputs.AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING

@description('Contains the location used for AI Services deployment')
output AZURE_ENV_AI_SERVICE_LOCATION string = isAvm ? avmDeployment!.outputs.AZURE_ENV_AI_SERVICE_LOCATION : bicepDeployment!.outputs.AZURE_ENV_AI_SERVICE_LOCATION

@description('Contains Container Instance Name')
output CONTAINER_INSTANCE_NAME string = isAvm ? avmDeployment!.outputs.CONTAINER_INSTANCE_NAME : bicepDeployment!.outputs.CONTAINER_INSTANCE_NAME

@description('Contains Container Instance FQDN (only for non-private networking)')
output CONTAINER_INSTANCE_FQDN string = isAvm ? avmDeployment!.outputs.CONTAINER_INSTANCE_FQDN : bicepDeployment!.outputs.CONTAINER_INSTANCE_FQDN

@description('Contains ACR Name')
output AZURE_ENV_CONTAINER_REGISTRY_NAME string = isAvm ? avmDeployment!.outputs.AZURE_ENV_CONTAINER_REGISTRY_NAME : bicepDeployment!.outputs.AZURE_ENV_CONTAINER_REGISTRY_NAME

@description('Contains flag for Azure AI Foundry usage')
output USE_FOUNDRY bool = isAvm ? avmDeployment!.outputs.USE_FOUNDRY : bicepDeployment!.outputs.USE_FOUNDRY

@description('Contains Azure AI Project Endpoint')
output AZURE_AI_PROJECT_ENDPOINT string = isAvm ? avmDeployment!.outputs.AZURE_AI_PROJECT_ENDPOINT : bicepDeployment!.outputs.AZURE_AI_PROJECT_ENDPOINT

@description('Contains Azure AI Model Deployment Name')
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = isAvm ? avmDeployment!.outputs.AZURE_AI_MODEL_DEPLOYMENT_NAME : bicepDeployment!.outputs.AZURE_AI_MODEL_DEPLOYMENT_NAME

@description('Contains Azure AI Image Model Deployment Name (empty if none selected)')
output AZURE_AI_IMAGE_MODEL_DEPLOYMENT string = isAvm ? avmDeployment!.outputs.AZURE_AI_IMAGE_MODEL_DEPLOYMENT : bicepDeployment!.outputs.AZURE_AI_IMAGE_MODEL_DEPLOYMENT

@description('Contains Managed Identity Client ID (bicep flavor only)')
output AZURE_CLIENT_ID string = isBicep ? bicepDeployment!.outputs.AZURE_CLIENT_ID : ''

@description('Frontend image name')
output FRONTEND_IMAGE_NAME string = isBicep ? bicepDeployment!.outputs.FRONTEND_IMAGE_NAME : frontendImageName

@description('Backend image name')
output BACKEND_IMAGE_NAME string = isBicep ? bicepDeployment!.outputs.BACKEND_IMAGE_NAME : backendImageName

@description('Image tag')
output AZURE_ENV_IMAGE_TAG string = isBicep ? bicepDeployment!.outputs.AZURE_ENV_IMAGE_TAG : imageTag
