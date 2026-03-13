## [Optional]: Customizing resource names

By default this template will use the environment name as the prefix to prevent naming collisions within Azure. The parameters below show the default values. You only need to run the statements below if you need to change the values.

> To override any of the parameters, run `azd env set <PARAMETER_NAME> <VALUE>` before running `azd up`. On the first azd command, it will prompt you for the environment name. Be sure to choose 3-15 characters alphanumeric unique name.

## Parameters

| Name                                   | Type    | Default Value                | Purpose                                                                       |
| -------------------------------------- | ------- | ---------------------------- | ----------------------------------------------------------------------------- |
| `AZURE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for resource deployment. Allowed: `australiaeast`, `centralus`, `eastasia`, `eastus`, `eastus2`, `japaneast`, `northeurope`, `southeastasia`, `swedencentral`, `uksouth`, `westus`, `westus3`. |
| `AZURE_ENV_NAME`                       | string  | `contentgen`               | Sets the environment name prefix for all Azure resources (3-15 characters).   |
| `secondaryLocation`                    | string  | `uksouth`                  | Specifies a secondary Azure region for database creation.                     |
| `gptModelName`                         | string  | `gpt-5.1`                 | Specifies the GPT model name to deploy.                                       |
| `gptModelVersion`                      | string  | `2025-11-13`               | Sets the GPT model version.                                                   |
| `gptModelDeploymentType`               | string  | `GlobalStandard`           | Defines the model deployment type (allowed: `Standard`, `GlobalStandard`).    |
| `gptModelCapacity`                     | integer | `150`                      | Sets the GPT model token capacity (minimum: `10`).                            |
| `imageModelChoice`                     | string  | `gpt-image-1-mini`             | Image model to deploy (allowed: `gpt-image-1-mini`, `gpt-image-1.5`, `none`). |
| `imageModelCapacity`                   | integer | `1`                        | Sets the image model deployment capacity in RPM (minimum: `1`).               |
| `azureOpenaiAPIVersion`                | string  | `2025-01-01-preview`       | Specifies the API version for Azure OpenAI service.                           |
| `AZURE_ENV_OPENAI_LOCATION`           | string  | `<User selects during deployment>` | Sets the Azure region for OpenAI resource deployment.                         |
| `AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID` | string  | `""`                       | Reuses an existing Log Analytics Workspace instead of creating a new one.     |
| `AZURE_EXISTING_AI_PROJECT_RESOURCE_ID`| string  | `""`                       | Reuses an existing AI Foundry Project instead of creating a new one.          |
| `ACR_NAME`                             | string  | `contentgencontainerreg`   | Sets the existing Azure Container Registry name (without `.azurecr.io`).      |
| `IMAGE_TAG`                            | string  | `latest`                   | Sets the container image tag (e.g., `latest`, `dev`, `hotfix`).               |

## How to Set a Parameter

To customize any of the above values, run the following command **before** `azd up`:

```bash
azd env set <PARAMETER_NAME> <VALUE>
```

**Examples:**

```bash
azd env set AZURE_LOCATION westus2
azd env set gptModelName gpt-5.1
azd env set gptModelDeploymentType Standard
azd env set imageModelChoice gpt-image-1-mini
azd env set ACR_NAME contentgencontainerreg
```
