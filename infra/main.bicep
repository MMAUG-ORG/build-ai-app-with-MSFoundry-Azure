// MMAUG · Foundry-powered Customer Support App
// Subscription-scope deployment (azd default scope is resource group, but
// App Service plans + Postgres are RG-scoped; we keep this RG-scoped).

targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string = resourceGroup().location

@description('Object id of the user/SP running azd – granted dev RBAC roles.')
param principalId string = ''

@secure()
@description('Admin password for the Postgres flexible server.')
param postgresAdminPassword string

// Fixed naming convention for the live MMAUG meetup deployment.
// All resources land as "<service>-mmaug-meetup-0217" (storage strips hyphens).
// The numeric tail keeps globally-namespaced resources (storage, app service,
// postgres) collision-free if the names are reused on a different day.
var suffix        = 'mmaug-meetup-0217'
var storageSuffix = replace(suffix, '-', '')
var tags          = { 'azd-env-name': environmentName, project: 'mmaug-foundry-support', event: 'mmaug-meetup' }

// ---------- Storage ----------
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name:     'st${storageSuffix}'
    location: location
    tags:     tags
  }
}

// ---------- Postgres ----------
module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    name:          'pg-${suffix}'
    location:      location
    tags:          tags
    adminUser:     'pgadmin'
    adminPassword: postgresAdminPassword
    databaseName:  'support'
  }
}

// ---------- Foundry (AI project + gpt-4o-mini deployment) ----------
module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  params: {
    accountName: 'aif-${suffix}'
    projectName: 'mmaug-support'
    location:    location
    tags:        tags
    modelName:   'gpt-4o-mini'
    modelVersion:'2024-07-18'
    skuCapacity: 50
  }
}

// ---------- App Service Plan (shared by API + Web) ----------
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'plan-${suffix}'
  location: location
  tags: tags
  sku: { name: 'B3', tier: 'Basic' }
  kind: 'linux'
  properties: { reserved: true }
}

// ---------- API (Python FastAPI) ----------
module api 'modules/appservice.bicep' = {
  name: 'api'
  params: {
    name: 'app-api-${suffix}'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    serverFarmId: plan.id
    runtime: 'PYTHON|3.11'
    startupCommand: 'gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --timeout 120'
    appSettings: [
      { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
      { name: 'WEBSITES_PORT',                  value: '8000' }
      { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundry.outputs.projectEndpoint }
      { name: 'FOUNDRY_MODEL_DEPLOYMENT', value: foundry.outputs.modelDeploymentName }
      { name: 'POSTGRES_HOST',     value: postgres.outputs.fqdn }
      { name: 'POSTGRES_DB',       value: 'support' }
      { name: 'POSTGRES_USER',     value: 'pgadmin' }
      { name: 'POSTGRES_PASSWORD', value: postgresAdminPassword }
      { name: 'POSTGRES_SSLMODE',  value: 'require' }
      { name: 'STORAGE_ACCOUNT_NAME', value: storage.outputs.name }
      { name: 'STORAGE_CONTAINER',    value: 'attachments' }
      { name: 'CORS_ORIGINS',         value: 'https://app-web-${suffix}.azurewebsites.net' }
    ]
  }
}

// ---------- Web (React static build) ----------
module web 'modules/appservice.bicep' = {
  name: 'web'
  params: {
    name: 'app-web-${suffix}'
    location: location
    tags: union(tags, { 'azd-service-name': 'web' })
    serverFarmId: plan.id
    runtime: 'NODE|20-lts'
    startupCommand: 'npx --yes serve -s . -l 8080'
    appSettings: [
      { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'false' }
      { name: 'WEBSITES_PORT', value: '8080' }
      { name: 'VITE_API_BASE', value: 'https://${api.outputs.defaultHostName}' }
    ]
  }
}

// ---------- RBAC ----------
// Storage Blob Data Contributor on the storage account → API managed identity
resource storageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'api', 'storage-blob-contrib')
  scope: resourceGroup()
  properties: {
    principalId: api.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'      // Storage Blob Data Contributor
    )
  }
}

// Azure AI User on the Foundry account → API managed identity
resource foundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'api', 'azure-ai-user')
  scope: resourceGroup()
  properties: {
    principalId: api.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '53ca6127-db72-4b80-b1b0-d745d6d5456d'      // Azure AI User
    )
  }
}

// Dev: also grant the user running azd
resource userFoundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(resourceGroup().id, principalId, 'azure-ai-user-dev')
  scope: resourceGroup()
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '53ca6127-db72-4b80-b1b0-d745d6d5456d'
    )
  }
}

// ---------- Outputs (consumed by post-provision hook) ----------
output AZURE_LOCATION string = location
output FOUNDRY_PROJECT_ENDPOINT string = foundry.outputs.projectEndpoint
output FOUNDRY_MODEL_DEPLOYMENT string = foundry.outputs.modelDeploymentName
output API_HOSTNAME string = api.outputs.defaultHostName
output WEB_HOSTNAME string = web.outputs.defaultHostName
output STORAGE_ACCOUNT_NAME string = storage.outputs.name
output POSTGRES_FQDN string = postgres.outputs.fqdn
