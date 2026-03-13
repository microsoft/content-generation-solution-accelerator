# =============================================================================
# Local Development Script for Content Generation Accelerator (PowerShell)
# =============================================================================
#
# This script sets up and runs the application locally for development.
#
# Usage:
#   .\local_dev.ps1              # Start both backend and frontend
#   .\local_dev.ps1 -Command backend   # Start only the backend
#   .\local_dev.ps1 -Command frontend  # Start only the frontend
#   .\local_dev.ps1 -Command setup     # Set up virtual environment and install dependencies
#   .\local_dev.ps1 -Command env       # Generate .env file from Azure resources
#
# Prerequisites:
#   - Python 3.11+
#   - Node.js 18+
#   - Azure CLI (for fetching environment variables)
#
# =============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "env", "backend", "frontend", "all", "build", "clean", "help")]
    [string]$Command = "all"
)

$ErrorActionPreference = "Stop"

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SrcDir = Join-Path $ProjectRoot "src"
$BackendDir = Join-Path $SrcDir "backend"
$FrontendDir = Join-Path $SrcDir "app\frontend"

# Default ports
$BackendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "5000" }
$FrontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "============================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$CommandName)
    return [bool](Get-Command -Name $CommandName -ErrorAction SilentlyContinue)
}

# =============================================================================
# Azure Authentication & Role Functions
# =============================================================================

function Ensure-AzureLogin {
    if (-not (Test-Command "az")) {
        Write-Error "Azure CLI is not installed. Please install it first."
        exit 1
    }
    
    $accountId = az account show --query id -o tsv 2>$null
    if ($accountId) {
        $accountName = az account show --query name -o tsv 2>$null
        Write-Success "Logged in to Azure: $accountName"
    } else {
        Write-Info "Not logged in. Running az login..."
        az login --use-device-code --output none
        $accountId = az account show --query id -o tsv 2>$null
        if (-not $accountId) {
            Write-Error "Azure login failed."
            exit 1
        }
        Write-Success "Azure login successful."
    }
}

function Ensure-AzureAIUserRole {
    Write-Info "Checking Azure AI User role..."
    
    # Get env vars
    $existingProjectId = $null
    $foundryResourceId = $null
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^AZURE_EXISTING_AI_PROJECT_RESOURCE_ID=(.*)$") { $existingProjectId = $matches[1].Trim('"').Trim("'") }
            if ($_ -match "^AI_FOUNDRY_RESOURCE_ID=(.*)$") { $foundryResourceId = $matches[1].Trim('"').Trim("'") }
        }
    }
    
    # Determine scope
    $scope = $null
    if ($existingProjectId) {
        $scope = $existingProjectId
    } elseif ($foundryResourceId) {
        $scope = $foundryResourceId
    } else {
        Write-Error "Neither AZURE_EXISTING_AI_PROJECT_RESOURCE_ID nor AI_FOUNDRY_RESOURCE_ID found in .env"
        exit 1
    }
    
    $signedUserId = az ad signed-in-user show --query id -o tsv 2>$null
    if (-not $signedUserId) {
        Write-Error "Could not get signed-in user ID."
        exit 1
    }
    
    $roleId = "53ca6127-db72-4b80-b1b0-d745d6d5456d"
    $existing = az role assignment list --assignee $signedUserId --role $roleId --scope $scope --query "[0].id" -o tsv 2>$null
    
    if ($existing) {
        Write-Success "Azure AI User role already assigned."
    } else {
        Write-Info "Assigning Azure AI User role..."
        az role assignment create --assignee $signedUserId --role $roleId --scope $scope --output none 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to assign Azure AI User role."
            exit 1
        }
        Write-Success "Azure AI User role assigned."
    }
}

