#!/bin/bash
# Package frontend for App Service deployment
# This script is called by AZD during prepackage hook
# Working directory is ./src/app/frontend-server (project directory)

echo "Building React frontend..."

# Build React frontend (one level up)
cd ../frontend
npm ci --loglevel=error
npm run build -- --outDir ../frontend-server/static
cd ../frontend-server

echo "Packaging frontend server..."

# Create dist folder and copy files
rm -rf ./dist
mkdir -p ./dist

# Copy required files to dist (node_modules excluded - App Service will npm install)
cp -r static ./dist/
cp server.js ./dist/
cp package.json ./dist/
cp package-lock.json ./dist/

echo "Frontend packaged successfully!"
