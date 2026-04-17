import logging
import os
from azure.monitor.events.extension import track_event


def track_event_if_configured(event_name: str, event_data: dict):
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        track_event(event_name, event_data)
    else:
        logging.warning(f"Skipping track_event for {event_name} as Application Insights is not configured")
