from mstrio.api import administration as admin_api
from mstrio.api import events as events_api
from mstrio.connection import Connection
from mstrio.helpers import IServerError, MstrException

# Stable ID of the "Load Metadata Object Telemetry" event, pre-shipped on
# every Strategy One install via LoadMetadataObjectTelemetry.bin delta script.
_LOAD_OBJECT_TELEMETRY_EVENT_ID = '1EDCE69F4474A420920D7F99AFF01080'


def get_telemetry_status(connection: Connection) -> str:
    """Retrieves the current status of the telemetry pipeline.

    The endpoint returns a short status string (e.g. ``"OK"``) as
    ``text/plain``; this helper returns it stripped.

    Args:
        connection (Connection): Strategy connection object.

    Returns:
        str: Telemetry pipeline status string (e.g. ``"OK"``).
    """

    return admin_api.get_telemetry_status(connection).text.strip()


def send_telemetry(
    connection: Connection,
    client_source: int,
    telemetry_logs_by_topics: list[dict],
) -> bool:
    """Sends a batch of telemetry logs to Messaging Services.

    Args:
        connection (Connection): Strategy connection object.
        client_source (int): Numeric identifier of the telemetry source.
        telemetry_logs_by_topics (list[dict]): TelemetryLogsByTopic payloads.

    Returns:
        bool: True if the server accepted the batch.
    """

    body = {
        'clientSource': client_source,
        'telemetryLogsByTopics': telemetry_logs_by_topics,
    }

    try:
        response = admin_api.send_telemetry(connection, body)
    except (IServerError, MstrException):
        return False
    return response.ok


def trigger_load_object_telemetry(connection: Connection) -> bool:
    """Triggers an immediate Load Metadata Object Telemetry operation.

    Args:
        connection (Connection): Strategy connection object.

    Returns:
        bool: True if the server accepted the trigger.
    """

    try:
        response = events_api.trigger_event(
            connection, id=_LOAD_OBJECT_TELEMETRY_EVENT_ID
        )
    except (IServerError, MstrException):
        return False
    return response.ok