function Ensure-CosmosDBRole {
    Write-Info "Checking Cosmos DB Data Contributor role..."
    
    # Get env vars
    $cosmosAccount = $null
    $resourceGroup = $null
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^COSMOSDB_ACCOUNT_NAME=(.*)$") { $cosmosAccount = $matches[1].Trim('"').Trim("'") }
            if ($_ -match "^RESOURCE_GROUP_NAME=(.*)$") { $resourceGroup = $matches[1].Trim('"').Trim("'") }
        }
    }
    
    if (-not $cosmosAccount -or -not $resourceGroup) {
        Write-Error "COSMOSDB_ACCOUNT_NAME or RESOURCE_GROUP_NAME not found in .env"
        exit 1
    }
    
    $signedUserId = az ad signed-in-user show --query id -o tsv 2>$null
    if (-not $signedUserId) {
        Write-Error "Could not get signed-in user ID."
        exit 1
    }
    
    $roleDefId = "00000000-0000-0000-0000-000000000002"
    
    # Check if role already assigned
    $existing = az cosmosdb sql role assignment list --resource-group $resourceGroup --account-name $cosmosAccount --query "[?principalId=='$signedUserId' && contains(roleDefinitionId, '$roleDefId')].id | [0]" -o tsv 2>$null
    
    if ($existing) {
        Write-Success "Cosmos DB role already assigned."
    } else {
        Write-Info "Assigning Cosmos DB role..."
        az cosmosdb sql role assignment create --resource-group $resourceGroup --account-name $cosmosAccount --role-definition-id $roleDefId --principal-id $signedUserId --scope "/" --output none 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to assign Cosmos DB role."
            exit 1
        }
        Write-Success "Cosmos DB role assigned."
    }
}

function Ensure-StorageRole {
    Write-Info "Checking Storage Blob Data Contributor role..."
    
    # Get env vars
    $storageAccount = $null
    $resourceGroup = $null
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^AZURE_BLOB_ACCOUNT_NAME=(.*)$") { $storageAccount = $matches[1].Trim('"').Trim("'") }
            if ($_ -match "^RESOURCE_GROUP_NAME=(.*)$") { $resourceGroup = $matches[1].Trim('"').Trim("'") }
        }
    }
    
    if (-not $storageAccount -or -not $resourceGroup) {
        Write-Error "AZURE_BLOB_ACCOUNT_NAME or RESOURCE_GROUP_NAME not found in .env"
        exit 1
    }
    
    $signedUserId = az ad signed-in-user show --query id -o tsv 2>$null
    if (-not $signedUserId) {
        Write-Error "Could not get signed-in user ID."
        exit 1
    }
    
    # Get storage account resource ID
    $storageResourceId = az storage account show --name $storageAccount --resource-group $resourceGroup --query id -o tsv 2>$null
    if (-not $storageResourceId) {
        Write-Error "Could not get storage account resource ID."
        exit 1
    }
    
    $roleId = "Storage Blob Data Contributor"
    $existing = az role assignment list --assignee $signedUserId --role $roleId --scope $storageResourceId --query "[0].id" -o tsv 2>$null
    
    if ($existing) {
        Write-Success "Storage Blob Data Contributor role already assigned."
    } else {
        Write-Info "Assigning Storage Blob Data Contributor role..."
        az role assignment create --assignee $signedUserId --role $roleId --scope $storageResourceId --output none 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to assign Storage Blob Data Contributor role."
            exit 1
        }
        Write-Success "Storage Blob Data Contributor role assigned."
    }
}

# =============================================================================
# Setup Function
# =============================================================================

function Invoke-Setup {
    Write-Header "Setting Up Local Development Environment"
    
    Set-Location $ProjectRoot
    
    # Check Python
    Write-Info "Checking Python installation..."
    if (-not (Test-Command "python")) {
        Write-Error "Python is not installed. Please install Python 3.11+"
        exit 1
    }
    $pythonVersion = python --version
    Write-Success "Python $pythonVersion found"
    
    # Check Node.js
    Write-Info "Checking Node.js installation..."
    if (-not (Test-Command "node")) {
        Write-Error "Node.js is not installed. Please install Node.js 18+"
        exit 1
    }
    $nodeVersion = node --version
    Write-Success "Node.js $nodeVersion found"
    
    # Create virtual environment
    Write-Info "Creating Python virtual environment..."
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
        Write-Success "Virtual environment created"
    } else {
        Write-Warning "Virtual environment already exists"
    }
    
    # Activate virtual environment
    $activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
    & $activateScript
    
    # Install Python dependencies
    Write-Info "Installing Python dependencies..."
    python -m pip install --upgrade pip | Out-Null
    python -m pip install -r (Join-Path $BackendDir "requirements.txt") | Out-Null
    Write-Success "Python dependencies installed"
    
    # Install frontend dependencies
    Write-Info "Installing frontend dependencies..."
    Set-Location $FrontendDir
    npm install | Out-Null
    Write-Success "Frontend dependencies installed"
    
    Set-Location $ProjectRoot
    
    # Check for .env file
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        if (Test-Path ".env.template") {
            Write-Info "Copying .env.template to .env..."
            Copy-Item ".env.template" ".env"
            Write-Warning "Please update .env with your Azure resource values"
        }
    } else {
        Write-Success ".env file found"
    }
    
    Write-Header "Setup Complete!"
    Write-Host "To start development, run: " -NoNewline
    Write-Host ".\scripts\local_dev.ps1" -ForegroundColor Green
    Write-Host "Or start individually:"
    Write-Host "  Backend:  " -NoNewline
    Write-Host ".\scripts\local_dev.ps1 -Command backend" -ForegroundColor Green
    Write-Host "  Frontend: " -NoNewline
    Write-Host ".\scripts\local_dev.ps1 -Command frontend" -ForegroundColor Green
}

