# Token Usage Workbook (standalone deployment)

This folder contains a **standalone** Bicep template that deploys the
**Token Usage** Application Insights workbook used by the Content Generation
Solution Accelerator.

The workbook visualises the custom events emitted by the orchestrator:

- `LLM_Token_Usage_Summary`
- `LLM_Agent_Token_Usage`
- `LLM_Model_Token_Usage`

It is deployed **separately** from `infra/main.bicep` /
`infra/main_custom.bicep` so it can target an Application Insights instance
that lives in a **different resource group** (or subscription) from the rest
of the accelerator — for example, a shared observability workspace.

## Files

| File | Purpose |
| --- | --- |
| `workbook.bicep` | Bicep template that creates the workbook resource. |
| `../dashboards/token-usage-workbook.json` | Serialized workbook definition (loaded by the template). |

## Parameters

| Name | Required | Description |
| --- | --- | --- |
| `applicationInsightsResourceId` | No | Full resource ID of the Application Insights instance to query. Defaults to `Azure Monitor` (unbound — pick the instance later in the portal). Re-deploy with a real ID to (re)bind. |
| `workbookName` | No | Stable GUID name. Keep the default so re-deployments update the SAME workbook even when the App Insights ID changes. |
| `location` | No | Azure region for the workbook resource. Defaults to the resource group location. |
| `displayName` | No | Display name in the Azure portal. Defaults to `Token Usage`. |
| `tags` | No | Tags applied to the workbook resource. |

## Bind / change Application Insights after deployment

Because `workbookName` is stable by default, you can:

1. **Deploy now without an App Insights ID** — workbook is created in
   "Azure Monitor" scope and shows up under *Monitor → Workbooks*. Open it,
   then use the resource picker at the top to point at any App Insights
   instance ad-hoc.
2. **Bind / re-bind later by re-deploying** with a new
   `applicationInsightsResourceId`. The same workbook resource is updated
   in place; no duplicate is created.

```bash
# 1) Deploy unbound first
az deployment group create \
  --resource-group rg-observability \
  --template-file infra/workbook/workbook.bicep

# 2) Later, bind it to App Insights instance A
az deployment group create \
  --resource-group rg-observability \
  --template-file infra/workbook/workbook.bicep \
  --parameters applicationInsightsResourceId="$APPI_ID_A"

# 3) Switch it to App Insights instance B - same workbook, new source
az deployment group create \
  --resource-group rg-observability \
  --template-file infra/workbook/workbook.bicep \
  --parameters applicationInsightsResourceId="$APPI_ID_B"
```

You can also change the binding from the **Azure portal**: open the
workbook → *Edit* → *Settings* → change the linked resource → *Save*.

## Deploy with Azure CLI

```bash
# Resource group where the WORKBOOK will live
WORKBOOK_RG="rg-observability"

# Full resource ID of the EXISTING Application Insights instance
# (can be in a different resource group / subscription)
APPI_ID="/subscriptions/<sub-id>/resourceGroups/<appi-rg>/providers/Microsoft.Insights/components/<appi-name>"

az deployment group create \
  --resource-group "$WORKBOOK_RG" \
  --template-file infra/workbook/workbook.bicep \
  --parameters applicationInsightsResourceId="$APPI_ID"
```

## Deploy with Azure PowerShell

```powershell
$workbookRg = "rg-observability"
$appiId = "/subscriptions/<sub-id>/resourceGroups/<appi-rg>/providers/Microsoft.Insights/components/<appi-name>"

New-AzResourceGroupDeployment `
  -ResourceGroupName $workbookRg `
  -TemplateFile infra/workbook/workbook.bicep `
  -applicationInsightsResourceId $appiId
```

## Notes

- The workbook resource itself can live in any resource group; only the
  `sourceId` it points at needs to be a valid Application Insights resource
  ID. This is what allows the workbook to fetch token-count telemetry from
  Application Insights deployed elsewhere.
- The workbook name is a stable GUID derived from the resource group ID and
  a fixed seed (`'token-usage-workbook'`), so re-running the deployment updates
  the same workbook in place rather than creating duplicates. The Application
  Insights resource ID is **not** part of the name, which lets you re-point
  the workbook at a different App Insights instance without renaming it.
- Required permission: `Microsoft.Insights/workbooks/write` on the target
  resource group. **No** permissions are required on the Application Insights
  resource group at deployment time — the workbook only references it; the
  user *viewing* the workbook needs read access to the App Insights instance.
