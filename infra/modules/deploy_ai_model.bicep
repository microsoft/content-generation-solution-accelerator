@description('Required. Name of the AI Services account.')
param aiServicesName string

@description('Required. Array of model deployments to create.')
param deployments array = []

// Reference AI Services account (module is scoped to the correct resource group)
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiServicesName
}

// Deploy models to AI Services account
// Using batchSize(1) to avoid concurrent deployment issues
@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [
  for (deployment, index) in deployments: {
    parent: aiServices
    name: deployment.name
    properties: {
      model: {
        format: deployment.format
        name: deployment.model
        version: deployment.version
      }
      raiPolicyName: deployment.raiPolicyName
    }
    sku: {
      name: deployment.sku.name
      capacity: deployment.sku.capacity
    }
  }
]

@description('The names of the deployed models.')
output deployedModelNames array = [for (deployment, i) in deployments: modelDeployments[i].name]
