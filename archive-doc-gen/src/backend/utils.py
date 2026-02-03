import dataclasses
import json
import logging
import os
from enum import Enum
from typing import List
import requests
import uuid
import time

AZURE_SEARCH_PERMITTED_GROUPS_COLUMN = os.environ.get(
    "AZURE_SEARCH_PERMITTED_GROUPS_COLUMN"
)


class ChatType(Enum):
    TEMPLATE = "template"
    BROWSE = "browse"


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


async def format_as_ndjson(r):
    try:
        async for event in r:
            yield json.dumps(event, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception(
            "Exception while generating response stream: %s", error)
        yield json.dumps({"error": str(error)})


def parse_multi_columns(columns: str) -> list:
    if "|" in columns:
        return columns.split("|")
    else:
        return columns.split(",")


def fetchUserGroups(userToken, nextLink=None):
    # Recursively fetch group membership
    if nextLink:
        endpoint = nextLink
    else:
        endpoint = "https://graph.microsoft.com/v1.0/me/transitiveMemberOf?$select=id"

    headers = {"Authorization": "bearer " + userToken}
    try:
        r = requests.get(endpoint, headers=headers)
        if r.status_code != 200:
            logging.error(
                f"Error fetching user groups: {r.status_code} {r.text}")
            return []

        r = r.json()
        if "@odata.nextLink" in r:
            nextLinkData = fetchUserGroups(userToken, r["@odata.nextLink"])
            r["value"].extend(nextLinkData)

        return r["value"]
    except Exception as e:
        logging.error(f"Exception in fetchUserGroups: {e}")
        return []


def generateFilterString(userToken):
    # Get list of groups user is a member of
    userGroups = fetchUserGroups(userToken)

    # Construct filter string
    if not userGroups:
        logging.debug("No user groups found")

    group_ids = ", ".join([obj["id"] for obj in userGroups])
    return f"{AZURE_SEARCH_PERMITTED_GROUPS_COLUMN}/any(g:search.in(g, '{group_ids}'))"


def format_non_streaming_response(chunk, history_metadata):
    from backend.settings import app_settings
    response_obj = {
        "id": str(uuid.uuid4()),
        "model": app_settings.azure_ai.agent_model_deployment_name,
        "created": int(time.time()),
        "choices": [{
            "messages": []
        }],
        "history_metadata": history_metadata
    }
    has_data = False

    if "answer" in chunk and chunk["answer"]:
        has_data = True
        response_obj["choices"][0]["messages"].append({
            "role": "assistant",
            "content": chunk["answer"]
        })

    if "citations" in chunk and chunk["citations"]:
        has_data = True
        response_obj["choices"][0]["messages"].append({
            "role": "tool",
            "content": chunk["citations"]
        })

    if not has_data:
        return {}
    return response_obj


def format_stream_response(chunk, history_metadata):
    from backend.settings import app_settings
    response_obj = {
        "id": str(uuid.uuid4()),
        "model": app_settings.azure_ai.agent_model_deployment_name,
        "created": int(time.time()),
        "choices": [{
            "messages": []
        }],
        "history_metadata": history_metadata
    }
    has_data = False

    if "answer" in chunk and chunk["answer"]:
        has_data = True
        response_obj["choices"][0]["messages"].append({
            "role": "assistant",
            "content": chunk["answer"]
        })

    if "citations" in chunk and chunk["citations"]:
        has_data = True
        response_obj["choices"][0]["messages"].append({
            "role": "tool",
            "content": chunk["citations"]
        })

    if not has_data:
        return {}
    return response_obj


def comma_separated_string_to_list(s: str) -> List[str]:
    """
    Split comma-separated values into a list.
    """
    return s.strip().replace(" ", "").split(",")


def configure_logging(logging_settings):
    """
    Configure logging based on the provided logging settings.

    Args:
        logging_settings: Instance of _LoggingSettings containing logging configuration
    """
    # Configure basic logging
    logging.basicConfig(
        level=logging_settings.get_basic_log_level(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )

    azure_log_level = logging_settings.get_package_log_level()
    for logger_name in logging_settings.logging_packages or []:
        logging.getLogger(logger_name).setLevel(azure_log_level)

    logging.info(f"Logging configured - Basic: {logging_settings.basic_logging_level}, Azure packages: {logging_settings.package_logging_level}, Packages: {logging_settings.logging_packages}")
