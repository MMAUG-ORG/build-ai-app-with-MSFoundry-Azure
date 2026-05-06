param name string
param location string
param tags object = {}
param serverFarmId string
param runtime string
param startupCommand string
param appSettings array = []

resource site 'Microsoft.Web/sites@2023-12-01' = {
  name: name
  location: location
  tags: tags
  kind: 'app,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: serverFarmId
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: runtime
      appCommandLine: startupCommand
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      alwaysOn: true
      appSettings: appSettings
    }
  }
}

output id string = site.id
output principalId string = site.identity.principalId
output defaultHostName string = site.properties.defaultHostName
