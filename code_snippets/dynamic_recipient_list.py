"""This is the demo script to show how to manage dynamic recipient lists. 
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.distribution_services.subscription import DynamicRecipientList, list_dynamic_recipient_lists

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define variables which can be later used in a script
# DRL stands for Dynamic Recipient List
DRL_NAME = $drl_name
SOURCE_REPORT_ID = $source_report_id
ATTRIBUTE_ID = $attribute_id
ATTRIBUTE_FORM_ID = $attribute_form_id
DESCRIPTION = $description
EXAMPLE_MAPPING_FIELD = DynamicRecipientList.MappingField(
    attribute_id=ATTRIBUTE_ID, 
    attribute_form_id=ATTRIBUTE_FORM_ID)

# Create a DRL
drl3 = DynamicRecipientList.create(connection=conn, name = DRL_NAME, description=DESCRIPTION,
    source_report_id=SOURCE_REPORT_ID,
    physical_address=EXAMPLE_MAPPING_FIELD, 
    linked_user=EXAMPLE_MAPPING_FIELD, 
    device=EXAMPLE_MAPPING_FIELD)

# List dynamic recipient lists with different conditions
list_of_all_drl = list_dynamic_recipient_lists(connection=conn)
print(list_of_all_drl)
list_of_all_drl_as_dicts = list_dynamic_recipient_lists(connection=conn, to_dictionary=True)
print(list_of_all_drl_as_dicts)
list_of_all_drl_by_name = list_dynamic_recipient_lists(connection=conn, name=DRL_NAME)
print(list_of_all_drl_by_name)

# Define variables which can be later used in a script
DRL_ID = $drl_id # ID of the DRL we want to perform actions on

# Get a DRL by it's id or name
drl = DynamicRecipientList(connection=conn, id=DRL_ID)
drl2 = DynamicRecipientList(connection=conn, name=DRL_NAME)

# List properties of a DRL
print(drl.list_properties())

# Alter a DRL
drl2.alter(name = DRL_NAME, description=DESCRIPTION,
    source_report_id=SOURCE_REPORT_ID,
    physical_address=EXAMPLE_MAPPING_FIELD,
    linked_user=EXAMPLE_MAPPING_FIELD, 
    device=EXAMPLE_MAPPING_FIELD)

# Delete a DRL without prompt
drl.delete(force=True)
