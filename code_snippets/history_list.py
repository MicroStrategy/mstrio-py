"""This is the demo script to show how to manage history list messages.

Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects import Dashboard, Report
from mstrio.server.history_list import (
    HistoryList,
    bulk_send_to_history_list,
    delete_all_history_list_messages,
    get_history_list_messages_by_ids,
    list_history_list_messages,
    send_to_history_list,
    update_history_list_messages_status,
)

PROJECT_ID = $project_id
TARGET_OBJECT_ID = $target_object_id
# Use "report_definition" for a report or "document_definition" for a dashboard.
# Object must exist in the project with PROJECT_ID and be accessible by the user.
TARGET_OBJECT_TYPE = $target_object_type

# Create connection to the environment
conn = get_connection(connectionData)

# Create an instance to get its execution message ID
if TARGET_OBJECT_TYPE == "report_definition":
    report = Report(connection=conn, id=TARGET_OBJECT_ID)
    report.to_dataframe()
    execution_msg_id = report.instance_id
elif TARGET_OBJECT_TYPE == "document_definition":
    dashboard = Dashboard(connection=conn, id=TARGET_OBJECT_ID)
    execution_msg_id = dashboard.instance_id
else:
    raise ValueError(
        "TARGET_OBJECT_TYPE must be 'report_definition' or 'document_definition'."
    )

print(f"Execution message ID: {execution_msg_id}")

# Send one object to the History List
send_result = send_to_history_list(
    conn,
    object_id=TARGET_OBJECT_ID,
    object_type=TARGET_OBJECT_TYPE,
    project_id=PROJECT_ID,
    display_name="Test message",
    message_id=execution_msg_id,
)
# List all History List messages for all users as dictionaries of data
messages = list_history_list_messages(conn)
print(messages)

# List messages for a specific target object
object_messages = list_history_list_messages(
    conn,
    project_id=PROJECT_ID,
    target_info_object_id=TARGET_OBJECT_ID,
)
print(object_messages)

# List messages as HistoryList objects
message_objects = list_history_list_messages(conn, to_dictionary=False)
print(message_objects)

# Initialize a message and list its detailed properties
message = HistoryList(conn, id=execution_msg_id)
print(message.list_properties())

# Find messages by IDs
messages_by_ids = get_history_list_messages_by_ids(conn, [execution_msg_id])
print(messages_by_ids)

# Send multiple objects to the History List
bulk_send_result = bulk_send_to_history_list(
    conn,
    requests=[
        {
            "projectId": PROJECT_ID,
            "objects": [
                {
                    "id": TARGET_OBJECT_ID,
                    "type": TARGET_OBJECT_TYPE,
                    "displayName": "Bulk upload test",
                }
            ],
        }
    ],
)
print(bulk_send_result)

# Rename a selected History List message
message.alter(display_name="Test message - new name")

# Mark selected messages as read
status_result = update_history_list_messages_status(
    conn,
    message_statuses=[{"id": execution_msg_id, "status": "read_message"}],
    project_id=PROJECT_ID,
)
print(status_result)

# Delete a selected History List message
message.delete(force=True)

# Delete all History List messages for all users
delete_all_history_list_messages(conn)
# The functionality will confirm whether the process failed or partially failed
# by leaving a warning.
