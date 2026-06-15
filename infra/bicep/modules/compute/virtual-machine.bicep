// ============================================================================
// Module: Virtual Machine (Jumpbox)
// Description: Vanilla Bicep module for a Windows jumpbox VM used for private
//              network administration via Azure Bastion.
// Resources: Microsoft.Compute/virtualMachines, Microsoft.Network/networkInterfaces
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
// ============================================================================

@description('Required. Name of the virtual machine (max 15 chars).')
param name string

@description('Required. Azure region for the resource.')
param location string

@description('Optional. Tags to apply to the resource.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
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

var vmName = take(name, 15)

resource nic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: 'nic-${vmName}'
  location: location
  tags: tags
  properties: {
    enableAcceleratedNetworking: true
    ipConfigurations: [
      {
        name: 'ipconfig01'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          subnet: {
            id: subnetResourceId
          }
        }
      }
    ]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' = {
  name: vmName
  location: location
  tags: tags
  zones: availabilityZone == -1 ? null : [string(availabilityZone)]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      adminPassword: adminPassword
    }
    storageProfile: {
      imageReference: {
        publisher: 'microsoft-dsvm'
        offer: 'dsvm-win-2022'
        sku: 'winserver-2022'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        caching: 'ReadWrite'
        diskSizeGB: 128
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
    securityProfile: {
      encryptionAtHost: false // Some Azure subscriptions do not support encryption at host
    }
  }
}

resource monitoringAgent 'Microsoft.Compute/virtualMachines/extensions@2024-07-01' = if (enableMonitoring) {
  parent: vm
  name: 'AzureMonitorWindowsAgent'
  location: location
  tags: tags
  properties: {
    publisher: 'Microsoft.Azure.Monitor'
    type: 'AzureMonitorWindowsAgent'
    typeHandlerVersion: '1.0'
    autoUpgradeMinorVersion: true
    enableAutomaticUpgrade: true
  }
}

resource dcrAssociation 'Microsoft.Insights/dataCollectionRuleAssociations@2023-03-11' = if (enableMonitoring && !empty(dataCollectionRuleResourceId)) {
  name: 'dcra-${vmName}'
  scope: vm
  properties: {
    description: 'Associates the Windows security event DCR with the jumpbox VM.'
    dataCollectionRuleId: dataCollectionRuleResourceId
  }
  dependsOn: [
    monitoringAgent
  ]
}

@description('Resource ID of the virtual machine.')
output resourceId string = vm.id

@description('Name of the virtual machine.')
output name string = vm.name