# =============================================================================
# Environment Generation Function
# =============================================================================

function Invoke-EnvGeneration {
    Write-Header "Generating Environment Variables from Azure"
    
    Set-Location $ProjectRoot
    
    Ensure-AzureLogin
    
    # If using azd
    if ((Test-Command "azd") -and (Test-Path "azure.yaml")) {
        Write-Info "Azure Developer CLI detected. Generating .env from azd..."
        try {
            $envValues = azd env get-values 2>$null
            if ($envValues) {
                $envValues | Out-File ".env.azd" -Encoding UTF8
                Write-Success "Environment variables exported to .env.azd"
                
                Write-Info "Merging with .env..."
                if (Test-Path ".env") {
                    Copy-Item ".env" ".env.backup"
                    $existingEnv = Get-Content ".env"
                    $newEnv = Get-Content ".env.azd"
                    
                    foreach ($line in $newEnv) {
                        $key = $line.Split('=')[0]
                        if (-not ($existingEnv -match "^$key=")) {
                            Add-Content ".env" $line
                        }
                    }
                } else {
                    Move-Item ".env.azd" ".env"
                }
                Remove-Item ".env.azd" -ErrorAction SilentlyContinue
                Write-Success "Environment variables merged"
            }
        } catch {
            Write-Warning "Could not export from azd"
        }
    } else {
        Write-Warning "Azure Developer CLI not found or no azure.yaml"
        Write-Info "Please manually update .env with your Azure resource values"
        
        if (-not (Test-Path ".env") -and (Test-Path ".env.template")) {
            Copy-Item ".env.template" ".env"
            Write-Info "Created .env from template"
        }
    }
    
    Write-Success "Environment setup complete"
    Write-Warning "Review .env and ensure all required values are set"
}

# =============================================================================
# Backend Start Function
# =============================================================================

function Start-Backend {
    Write-Header "Starting Backend Server"
    
    Set-Location $ProjectRoot
    
    # Check for .env
    if (-not (Test-Path ".env")) {
        Write-Error ".env file not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    # Ensure Azure roles
    Ensure-AzureLogin
    Ensure-AzureAIUserRole
    Ensure-CosmosDBRole
    Ensure-StorageRole
    
    # Activate virtual environment
    if (Test-Path ".venv") {
        $activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
        & $activateScript
        Write-Success "Virtual environment activated"
    } else {
        Write-Error "Virtual environment not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    # Set environment variables
    $env:PYTHONPATH = $BackendDir
    $env:DOTENV_PATH = Join-Path $ProjectRoot ".env"
    
    # Load .env file
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Strip surrounding quotes (single or double)
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            Set-Item -Path "env:$name" -Value $value
        }
    }
    
    Write-Info "Starting Quart backend on port $BackendPort..."
    Write-Info "API will be available at: http://localhost:$BackendPort"
    Write-Info "Health check: http://localhost:$BackendPort/api/health"
    Write-Host ""
    
    Set-Location $BackendDir
    
    # Use hypercorn for async support
    if (Test-Command "hypercorn") {
        hypercorn app:app --bind "0.0.0.0:$BackendPort" --reload
    } else {
        python -m quart --app app:app run --host 0.0.0.0 --port $BackendPort --reload
    }
}

# =============================================================================
# Frontend Start Function
# =============================================================================

function Start-Frontend {
    Write-Header "Starting Frontend Development Server"
    
    Set-Location $FrontendDir
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Error "Node modules not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    Write-Info "Starting Vite dev server on port $FrontendPort..."
    Write-Info "Frontend will be available at: http://localhost:$FrontendPort"
    Write-Info "API requests will proxy to: http://localhost:$BackendPort"
    Write-Host ""
    
    npm run dev
}

