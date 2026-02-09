#!/bin/bash

# 🚀 Script de Setup Completo para Azure
# Autor: Lucila Gomez
# Proyecto: Plataforma de Empleos - IngSW3

set -e

echo "🚀 Iniciando setup de Azure para Plataforma de Empleos..."
echo "📍 Región: East US"
echo "👤 Usuario: Lucila Gomez"

# Variables de configuración
RESOURCE_GROUP="rg-empleos-lucila"
LOCATION="eastus"
ACR_NAME="acrempleos2024"
BACKEND_APP="userapi-lucila"
FRONTEND_APP="frontend-lucila"
POSTGRES_SERVER="postgresql-empleos-lucila"
POSTGRES_USER="adminlucila"
POSTGRES_PASSWORD="Admin1234!"
POSTGRES_DB="empleosdb"
KEY_VAULT="kv-empleos-lucila"
APP_INSIGHTS="ai-empleos-lucila"

echo ""
echo "=== 📋 Configuración ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $ACR_NAME"
echo "Backend App: $BACKEND_APP"
echo "Frontend App: $FRONTEND_APP"
echo "PostgreSQL Server: $POSTGRES_SERVER"
echo "Key Vault: $KEY_VAULT"
echo ""

# Verificar login de Azure
echo "🔐 Verificando login de Azure..."
if ! az account show &> /dev/null; then
    echo "❌ No estás logueado en Azure. Ejecuta: az login"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)
echo "✅ Logueado en Azure - Subscription: $SUBSCRIPTION_ID"

# Paso 1: Crear Resource Group
echo ""
echo "=== 📦 Paso 1: Crear Resource Group ==="
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags "proyecto=empleos" "owner=lucila" "environment=development"

echo "✅ Resource Group creado: $RESOURCE_GROUP"

# Paso 2: Crear Container Registry
echo ""
echo "=== 🐳 Paso 2: Crear Container Registry ==="
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

echo "✅ Container Registry creado: $ACR_NAME"

# Obtener credenciales de ACR
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "loginServer" -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "passwords[0].value" -o tsv)

echo "   📝 Login Server: $ACR_LOGIN_SERVER"
echo "   📝 Username: $ACR_USERNAME"

# Paso 3: Crear PostgreSQL Server
echo ""
echo "=== 🗄️ Paso 3: Crear PostgreSQL Server ==="
az postgres server create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --location $LOCATION \
  --admin-user $POSTGRES_USER \
  --admin-password $POSTGRES_PASSWORD \
  --sku-name B_Gen5_1 \
  --version 13

echo "✅ PostgreSQL Server creado: $POSTGRES_SERVER"

# Configurar firewall de PostgreSQL (permitir Azure services)
echo "   🔥 Configurando firewall..."
az postgres server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $POSTGRES_SERVER \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Crear base de datos
echo "   💾 Creando base de datos..."
az postgres db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $POSTGRES_SERVER \
  --name $POSTGRES_DB

echo "✅ Base de datos creada: $POSTGRES_DB"

# Paso 4: Crear Key Vault
echo ""
echo "=== 🔐 Paso 4: Crear Key Vault ==="
az keyvault create \
  --name $KEY_VAULT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

echo "✅ Key Vault creado: $KEY_VAULT"

# Paso 5: Crear Application Insights
echo ""
echo "=== 📊 Paso 5: Crear Application Insights ==="
az monitor app-insights component create \
  --app $APP_INSIGHTS \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

echo "✅ Application Insights creado: $APP_INSIGHTS"

# Paso 6: Crear App Service Plan
echo ""
echo "=== 🏗️ Paso 6: Crear App Service Plan ==="
APP_SERVICE_PLAN="asp-empleos-lucila"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --is-linux \
  --sku B1

echo "✅ App Service Plan creado: $APP_SERVICE_PLAN"

# Paso 7: Crear Web Apps
echo ""
echo "=== 🌐 Paso 7: Crear Web Apps ==="

