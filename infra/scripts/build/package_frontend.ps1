# Package frontend for App Service deployment
# This script is called by AZD during prepackage hook
# Working directory is ./src/App/server (project directory)

$ErrorActionPreference = 'Stop'

Write-Host "Building React frontend..." -ForegroundColor Cyan

# Build React frontend (one level up)
Push-Location ..
npm ci --loglevel=error
if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }
npm run build -- --outDir ./server/static
if ($LASTEXITCODE -ne 0) { throw "npm run build failed with exit code $LASTEXITCODE" }
Pop-Location

Write-Host "Packaging frontend server..." -ForegroundColor Cyan

# Create dist folder
mkdir dist -Force | Out-Null
rm dist/* -r -Force -ErrorAction SilentlyContinue

# Copy required files to dist (node_modules excluded - App Service will npm install)
cp -r static dist -Force
cp server.js dist -Force
cp package.json dist -Force
cp package-lock.json dist -Force

Write-Host "Frontend packaged successfully!" -ForegroundColor Green