# =============================================================================
# Start Both (using Jobs)
# =============================================================================

function Start-All {
    Write-Header "Starting Full Development Environment"
    
    Set-Location $ProjectRoot
    
    # Check prerequisites
    if (-not (Test-Path ".env")) {
        Write-Error ".env file not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    if (-not (Test-Path ".venv")) {
        Write-Error "Virtual environment not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Error "Frontend dependencies not found. Run: .\scripts\local_dev.ps1 -Command setup"
        exit 1
    }
    
    # Ensure Azure roles
    Ensure-AzureLogin
    Ensure-AzureAIUserRole
    Ensure-CosmosDBRole
    Ensure-StorageRole
    
    Write-Info "Starting backend and frontend in parallel..."
    Write-Info ""
    Write-Info "Services:"
    Write-Info "  Backend API:  http://localhost:$BackendPort"
    Write-Info "  Frontend:     http://localhost:$FrontendPort"
    Write-Info ""
    Write-Info "Press Ctrl+C to stop all services"
    Write-Host ""
    
    # Start backend as a job
    $backendJob = Start-Job -ScriptBlock {
        param($ProjectRoot, $BackendDir, $BackendPort)
        Set-Location $ProjectRoot
        
        # Activate venv
        $activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
        & $activateScript
        
        $env:PYTHONPATH = $BackendDir
        $env:DOTENV_PATH = Join-Path $ProjectRoot ".env"
        
        # Load .env
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Strip surrounding quotes (single or double)
                if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                Set-Item -Path "env:$name" -Value $value
            }
        }
        
        Set-Location $BackendDir
        python -m quart --app app:app run --host 0.0.0.0 --port $BackendPort --reload
    } -ArgumentList $ProjectRoot, $BackendDir, $BackendPort
    
    # Give backend time to start
    Start-Sleep -Seconds 2
    
    # Start frontend as a job
    $frontendJob = Start-Job -ScriptBlock {
        param($FrontendDir)
        Set-Location $FrontendDir
        npm run dev
    } -ArgumentList $FrontendDir
    
    try {
        # Monitor jobs and output their results
        while ($true) {
            Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
            Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
            
            if ($backendJob.State -eq 'Failed' -or $frontendJob.State -eq 'Failed') {
                Write-Error "One of the services failed"
                break
            }
            
            Start-Sleep -Milliseconds 500
        }
    } finally {
        # Cleanup jobs on exit
        Write-Info "Stopping all services..."
        Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
        Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
    }
}

# =============================================================================
# Build Function
# =============================================================================

function Invoke-Build {
    Write-Header "Building for Production"
    
    Set-Location $FrontendDir
    
    Write-Info "Building frontend..."
    npm run build
    
    Write-Success "Build complete!"
    Write-Info "Static files are in: $SrcDir\static"
}

# =============================================================================
# Clean Function
# =============================================================================

function Invoke-Clean {
    Write-Header "Cleaning Development Environment"
    
    Set-Location $ProjectRoot
    
    Write-Info "Removing Python cache..."
    Get-ChildItem -Path . -Include "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Include "*.pyc" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Info "Removing node_modules..."
    Remove-Item -Path (Join-Path $FrontendDir "node_modules") -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Info "Removing build artifacts..."
    Remove-Item -Path (Join-Path $SrcDir "static") -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Success "Clean complete!"
}

# =============================================================================
# Help Function
# =============================================================================

function Show-Help {
    Write-Host "Content Generation Accelerator - Local Development" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\local_dev.ps1 [-Command <command>]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  setup     Set up virtual environment and install dependencies"
    Write-Host "  env       Generate .env file from Azure resources"
    Write-Host "  backend   Start only the backend server"
    Write-Host "  frontend  Start only the frontend dev server"
    Write-Host "  all       Start both backend and frontend (default)"
    Write-Host "  build     Build frontend for production"
    Write-Host "  clean     Remove cache and build artifacts"
    Write-Host "  help      Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  BACKEND_PORT   Backend port (default: 5000)"
    Write-Host "  FRONTEND_PORT  Frontend port (default: 3000)"
}

# =============================================================================
# Main Script
# =============================================================================

switch ($Command) {
    "setup" { Invoke-Setup }
    "env" { Invoke-EnvGeneration }
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "all" { Start-All }
    "build" { Invoke-Build }
    "clean" { Invoke-Clean }
    "help" { Show-Help }
    default { Start-All }
}
