/****************************************************************************************************************************/
// Networking - NSGs, VNET and Subnets for Content Generation Solution
// Vanilla Bicep implementation (raw resources, no AVM registry dependency).
// NOTE: Not used by the lean main.bicep; retained for module parity with the
//       AVM flavor across GSA.
/****************************************************************************************************************************/
@description('Name of the virtual network.')
param vnetName string

@description('Azure region to deploy resources.')
param location string = resourceGroup().location

@description('Required. An Array of 1 or more IP Address Prefixes for the Virtual Network.')
param addressPrefixes array = ['10.0.0.0/20']

@description('Optional. Deploy Azure Bastion and Jumpbox subnets for VM-based administration.')
param deployBastionAndJumpbox bool = false

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. The resource ID of the Log Analytics Workspace to send diagnostic logs to.')
param logAnalyticsWorkspaceId string = ''

@description('Optional. Enable/Disable usage telemetry for module.')
#disable-next-line no-unused-params
param enableTelemetry bool = true

@description('Required. Suffix for resource naming.')
param resourceSuffix string

// Core subnets: web (App Service), peps (Private Endpoints), aci (Container Instance)
// Optional: AzureBastionSubnet and jumpbox (only when deployBastionAndJumpbox is true)
var coreSubnets = [
  {
    name: 'web'
    addressPrefixes: ['10.0.0.0/23']
    delegation: 'Microsoft.Web/serverFarms'
    networkSecurityGroup: {
      name: 'nsg-web'
      securityRules: [
        {
          name: 'AllowHttpsInbound'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '443'
            sourceAddressPrefixes: ['0.0.0.0/0']
            destinationAddressPrefixes: ['10.0.0.0/23']
          }
        }
        {
          name: 'AllowIntraSubnetTraffic'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 200
            protocol: '*'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: ['10.0.0.0/23']
            destinationAddressPrefixes: ['10.0.0.0/23']
          }
        }
        {
          name: 'AllowAzureLoadBalancer'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 300
            protocol: '*'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefix: 'AzureLoadBalancer'
            destinationAddressPrefix: '10.0.0.0/23'
          }
        }
      ]
    }
  }
  {
    name: 'peps'
    addressPrefixes: ['10.0.2.0/23']
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
    networkSecurityGroup: {
      name: 'nsg-peps'
      securityRules: []
    }
  }
  {
    name: 'aci'
    addressPrefixes: ['10.0.4.0/24']
    delegation: 'Microsoft.ContainerInstance/containerGroups'
    networkSecurityGroup: {
      name: 'nsg-aci'
      securityRules: [
        {
          name: 'AllowHttpsInbound'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '8000'
            sourceAddressPrefixes: ['10.0.0.0/20']
            destinationAddressPrefixes: ['10.0.4.0/24']
          }
        }
      ]
    }
  }
]

var bastionSubnets = deployBastionAndJumpbox ? [
  {
    name: 'AzureBastionSubnet'
    addressPrefixes: ['10.0.10.0/26']
    networkSecurityGroup: {
      name: 'nsg-bastion'
      securityRules: [
        {
          name: 'AllowGatewayManager'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 2702
            protocol: '*'
            sourcePortRange: '*'
            destinationPortRange: '443'
            sourceAddressPrefix: 'GatewayManager'
            destinationAddressPrefix: '*'
          }
        }
        {
          name: 'AllowHttpsInBound'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 2703
            protocol: '*'
            sourcePortRange: '*'
            destinationPortRange: '443'
            sourceAddressPrefix: 'Internet'
            destinationAddressPrefix: '*'
          }
        }
        {
          name: 'AllowSshRdpOutbound'
          properties: {
            access: 'Allow'
            direction: 'Outbound'
            priority: 100
            protocol: '*'
            sourcePortRange: '*'
            destinationPortRanges: ['22', '3389']
            sourceAddressPrefix: '*'
            destinationAddressPrefix: 'VirtualNetwork'
          }
        }
        {
          name: 'AllowAzureCloudOutbound'
          properties: {
            access: 'Allow'
            direction: 'Outbound'
            priority: 110
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '443'
            sourceAddressPrefix: '*'
            destinationAddressPrefix: 'AzureCloud'
          }
        }
      ]
    }
  }
  {
    name: 'jumpbox'
    addressPrefixes: ['10.0.12.0/23']
    networkSecurityGroup: {
      name: 'nsg-jumpbox'
      securityRules: [
        {
          name: 'AllowRdpFromBastion'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '3389'
            sourceAddressPrefixes: ['10.0.10.0/26']
            destinationAddressPrefixes: ['10.0.12.0/23']
          }
        }
      ]
    }
  }
] : []

var vnetSubnets = concat(coreSubnets, bastionSubnets)
var subnetNames = map(vnetSubnets, subnet => subnet.name)

// Create NSGs for subnets
@batchSize(1)
resource nsgs 'Microsoft.Network/networkSecurityGroups@2024-05-01' = [
  for (subnet, i) in vnetSubnets: {
    name: '${subnet.networkSecurityGroup.name}-${resourceSuffix}'
    location: location
    tags: tags
    properties: {
      securityRules: subnet.networkSecurityGroup.securityRules
    }
  }
]

// Create VNet and subnets
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: addressPrefixes
    }
    subnets: [
      for (subnet, i) in vnetSubnets: {
        name: subnet.name
        properties: {
          addressPrefixes: subnet.addressPrefixes
          networkSecurityGroup: {
            id: nsgs[i].id
          }
          privateEndpointNetworkPolicies: subnet.?privateEndpointNetworkPolicies
          privateLinkServiceNetworkPolicies: subnet.?privateLinkServiceNetworkPolicies
          delegations: empty(subnet.?delegation) ? [] : [
            {
              name: 'delegation'
              properties: {
                serviceName: subnet.?delegation
              }
            }
          ]
        }
      }
    ]
  }
}

resource vnetDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'vnetDiagnostics'
  scope: virtualNetwork
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output name string = virtualNetwork.name
output resourceId string = virtualNetwork.id

// Core subnet outputs (always present)
output webSubnetResourceId string = contains(subnetNames, 'web') ? virtualNetwork.properties.subnets[indexOf(subnetNames, 'web')].id : ''
output pepsSubnetResourceId string = contains(subnetNames, 'peps') ? virtualNetwork.properties.subnets[indexOf(subnetNames, 'peps')].id : ''
output aciSubnetResourceId string = contains(subnetNames, 'aci') ? virtualNetwork.properties.subnets[indexOf(subnetNames, 'aci')].id : ''

// Bastion/jumpbox subnet outputs (always declared; will be empty when those subnets are not deployed)
output bastionSubnetResourceId string = contains(subnetNames, 'AzureBastionSubnet') ? virtualNetwork.properties.subnets[indexOf(subnetNames, 'AzureBastionSubnet')].id : ''
output jumpboxSubnetResourceId string = contains(subnetNames, 'jumpbox') ? virtualNetwork.properties.subnets[indexOf(subnetNames, 'jumpbox')].id : ''
