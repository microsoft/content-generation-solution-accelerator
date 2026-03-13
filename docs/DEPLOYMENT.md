# Deployment Guide

## **Pre-requisites**

To deploy this solution, ensure you have access to an [Azure subscription](https://azure.microsoft.com/free/) with the necessary permissions to create **resource groups, resources, app registrations, and assign roles at the resource group level**. This should include Contributor role at the subscription level and Role Based Access Control (RBAC) permissions at the subscription and/or resource group level.

Check the [Azure Products by Region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?products=all&regions=all) page and select a **region** where the following services are available:

- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry)
- [GPT Model Capacity](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
- [Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Azure Container Instance](https://learn.microsoft.com/en-us/azure/container-instances/)
- [Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)

Here are some example regions where the services are available: East US, East US2, Australia East, UK South, France Central.

### **Important Note for PowerShell Users**

If you encounter issues running PowerShell scripts due to the policy of not being digitally signed, you can temporarily adjust the `ExecutionPolicy` by running the following command in an elevated PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This will allow the scripts to run for the current session without permanently changing your system's policy.

## Deployment Options & Steps

Pick from the options below to see step-by-step instructions for GitHub Codespaces, VS Code Dev Containers, VS Code Web, and Local Environments.

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/content-generation-solution-accelerator) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/content-generation-solution-accelerator) | [![Open in Visual Studio Code Web](https://img.shields.io/static/v1?style=for-the-badge&label=Visual%20Studio%20Code%20(Web)&message=Open&color=blue&logo=visualstudiocode&logoColor=white)](https://vscode.dev/azure/?vscode-azure-exp=foundry&agentPayload=eyJiYXNlVXJsIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvY29udGVudC1nZW5lcmF0aW9uLXNvbHV0aW9uLWFjY2VsZXJhdG9yL3JlZnMvaGVhZHMvbWFpbi9jb250ZW50LWdlbi9pbmZyYS92c2NvZGVfd2ViIiwgImluZGV4VXJsIjogIi9pbmRleC5qc29uIiwgInZhcmlhYmxlcyI6IHsiYWdlbnRJZCI6ICIiLCAiY29ubmVjdGlvblN0cmluZyI6ICIiLCAidGhyZWFkSWQiOiAiIiwgInVzZXJNZXNzYWdlIjogIiIsICJwbGF5Z3JvdW5kTmFtZSI6ICIiLCAibG9jYXRpb24iOiAiIiwgInN1YnNjcmlwdGlvbklkIjogIiIsICJyZXNvdXJjZUlkIjogIiIsICJwcm9qZWN0UmVzb3VyY2VJZCI6ICIiLCAiZW5kcG9pbnQiOiAiIn0sICJjb2RlUm91dGUiOiBbImFpLXByb2plY3RzLXNkayIsICJweXRob24iLCAiZGVmYXVsdC1henVyZS1hdXRoIiwgImVuZHBvaW50Il19) |
|---|---|---|

<details>
  <summary><b>Deploy in GitHub Codespaces</b></summary>

### GitHub Codespaces

You can run this solution using GitHub Codespaces. The button will open a web-based VS Code instance in your browser:

1. Open the solution accelerator (this may take several minutes):

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/content-generation-solution-accelerator)

2. Accept the default values on the create Codespaces page.
3. Open a terminal window if it is not already open.
4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<details>
  <summary><b>Deploy in VS Code</b></summary>

### VS Code Dev Containers

You can run this solution in VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed).
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/content-generation-solution-accelerator)

3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<details>
  <summary><b>Deploy in VS Code Web</b></summary>

### Visual Studio Code Web

You can run this solution using VS Code Web, which provides a browser-based development environment with Azure integration:

