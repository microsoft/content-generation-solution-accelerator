# Add monitoring after deployment (standalone)

Use this when the main accelerator was deployed with
`enableMonitoring=false` and you now want to add **Log Analytics + Application
Insights** without re-running the full `azd up`.

Resource names match `infra/main.bicep` exactly:

- Log Analytics: `log-${solutionSuffix}`
- App Insights:  `appi-${solutionSuffix}`

…where `solutionSuffix = toLower("${solutionName}${solutionUniqueText}")`
(symbols stripped). So after this runs, the rest of the solution can find
them by name with no further changes.

## Parameters

| Name | Required | Description |
| --- | --- | --- |
| `solutionName` | Yes | Same value you passed to `main.bicep` / `azd` (3-15 chars). |
| `solutionUniqueText` | No | Same as main; defaults to the same `uniqueString(...)` expression. Override only if the original deployment used a custom value. |
| `location` | No | Region for the resources. Defaults to RG location. |
| `tags` | No | Tags applied to both resources. |
| `retentionInDays` | No | Defaults to 365 (matches main). |

## Deploy

```bash
RG="<your-existing-rg>"
SOLUTION_NAME="<same as original azd env name / main solutionName>"

az deployment group create \
  --resource-group "$RG" \
  --name monitoring \
  --template-file infra/monitoring/monitoring.bicep \
  --parameters solutionName="$SOLUTION_NAME"
```

Capture the outputs:

```bash
APPI_ID=$(az deployment group show -g "$RG" -n monitoring \
  --query properties.outputs.applicationInsightsResourceId.value -o tsv)
APPI_CS=$(az deployment group show -g "$RG" -n monitoring \
  --query properties.outputs.applicationInsightsConnectionString.value -o tsv)
```

## Wire the app to send telemetry

Set the connection string on the running app(s):

```bash
# App Service example
az webapp config appsettings set -g "$RG" -n <app-name> \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="$APPI_CS"

# Container App example
az containerapp update -g "$RG" -n <app-name> \
  --set-env-vars APPLICATIONINSIGHTS_CONNECTION_STRING="$APPI_CS"
```

Or, if managed via azd:

```bash
azd env set APPLICATIONINSIGHTS_CONNECTION_STRING "$APPI_CS"
azd deploy   # re-deploy app code only, no infra changes
```

## Idempotency / re-runs

Re-running this deployment against the same RG is safe — AVM modules use
stable names so existing resources are updated in place rather than
duplicated.

## Caveat

This template **only** creates Log Analytics + App Insights. It does **not**
re-wire `main.bicep`'s diagnostic settings on other resources (Storage, Key
Vault, Cosmos, etc.) which are normally created by `main.bicep` when
`enableMonitoring=true`. If you need those too, the cleanest fix is still to
re-run `azd provision` with `enableMonitoring=true` — Bicep will add only
the missing diagnostic settings without recreating existing resources.
