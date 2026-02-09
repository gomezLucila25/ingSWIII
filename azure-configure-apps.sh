#!/bin/bash

# 🔧 Script de Configuración Post-Deploy
# Configura las Web Apps con ambientes QA y Production
# Autor: Lucila Gomez - IngSW3

set -e

echo "🔧 Configurando aplicaciones Azure para Lucila Gomez..."

# Variables
RESOURCE_GROUP="rg-empleos-lucila"
KEY_VAULT="kv-empleos-lucila"
BACKEND_APP_QA="userapi-lucila-qa"
BACKEND_APP_PROD="userapi-lucila"
FRONTEND_APP_QA="frontend-lucila-qa"  
FRONTEND_APP_PROD="frontend-lucila"
ACR_NAME="acrempleos2024"

echo "📋 Configuración:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Key Vault: $KEY_VAULT"
echo "   Backend QA: $BACKEND_APP_QA"
echo "   Backend Prod: $BACKEND_APP_PROD"
echo "   Frontend QA: $FRONTEND_APP_QA"
echo "   Frontend Prod: $FRONTEND_APP_PROD"

# Verificar login
if ! az account show &> /dev/null; then
    echo "❌ No estás logueado en Azure. Ejecuta: az login"
    exit 1
fi

echo ""
echo "=== 🔐 Paso 1: Obtener secrets de Key Vault ==="

DATABASE_URL=$(az keyvault secret show --name "DATABASE-URL" --vault-name "$KEY_VAULT" --query "value" -o tsv)
SECRET_KEY=$(az keyvault secret show --name "SECRET-KEY" --vault-name "$KEY_VAULT" --query "value" -o tsv)
INTERNAL_KEY=$(az keyvault secret show --name "INTERNAL-SERVICE-API-KEY" --vault-name "$KEY_VAULT" --query "value" -o tsv)

echo "✅ Secrets obtenidos de Key Vault"

echo ""
echo "=== ⚙️ Paso 2: Configurar Backend QA ==="

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_QA \
  --settings \
  DATABASE_URL="$DATABASE_URL" \
  SECRET_KEY="$SECRET_KEY" \
  INTERNAL_SERVICE_API_KEY="$INTERNAL_KEY" \
  ALGORITHM="HS256" \
  ACCESS_TOKEN_EXPIRE_MINUTES="30" \
  PORT="8000" \
  ENVIRONMENT="qa"

echo "✅ Backend QA configurado"

echo ""
echo "=== ⚙️ Paso 3: Configurar Backend Production ==="

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_PROD \
  --settings \
  DATABASE_URL="$DATABASE_URL" \
  SECRET_KEY="$SECRET_KEY" \
  INTERNAL_SERVICE_API_KEY="$INTERNAL_KEY" \
  ALGORITHM="HS256" \
  ACCESS_TOKEN_EXPIRE_MINUTES="120" \
  PORT="8000" \
  ENVIRONMENT="production"

echo "✅ Backend Production configurado"

echo ""
echo "=== 🐳 Paso 4: Configurar Container Settings ==="

# Obtener credenciales de ACR
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "loginServer" -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "passwords[0].value" -o tsv)

# Configurar Backend QA
az webapp config container set \
  --name $BACKEND_APP_QA \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configurar Backend Production
az webapp config container set \
  --name $BACKEND_APP_PROD \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configurar Frontend QA
az webapp config container set \
  --name $FRONTEND_APP_QA \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configurar Frontend Production
az webapp config container set \
  --name $FRONTEND_APP_PROD \
  --resource-group $RESOURCE_GROUP \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

echo "✅ Container settings configurados"

echo ""
echo "=== 🌐 Paso 5: Configurar Custom Domains y SSL ==="

# Habilitar HTTPS Only
az webapp update --resource-group $RESOURCE_GROUP --name $BACKEND_APP_QA --https-only true
az webapp update --resource-group $RESOURCE_GROUP --name $BACKEND_APP_PROD --https-only true
az webapp update --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_QA --https-only true
az webapp update --resource-group $RESOURCE_GROUP --name $FRONTEND_APP_PROD --https-only true

echo "✅ HTTPS habilitado para todas las apps"

echo ""
echo "=== 🔍 Paso 6: Verificar configuración ==="

# URLs finales
BACKEND_QA_URL="https://$BACKEND_APP_QA.azurewebsites.net"
BACKEND_PROD_URL="https://$BACKEND_APP_PROD.azurewebsites.net"
FRONTEND_QA_URL="https://$FRONTEND_APP_QA.azurewebsites.net"
FRONTEND_PROD_URL="https://$FRONTEND_APP_PROD.azurewebsites.net"

echo "📋 URLs de aplicaciones:"
echo "   Backend QA:     $BACKEND_QA_URL"
echo "   Backend Prod:   $BACKEND_PROD_URL"
echo "   Frontend QA:    $FRONTEND_QA_URL"
echo "   Frontend Prod:  $FRONTEND_PROD_URL"

echo ""
echo "=== 💾 Paso 7: Crear archivo de configuración ==="

cat > azure-urls.env << EOF
# URLs de Azure - Plataforma de Empleos Lucila Gomez
# Generado el $(date)

# Backend URLs
BACKEND_QA_URL=$BACKEND_QA_URL
BACKEND_PROD_URL=$BACKEND_PROD_URL

# Frontend URLs  
FRONTEND_QA_URL=$FRONTEND_QA_URL
FRONTEND_PROD_URL=$FRONTEND_PROD_URL

# API Documentation
API_DOCS_QA=$BACKEND_QA_URL/docs
API_DOCS_PROD=$BACKEND_PROD_URL/docs

# Health Check Endpoints
HEALTH_QA=$BACKEND_QA_URL/health
HEALTH_PROD=$BACKEND_PROD_URL/health

# Container Registry
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
EOF

echo "✅ Configuración guardada en azure-urls.env"

echo ""
echo "🎉 ¡CONFIGURACIÓN COMPLETA!"
echo ""
echo "🚀 Para hacer deploy inicial ejecuta:"
echo "   ./azure-first-deploy.sh"
echo ""
echo "📋 Para monitorear logs:"
echo "   az webapp log tail --name $BACKEND_APP_PROD --resource-group $RESOURCE_GROUP"
echo ""
echo "🔍 Para verificar health checks:"
echo "   curl $BACKEND_PROD_URL/health"