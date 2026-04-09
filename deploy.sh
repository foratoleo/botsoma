#!/bin/bash
# Deploy botsoma to Azure Container Apps
# Usage: ./deploy.sh [version]
# Example: ./deploy.sh v3

set -e

VERSION=${1:-v$(date +%Y%m%d-%H%M)}
ACR_NAME="botsomaacr"
ACR_URL="${ACR_NAME}.azurecr.io"
RG="teams-bot-rg"
APP_NAME="botsoma-bot"
IMAGE="${ACR_URL}/botsoma/${VERSION}"

echo "=== Building Docker image ==="
docker build -t botsoma .

echo ""
echo "=== Tagging as ${IMAGE} ==="
docker tag botsoma:latest "${IMAGE}"

echo ""
echo "=== Getting ACR token ==="
ACR_TOKEN=$(az acr login --name "${ACR_NAME}" --expose-token --query accessToken -o tsv 2>/dev/null)
mkdir -p /tmp/docker-config
echo "$ACR_TOKEN" | docker --config /tmp/docker-config login "${ACR_URL}" \
  -u 00000000-0000-0000-0000-000000000000 --password-stdin

echo ""
echo "=== Pushing to ACR ==="
docker --config /tmp/docker-config push "${IMAGE}"

echo ""
echo "=== Updating Container App ==="
az containerapp update --name "${APP_NAME}" --resource-group "${RG}" --image "${IMAGE}"

echo ""
echo "=== Done! Version: ${VERSION} ==="
echo "Endpoint: https://botsoma-bot.salmonsmoke-8320777a.eastus2.azurecontainerapps.io/api/messages"
echo ""
echo "Checking logs (Ctrl+C to stop)..."
sleep 20
az containerapp logs show --name "${APP_NAME}" --resource-group "${RG}" --tail 15
