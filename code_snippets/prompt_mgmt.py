"""This is the demo script to show how to manage prompts.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from pprint import pprint
from mstrio.connection import get_connection
from mstrio.modeling import Prompt, list_prompts, PromptRestrictions
from mstrio.project_objects import Report
from mstrio.types import ObjectSubTypes
from mstrio.modeling.schema.helpers import ObjectSubType


PROJECT_NAME = "MicroStrategy Tutorial"
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Try different filtering options in list_prompts function
all_prompts = list_prompts(conn)

name_filtered_prompts = list_prompts(conn, name='prompt')

prompts_dicts = list_prompts(conn, to_dictionary=True)

filtered_by_sub_type = list_prompts(conn, subtype=ObjectSubTypes.PROMPT_DOUBLE)

# Define values for new prompt
NEW_PROMPT_NAME = $new_prompt_name
NEW_PROMPT_DESTINATION_FOLDER = $new_prompt_destination_folder

# Create value prompt
simple_value_prompt = Prompt.create_value_prompt(
    conn,
    NEW_PROMPT_NAME,
    ObjectSubType.PROMPT_DOUBLE,
    destination_folder=NEW_PROMPT_DESTINATION_FOLDER,
    restrictions=PromptRestrictions(
        allow_personal_answers='single', required=True, min=1, max=100
    ),
)

# Init created prompt by name
existing_value_prompt = Prompt(conn, name=NEW_PROMPT_NAME)

# List properties
pprint(existing_value_prompt.list_properties())

# Alter existing prompt
existing_value_prompt.alter(name='Altered Prompt Name 3', default_answer={'value': 25})

# Add personal answer
existing_value_prompt.add_personal_answer(50, 'my_personal_answer')

# Delete existing prompt
existing_value_prompt.delete(force=True)

# Define values for new attribute elements prompt
NEW_ATTRIBUTE_ELEMENTS_PROMPT_NAME = $new_attribute_elements_prompt_name
SELECTED_ATTRIBUTE = $selected_attribute

# Create attribute elements prompt
attribute_elements_prompt = Prompt.create_attr_elements_prompt(
    conn,
    NEW_ATTRIBUTE_ELEMENTS_PROMPT_NAME,
    attribute=SELECTED_ATTRIBUTE,
    destination_folder=NEW_PROMPT_DESTINATION_FOLDER,
    restrictions=PromptRestrictions(allow_personal_answers='single', required=True),
    default_answer=[{'display': 'Electronics', 'elementId': 'h2'}],
)

attribute_elements_prompt.delete(force=True)
