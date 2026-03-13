#!/bin/bash
# Script to update the backend DNS record after container restart
# This keeps the BACKEND_URL stable (backend.contentgen.internal)
# while updating the underlying IP when the container gets a new one.

set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-contentgen-jahunte}"
CONTAINER_NAME="${CONTAINER_NAME:-aci-contentgen-backend}"
DNS_ZONE="contentgen.internal"
RECORD_NAME="backend"

echo "Fetching current container IP..."
NEW_IP=$(az container show -g "$RESOURCE_GROUP" -n "$CONTAINER_NAME" --query "ipAddress.ip" -o tsv)
echo "Current container IP: $NEW_IP"

echo "Fetching current DNS record IP..."
CURRENT_IP=$(az network private-dns record-set a show -g "$RESOURCE_GROUP" -z "$DNS_ZONE" -n "$RECORD_NAME" --query "aRecords[0].ipv4Address" -o tsv 2>/dev/null || echo "")

if [ "$CURRENT_IP" == "$NEW_IP" ]; then
    echo "✓ DNS record is already up to date ($NEW_IP)"
    exit 0
fi

if [ -n "$CURRENT_IP" ]; then
    echo "Removing old DNS record ($CURRENT_IP)..."
    az network private-dns record-set a remove-record \
        -g "$RESOURCE_GROUP" \
        -z "$DNS_ZONE" \
        -n "$RECORD_NAME" \
        -a "$CURRENT_IP" \
        --keep-empty-record-set
fi

echo "Adding new DNS record ($NEW_IP)..."
az network private-dns record-set a add-record \
    -g "$RESOURCE_GROUP" \
    -z "$DNS_ZONE" \
    -n "$RECORD_NAME" \
    -a "$NEW_IP"

echo "✓ DNS record updated: $RECORD_NAME.$DNS_ZONE -> $NEW_IP"
echo ""
echo "The App Service will automatically use the new IP via:"
echo "  BACKEND_URL=http://backend.contentgen.internal:8000"