1. Open the solution accelerator:

    [![Open in Visual Studio Code Web](https://img.shields.io/static/v1?style=for-the-badge&label=Visual%20Studio%20Code%20(Web)&message=Open&color=blue&logo=visualstudiocode&logoColor=white)](https://vscode.dev/azure/?vscode-azure-exp=foundry&agentPayload=eyJiYXNlVXJsIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvY29udGVudC1nZW5lcmF0aW9uLXNvbHV0aW9uLWFjY2VsZXJhdG9yL3JlZnMvaGVhZHMvbWFpbi9jb250ZW50LWdlbi9pbmZyYS92c2NvZGVfd2ViIiwgImluZGV4VXJsIjogIi9pbmRleC5qc29uIiwgInZhcmlhYmxlcyI6IHsiYWdlbnRJZCI6ICIiLCAiY29ubmVjdGlvblN0cmluZyI6ICIiLCAidGhyZWFkSWQiOiAiIiwgInVzZXJNZXNzYWdlIjogIiIsICJwbGF5Z3JvdW5kTmFtZSI6ICIiLCAibG9jYXRpb24iOiAiIiwgInN1YnNjcmlwdGlvbklkIjogIiIsICJyZXNvdXJjZUlkIjogIiIsICJwcm9qZWN0UmVzb3VyY2VJZCI6ICIiLCAiZW5kcG9pbnQiOiAiIn0sICJjb2RlUm91dGUiOiBbImFpLXByb2plY3RzLXNkayIsICJweXRob24iLCAiZGVmYXVsdC1henVyZS1hdXRoIiwgImVuZHBvaW50Il19)

2. Sign in with your Azure account when prompted.
3. Select the subscription where you want to deploy the solution.
4. Wait for the environment to initialize (includes all deployment tools).
5. Once the solution opens, the **AI Foundry terminal** will automatically start. If prompted, choose "**Overwrite with versions from template**" and provide a unique environment name.
6. **Authenticate with Azure** (VS Code Web requires device code authentication):
   
    ```shell
    azd auth login --use-device-code
    ```
    
    > **Note:** In VS Code Web environment, the regular `azd auth login` command may fail. Use the `--use-device-code` flag to authenticate via device code flow. Follow the prompts in the terminal to complete authentication.
   
7. Continue with the [deploying steps](#deploying-with-azd).

</details>

<details>
  <summary><b>Deploy in your local Environment</b></summary>

### Local Environment

If you're not using one of the above options for opening the project, then you'll need to:

1. Make sure the following tools are installed:
    - [PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.5) <small>(v7.0+)</small> - available for Windows, macOS, and Linux.
    - [Azure Developer CLI (azd)](https://aka.ms/install-azd) <small>(v1.15.0+)</small>
    - [Python 3.11+](https://www.python.org/downloads/)
    - [Node.js 18+](https://nodejs.org/)
    - [Docker Desktop](https://www.docker.com/products/docker-desktop/)
    - [Git](https://git-scm.com/downloads)

2. Clone the repository or download the project code via command-line:

    ```shell
    azd init -t microsoft/content-generation-solution-accelerator/
    ```

3. Open the project folder in your terminal or editor.
4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<br/>

Consider the following settings during your deployment to modify specific settings:

<details>
  <summary><b>Configurable Deployment Settings</b></summary>

When you start the deployment, most parameters will have **default values**, but you can update the following settings:

| **Setting**                                 | **Description**                                                                                           | **Default value**      |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------- |
| **Azure Region**                            | The region where resources will be created.                                                               | *(empty)*              |
| **Environment Name**                        | A **3–20 character alphanumeric value** used to generate a unique ID to prefix the resources.             | env\_name              |
| **GPT Model**                               | Choose from **gpt-4, gpt-4o, gpt-4o-mini, gpt-5.1**.                                                               | gpt-5.1           |
| **GPT Model Version**                       | The version of the selected GPT model.                                                                    | 2025-11-13            |
| **OpenAI API Version**                      | The Azure OpenAI API version to use.                                                                      | 2025-01-01-preview     |
| **GPT Model Deployment Capacity**           | Configure capacity for **GPT models** (in thousands).                                                     | 150k                    |
| **Image Model**                            | Choose from **gpt-image-1-mini, gpt-image-1.5**                                                                          | gpt-image-1-mini             |
| **Image Tag**                               | Docker image tag to deploy. Common values: `latest`, `dev`, `hotfix`.                                     | latest                 |
| **Existing Log Analytics Workspace**        | To reuse an existing Log Analytics Workspace ID.                                                          | *(empty)*              |
| **Existing Azure AI Foundry Project**       | To reuse an existing Azure AI Foundry Project ID instead of creating a new one.                           | *(empty)*              |

</details>

<details>
  <summary><b>[Optional] Quota Recommendations</b></summary>

By default, the **GPT-5.1 model capacity** in deployment is set to **150k tokens**, so we recommend updating the following:

> **For GPT-5.1 - increase the capacity post-deployment for optimal performance if required.**

> **For GPT-Image-1-mini - ensure you have sufficient capacity for image generation requests.**

Depending on your subscription quota and capacity, you can adjust quota settings to better meet your specific needs.

**⚠️ Warning:** Insufficient quota can cause deployment errors. Please ensure you have the recommended capacity or request additional capacity before deploying this solution.

</details>

### Deploying with AZD

Once you've opened the project in [Codespaces](#github-codespaces), [Dev Containers](#vs-code-dev-containers), or [locally](#local-environment), you can deploy it to Azure by following the steps in the [AZD Deployment Guide](AZD_DEPLOYMENT.md).

## Post Deployment Steps

1. **Add App Authentication**
   
    Follow steps in [App Authentication](./AppAuthentication.md) to configure authentication in app service. Note: Authentication changes can take up to 10 minutes.

2. **Deleting Resources After a Failed Deployment**  
    - Follow steps in [Delete Resource Group](./DeleteResourceGroup.md) if your deployment fails and/or you need to clean up the resources.

## Troubleshooting

<details>
  <summary><b>Common Issues and Solutions</b></summary>

### 403 Forbidden from Cosmos DB

**Symptom**: Cosmos DB operations fail with 403

**Cause**: Missing Cosmos DB data plane role (not ARM role)

**Solution**: Use `az cosmosdb sql role assignment create` (not `az role assignment create`)

### SSE Streaming Not Working

**Symptom**: Long responses timeout, no streaming updates

**Causes**:
1. HTTP/2 enabled on App Service (breaks SSE)
2. Proxy timeout too short

**Solution**:
```bash
az webapp config set -g $RESOURCE_GROUP -n <app-name> --http20-enabled false
```

### Backend Not Accessible

**Symptom**: Frontend cannot reach backend API

**Cause**: VNet/DNS configuration issues

**Solution**:
1. Verify VNet integration is enabled on App Service
2. Verify private DNS zone is linked to VNet
3. Verify A record points to correct ACI IP
4. Check if ACI IP changed (run `update_backend_dns.sh`)

### Image Generation Not Working

**Symptom**: GPT-Image requests fail

**Cause**: Missing GPT-Image model deployment or incorrect endpoint

**Solution**: 
1. Verify GPT-Image-1-mini or GPT-Image-1.5 deployment exists in Azure OpenAI resource
2. Check `AZURE_OPENAI_IMAGE_MODEL` and `AZURE_OPENAI_GPT_IMAGE_ENDPOINT` environment variables

</details>

## Sample Workflow

To get started with the Content Generation solution, follow these steps:

1. **Task:** From the welcome screen, select one of the suggested prompts. Sample prompts include:
   - *"I need to create a social media post about paint products for home remodels. The campaign is titled 'Brighten Your Springtime' and the audience is new homeowners. I need marketing copy plus an image."*
   - *"Generate a social media campaign with ad copy and an image. This is for 'Back to School' and the audience is parents of school age children. Tone is playful and humorous."*

2. **Task:** Click the **"Confirm Brief"** button.
   > **Observe:** The system analyzes the creative brief to provide suggestions later.

3. **Task:** Select a product from the product list, then click **"Generate Content"**.
   > **Observe:** Enters "Thinking Process" with a "Generating Content.." spinner. Once complete, the detailed output is displayed.

## Architecture Overview

The solution consists of:

- **Backend**: Python 3.11 + Quart + Hypercorn running in Azure Container Instance (ACI) with VNet integration
- **Frontend**: React + Vite + TypeScript + Fluent UI running on Azure App Service with Node.js proxy
- **AI Services**: 
  - Azure OpenAI (GPT model for text generation)
  - Azure OpenAI (GPT Image model for image generation)
- **Data Services**:
  - Azure Cosmos DB (products catalog, conversations)
  - Azure Blob Storage (product images, generated images)
- **Networking**: 
  - Private VNet for backend container
  - App Service with VNet integration for frontend-to-backend communication
  - Private DNS zone for internal name resolution

## Security Considerations

1. **Managed Identity**: The solution uses system-assigned managed identity instead of connection strings
2. **Private VNet**: Backend runs in private subnet, not exposed to internet
3. **RBAC**: Principle of least privilege - only necessary roles are assigned
4. **No Secrets in Code**: All credentials managed through Azure identity
