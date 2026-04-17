## [Optional]: Customizing resource names

By default this template will use the environment name as the prefix to prevent naming collisions within Azure. The parameters below show the default values. You only need to run the statements below if you need to change the values.

> To override any of the parameters, run `azd env set <PARAMETER_NAME> <VALUE>` before running `azd up`. On the first azd command, it will prompt you for the environment name. Be sure to choose 3-15 characters alphanumeric unique name.

## Parameters

| Name                                   | Type    | Default Value                | Purpose                                                                       |
| -------------------------------------- | ------- | ---------------------------- | ----------------------------------------------------------------------------- |
| `AZURE_LOCATION`                       | string  | `<User selects during deployment>` | Sets the Azure region for resource deployment. Allowed: `australiaeast`, `centralus`, `eastasia`, `eastus`, `eastus2`, `japaneast`, `northeurope`, `southeastasia`, `swedencentral`, `uksouth`, `westus`, `westus3`. |
| `AZURE_ENV_NAME`                       | string  | `contentgen`               | Sets the environment name prefix for all Azure resources (3-15 characters).   |
| `AZURE_ENV_SECONDARY_LOCATION`                   | string  | `uksouth`                  | Specifies a secondary Azure region for database creation.                     |
| `AZURE_ENV_GPT_MODEL_NAME`              | string  | `gpt-5.1`                 | Specifies the GPT model name to deploy.                                       |
| `AZURE_ENV_GPT_MODEL_VERSION`                    | string  | `2025-11-13`               | Sets the GPT model version.                                                   |
| `AZURE_ENV_MODEL_DEPLOYMENT_TYPE`            | string  | `GlobalStandard`           | Defines the model deployment type (allowed: `Standard`, `GlobalStandard`).    |
| `AZURE_ENV_GPT_MODEL_CAPACITY`                   | integer | `150`                      | Sets the GPT model token capacity (minimum: `10`).                            |
| `AZURE_ENV_IMAGE_MODEL_NAME`           | string  | `gpt-image-1-mini`         | Image model to deploy (allowed: `gpt-image-1-mini`, `gpt-image-1.5`, `none`). |
| `AZURE_ENV_IMAGE_MODEL_CAPACITY`       | integer | `1`                        | Sets the image model deployment capacity in RPM (minimum: `1`).               |
| `AZURE_ENV_OPENAI_API_VERSION`            | string  | `2025-01-01-preview`       | Specifies the API version for Azure OpenAI service.                           |
| `AZURE_ENV_AI_SERVICE_LOCATION`           | string  | `<User selects during deployment>` | Sets the Azure region for OpenAI resource deployment. Allowed: `australiaeast`, `canadaeast`, `eastus2`, `japaneast`, `koreacentral`, `polandcentral`, `swedencentral`, `switzerlandnorth`, `uaenorth`, `uksouth`, `westus3`. |
| `AZURE_ENV_EXISTING_LOG_ANALYTICS_WORKSPACE_RID`   | string  | `""`                       | Reuses an existing Log Analytics Workspace instead of creating a new one.     |
| `AZURE_EXISTING_AIPROJECT_RESOURCE_ID`           | string  | `""`                       | Reuses an existing AI Foundry Project instead of creating a new one.          |
| `enableMonitoring`                     | boolean | `false`                    | Enable Log Analytics and Application Insights (WAF-aligned).                  |
| `enableScalability`                    | boolean | `false`                    | Enable auto-scaling and higher SKUs (WAF-aligned).                            |
| `enableRedundancy`                     | boolean | `false`                    | Enable zone redundancy and geo-replication (WAF-aligned).                     |
| `enablePrivateNetworking`              | boolean | `false`                    | Enable VNet integration and private endpoints (WAF-aligned).                  |
| `deployBastionAndJumpbox`              | boolean | `false`                    | Deploy Azure Bastion and jumpbox admin-path resources when private networking is enabled. |
| `AZURE_ENV_VM_SIZE`                    | string  | `""`                       | Overrides the jumpbox VM size (private networking only). Must support accelerated networking and Premium SSD. |
| `AZURE_ENV_VM_ADMIN_USERNAME`          | string  | `""`                       | Sets the jumpbox VM admin username (private networking only).                 |
| `AZURE_ENV_VM_ADMIN_PASSWORD`          | string  | `""`                       | Sets the jumpbox VM admin password. Bastion and jumpbox resources are deployed only when this is set and `deployBastionAndJumpbox=true`. |
| `AZURE_ENV_CONTAINER_REGISTRY_NAME`       | string  | `contentgencontainerreg`   | Sets the existing Azure Container Registry name (without `.azurecr.io`).      |
| `AZURE_ENV_IMAGE_TAG`                     | string  | `latest`                   | Sets the container image tag (e.g., `latest`, `dev`, `hotfix`).               |

## How to Set a Parameter

To customize any of the above values, run the following command **before** `azd up`:

```bash
azd env set <PARAMETER_NAME> <VALUE>
```

**Examples:**

```bash
azd env set AZURE_LOCATION westus2
azd env set AZURE_ENV_GPT_MODEL_NAME gpt-5.1
azd env set AZURE_ENV_MODEL_DEPLOYMENT_TYPE Standard
azd env set AZURE_ENV_IMAGE_MODEL_NAME gpt-image-1-mini
azd env set AZURE_ENV_CONTAINER_REGISTRY_NAME contentgencontainerreg
```