# Backend App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $BACKEND_APP \
  --deployment-container-image-name "nginx:latest"

echo "✅ Backend App creada: $BACKEND_APP"

# Frontend App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $FRONTEND_APP \
  --deployment-container-image-name "nginx:latest"

echo "✅ Frontend App creada: $FRONTEND_APP"

# Paso 8: Configurar Container Registry en Web Apps
echo ""
echo "=== 🔗 Paso 8: Configurar Container Registry ==="

# Backend
az webapp config container set \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Frontend
az webapp config container set \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

echo "✅ Container Registry configurado en ambas apps"

# Paso 9: Crear secrets en Key Vault
echo ""
echo "=== 🔑 Paso 9: Crear Secrets en Key Vault ==="

# Connection string de PostgreSQL
POSTGRES_CONNECTION="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_SERVER.postgres.database.azure.com:5432/$POSTGRES_DB?sslmode=require"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "DATABASE-URL" \
  --value "$POSTGRES_CONNECTION"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "SECRET-KEY" \
  --value "$(openssl rand -hex 32)"

az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "INTERNAL-SERVICE-API-KEY" \
  --value "$(openssl rand -hex 32)"

echo "✅ Secrets creados en Key Vault"

# Paso 10: Obtener URLs finales
echo ""
echo "=== 📝 URLs Finales ==="
BACKEND_URL="https://$BACKEND_APP.azurewebsites.net"
FRONTEND_URL="https://$FRONTEND_APP.azurewebsites.net"

echo "🚀 Backend URL: $BACKEND_URL"
echo "🚀 Frontend URL: $FRONTEND_URL"
echo "🗄️ PostgreSQL: $POSTGRES_SERVER.postgres.database.azure.com"
echo "🐳 ACR: $ACR_LOGIN_SERVER"
echo "🔐 Key Vault: $KEY_VAULT.vault.azure.net"

# Paso 11: Crear Service Principal para CI/CD
echo ""
echo "=== 🤖 Paso 11: Crear Service Principal para CI/CD ==="
SERVICE_PRINCIPAL_NAME="sp-empleos-lucila"

SP_OUTPUT=$(az ad sp create-for-rbac \
  --name $SERVICE_PRINCIPAL_NAME \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --sdk-auth)

echo "✅ Service Principal creado: $SERVICE_PRINCIPAL_NAME"
echo ""
echo "🔑 IMPORTANTE: Guarda este JSON para GitHub Secrets:"
echo "---------------------------------------------------"
echo "$SP_OUTPUT"
echo "---------------------------------------------------"

# Crear archivo de configuración
echo ""
echo "=== 💾 Guardando configuración ==="
cat > azure-config.env << EOF
# Configuración de Azure - Plataforma de Empleos
# Generado automáticamente el $(date)

RESOURCE_GROUP=$RESOURCE_GROUP
LOCATION=$LOCATION
ACR_NAME=$ACR_NAME
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
BACKEND_APP=$BACKEND_APP
FRONTEND_APP=$FRONTEND_APP
POSTGRES_SERVER=$POSTGRES_SERVER
POSTGRES_USER=$POSTGRES_USER
POSTGRES_DB=$POSTGRES_DB
KEY_VAULT=$KEY_VAULT
APP_INSIGHTS=$APP_INSIGHTS
BACKEND_URL=$BACKEND_URL
FRONTEND_URL=$FRONTEND_URL
SUBSCRIPTION_ID=$SUBSCRIPTION_ID
EOF

echo "✅ Configuración guardada en azure-config.env"

echo ""
echo "🎉 ¡SETUP COMPLETO!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Guarda el JSON del Service Principal en GitHub Secrets como 'AZURE_CREDENTIALS'"
echo "2. Ejecuta los scripts de build y deploy"
echo "3. Configura las variables de entorno en las Web Apps"
echo ""
echo "🚀 URLs de tu aplicación:"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"