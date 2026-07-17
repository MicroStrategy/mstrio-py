"""This is the demo script to show how to manage Mosaic models and use
Enable for AI operations. Its basic goal is to present what can be done with
this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.mosaic_model import MosaicModel, list_mosaic_models


# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(connectionData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
MOSAIC_MODEL_ID = $mosaic_model_id  # Insert Mosaic model ID here
MOSAIC_MODEL_NAME = $mosaic_model_name  # Insert Mosaic model name here
NEW_MOSAIC_MODEL_NAME = $new_mosaic_model_name
NEW_MOSAIC_MODEL_DESCRIPTION = $new_mosaic_model_description
NEW_MOSAIC_MODEL_ABBREVIATION = $new_mosaic_model_abbreviation
NEW_MOSAIC_MODEL_OWNER = $new_mosaic_model_owner
FOLDER_ID = $folder_id

# List Mosaic models in the project
mosaic_models = list_mosaic_models(connection=conn, project=PROJECT_NAME)
mosaic_models_as_dicts = list_mosaic_models(
    connection=conn,
    project=PROJECT_NAME,
    to_dictionary=True,
)

# Initialize a Mosaic model by id or name
mosaic_model = MosaicModel(connection=conn, id=MOSAIC_MODEL_ID)
mosaic_model_by_name = MosaicModel(connection=conn, name=MOSAIC_MODEL_NAME)

# Get Mosaic model properties
properties = mosaic_model.list_properties()
print(properties)

# Alter Mosaic model properties
mosaic_model.alter(
    name=NEW_MOSAIC_MODEL_NAME,
    description=NEW_MOSAIC_MODEL_DESCRIPTION,
    abbreviation=NEW_MOSAIC_MODEL_ABBREVIATION,
    owner=NEW_MOSAIC_MODEL_OWNER,
)

# Create a copy of the Mosaic model in the same folder or in a different folder
copied_model = mosaic_model.create_copy(name=NEW_MOSAIC_MODEL_NAME)
copied_model_in_folder = mosaic_model.create_copy(
    name=NEW_MOSAIC_MODEL_NAME,
    folder_id=FOLDER_ID,
)

# Certify, decertify, move and delete Mosaic models
mosaic_model.certify()
mosaic_model.decertify()
mosaic_model.move(FOLDER_ID)
mosaic_model.delete(force=True)

# Enable for AI workflow
enabled = mosaic_model.enable_for_ai()
if enabled:
    final_status = mosaic_model.wait_until_enabled_for_ai()

enable_status = mosaic_model.get_enable_for_ai_status()
enable_status_as_dict = mosaic_model.get_enable_for_ai_status(to_dictionary=True)
print(enable_status)

# Disable AI on the Mosaic model when needed
mosaic_model.disable_for_ai()
print(enabled)
