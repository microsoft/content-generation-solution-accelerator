// ============================================================================
// Module: Virtual Machine (Jumpbox)
// Description: AVM wrapper for a Windows jumpbox VM used for private network
//              administration via Azure Bastion.
// AVM Module: avm/res/compute/virtual-machine:0.21.0
// ============================================================================

@description('Required. Name of the virtual machine (max 15 chars).')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. VM size.')
param vmSize string = 'Standard_D2s_v5'

@description('Required. Admin username for the VM.')
param adminUsername string

@secure()
@description('Required. Admin password for the VM.')
param adminPassword string

@description('Required. Resource ID of the user assigned managed identity.')
param userAssignedIdentityResourceId string

@description('Required. Resource ID of the subnet to attach the NIC to.')
param subnetResourceId string

@description('Optional. Availability zone (-1 to disable).')
param availabilityZone int = -1

@description('Optional. Enable monitoring agent and DCR association.')
param enableMonitoring bool = false

@description('Optional. Resource ID of the Data Collection Rule to associate.')
param dataCollectionRuleResourceId string = ''

module vm 'br/public:avm/res/compute/virtual-machine:0.21.0' = {
  name: take('avm.res.compute.virtual-machine.${name}', 64)
  params: {
    name: take(name, 15)
    enableTelemetry: enableTelemetry
    computerName: take(name, 15)
    osType: 'Windows'
    vmSize: vmSize
    adminUsername: adminUsername
    adminPassword: adminPassword
    managedIdentities: {
      userAssignedResourceIds: [
        userAssignedIdentityResourceId
      ]
    }
    availabilityZone: availabilityZone
    imageReference: {
      publisher: 'microsoft-dsvm'
      offer: 'dsvm-win-2022'
      sku: 'winserver-2022'
      version: 'latest'
    }
    nicConfigurations: [
      {
        name: 'nic-${name}'
        enableAcceleratedNetworking: true
        ipConfigurations: [
          {
            name: 'ipconfig01'
            subnetResourceId: subnetResourceId
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
    extensionMonitoringAgentConfig: {
      enabled: enableMonitoring
      dataCollectionRuleAssociations: enableMonitoring && !empty(dataCollectionRuleResourceId)
        ? [
            {
              name: 'dcra-${name}'
              dataCollectionRuleResourceId: dataCollectionRuleResourceId
              description: 'Associates the Windows security event DCR with the jumpbox VM.'
            }
          ]
        : []
    }
    location: location
    tags: tags
  }
}

@description('Resource ID of the virtual machine.')
output resourceId string = vm.outputs.resourceId

@description('Name of the virtual machine.')
output name string = vm.outputs.name
