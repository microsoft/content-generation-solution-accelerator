#!/usr/bin/env python3
"""
Update an Azure Container Instance with agent name environment variables.

Called by the postprovision hook ONLY after successful agent creation.
Fetches the current ACI definition via Azure REST API, appends the agent
name env vars, and PUTs the updated definition back.

Usage:
    python update_aci_agent_vars.py \
        --resource_group <rg> \
        --aci_name <name> \
        --solution_name <suffix> \
        --subscription_id <sub>
"""

import argparse
import json
import platform
import subprocess
import sys

ACI_API_VERSION = "2023-05-01"

# Read-only properties that must be stripped before PUT
READONLY_CONTAINER_PROPS = ("instanceView",)
READONLY_ROOT_PROPS = ("provisioningState", "instanceView")
# Properties unsupported by the stable API version
UNSUPPORTED_PROPS = (
    "customProvisioningTimeoutInSeconds",
    "provisioningTimeoutInSeconds",
    "isCustomProvisioningTimeout",
    "isCreatedFromStandbyPool",
)


def _az_rest(method: str, uri: str, body: str | None = None) -> dict | None:
    """Call `az rest` and return parsed JSON (or None on non-JSON responses)."""
    cmd = ["az", "rest", "--method", method, "--uri", uri]
    if body is not None:
        cmd += ["--body", body]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            shell=(platform.system() == "Windows"))
    if result.returncode != 0:
        print(f"ERROR: az rest {method} failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    if result.stdout.strip():
        return json.loads(result.stdout)
    return None


def _strip_keys(obj, keys_to_strip: set):
    """Recursively remove specified keys from a nested dict/list structure."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in keys_to_strip:
                del obj[key]
            else:
                _strip_keys(obj[key], keys_to_strip)
    elif isinstance(obj, list):
        for item in obj:
            _strip_keys(item, keys_to_strip)


def main() -> None:
    p = argparse.ArgumentParser(description="Inject agent env vars into an ACI container group")
    p.add_argument("--resource_group", required=True)
    p.add_argument("--aci_name", required=True)
    p.add_argument("--solution_name", required=True)
    p.add_argument("--subscription_id", required=True)
    args = p.parse_args()

    sn = args.solution_name
    base_uri = (
        f"/subscriptions/{args.subscription_id}"
        f"/resourceGroups/{args.resource_group}"
        f"/providers/Microsoft.ContainerInstance/containerGroups/{args.aci_name}"
        f"?api-version={ACI_API_VERSION}"
    )

    # 1. GET current container group definition
    print(f"Fetching ACI definition for {args.aci_name}...")
    aci = _az_rest("GET", base_uri)
    if not aci:
        print("ERROR: Empty response from ACI GET", file=sys.stderr)
        sys.exit(1)

    # 2. Build the agent name env vars
    agent_vars = [
        {"name": "AGENT_NAME_TRIAGE", "value": f"CG-TriageAgent-{sn}"},
        {"name": "AGENT_NAME_PLANNING", "value": f"CG-PlanningAgent-{sn}"},
        {"name": "AGENT_NAME_RESEARCH", "value": f"CG-ResearchAgent-{sn}"},
        {"name": "AGENT_NAME_TEXT_CONTENT", "value": f"CG-TextContentAgent-{sn}"},
        {"name": "AGENT_NAME_IMAGE_CONTENT", "value": f"CG-ImageContentAgent-{sn}"},
        {"name": "AGENT_NAME_COMPLIANCE", "value": f"CG-ComplianceAgent-{sn}"},
        {"name": "AGENT_NAME_RAI", "value": f"CG-RAIAgent-{sn}"},
        {"name": "AGENT_NAME_TITLE", "value": f"CG-TitleAgent-{sn}"},
    ]

    # 3. Merge with existing env vars (skip duplicates by name)
    container_props = aci["properties"]["containers"][0]["properties"]
    existing_vars = container_props.get("environmentVariables", [])
    existing_names = {v["name"] for v in existing_vars}
    for var in agent_vars:
        if var["name"] not in existing_names:
            existing_vars.append(var)
    container_props["environmentVariables"] = existing_vars

    # 4. Strip read-only / unsupported properties that ARM rejects on PUT
    props = aci.get("properties", {})
    for key in READONLY_ROOT_PROPS:
        props.pop(key, None)
    for key in UNSUPPORTED_PROPS:
        props.pop(key, None)
    for container in props.get("containers", []):
        c_props = container.get("properties", {})
        for key in READONLY_CONTAINER_PROPS:
            c_props.pop(key, None)
        for key in UNSUPPORTED_PROPS:
            c_props.pop(key, None)

    # Also do a recursive sweep to catch the property at any nesting level
    _strip_keys(aci, set(READONLY_ROOT_PROPS) | set(READONLY_CONTAINER_PROPS) | set(UNSUPPORTED_PROPS))

    # 5. PUT the updated definition
    body = json.dumps(aci, separators=(",", ":"))
    print(f"Updating ACI {args.aci_name} with {len(agent_vars)} agent env vars...")
    _az_rest("PUT", base_uri, body)
    print("ACI updated successfully with agent environment variables.")


if __name__ == "__main__":
    main()
