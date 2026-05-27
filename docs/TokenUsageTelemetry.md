# Token Usage Telemetry & Dashboard

The Content Generation backend emits **per-request, per-agent, and per-model**
LLM token-usage metrics to **Azure Application Insights** as custom events.
This page describes what is emitted, how to enable it, and how to visualize it.

## What is emitted

Three custom events are sent on every request that consumes LLM tokens
(see `src/backend/llm_token_telemetry.py`):

| Event | When | Custom dimensions |
|---|---|---|
| `LLM_Token_Usage_Summary` | Once per request | `total_input_tokens`, `total_output_tokens`, `total_tokens`, `agent_count`, `model_count`, `user_id`, `conversation_id`, `source` |
| `LLM_Agent_Token_Usage` | Per agent that ran | `agent_name`, `model_deployment_name`, `input_tokens`, `output_tokens`, `total_tokens`, `user_id`, `conversation_id`, `source` |
| `LLM_Model_Token_Usage` | Per model deployment used | `model_deployment_name`, `input_tokens`, `output_tokens`, `total_tokens`, `user_id`, `conversation_id`, `source` |

**Agents covered:** `triage_agent`, `planning_agent`, `research_agent`,
`text_content_agent`, `image_content_agent`, `compliance_agent`, `rai_agent`.

**Sources** (carried in the `source` dimension):
- `process_message` — main HandoffBuilder workflow
- `send_user_response` — workflow continuations
- `parse_brief` — RAI + planning agent calls
- `generate_content` — text/image/compliance agent calls
- `regenerate_image` — direct-mode image agent
- `foundry_image_generation` — direct REST call to Azure OpenAI Image API

> **Note:** All numeric values are stored as strings in `customDimensions`
> (App Insights requirement). Always cast with `tolong()` / `toint()` in KQL.

## Enabling telemetry

Set `APPLICATIONINSIGHTS_CONNECTION_STRING` in the backend environment.
Application Insights wiring is already configured in `src/backend/app.py`
via `configure_azure_monitor()`. If the env var is unset, no telemetry is
sent to Application Insights — `_RequestTokenTracker.flush()` short-circuits
the network emit path. Aggregated per-request totals are still written to
the local logger at `INFO` level (one `[TOKEN USAGE] ...` line per flush)
so token tracking remains useful for local debugging without a connection
string.

When deploying via `azd up`, the Bicep templates create an Application
Insights instance and pass the connection string to the App Service.

## Viewing the dashboard

A ready-to-use KQL query pack lives at:

```
infra/dashboards/token-usage-queries.kql
```

It contains 12 queries:

1. Overall token usage (last 24h)
2. Token usage by agent
3. Token usage by model deployment
4. Top users by token spend (last 7d)
5. Hourly trend (last 24h, time chart)
6. Per-agent daily trend (last 7d, time chart)
7. Per-model daily trend (last 7d, time chart)
8. Token usage by request source
9. Top conversations by token spend
10. Avg input/output token ratio per agent
11. Heaviest individual requests
12. OpenTelemetry-instrumented OpenAI dependency calls (cross-check)

### Run a query

1. Open the **Application Insights** resource in the Azure portal.
2. Go to **Monitoring → Logs**.
3. Paste any query from the file above and click **Run**.

## Verifying locally

After triggering a brief generation in a dev environment with a valid
`APPLICATIONINSIGHTS_CONNECTION_STRING`, custom events typically appear in
Application Insights within ~2 minutes:

```kusto
customEvents
| where timestamp > ago(15m)
| where name startswith "LLM_"
| project timestamp, name, customDimensions
| order by timestamp desc
```

## Design notes

- **Best-effort by design.** Every extraction and every emit call is wrapped
  in `try/except`. Telemetry failures are logged at `DEBUG`/`WARNING` and
  never break the user flow.
- **No PII.** Only `user_id` and `conversation_id` are included as
  dimensions; no prompt or response text is sent.
- **Out of scope (intentional).** The current implementation does not persist
  token totals to Cosmos DB and does not push real-time updates to the
  frontend. Operators add cost-estimation queries as needed by multiplying
  token counts by their negotiated per-1K-token rates.
