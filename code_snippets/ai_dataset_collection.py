"""This is the demo script to show how to manage AI Dataset Collections.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.ai_dataset_collection import (
    AIDatasetCollection,
    list_ai_dataset_collections,
)


# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(connectionData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
AI_DATASET_COLLECTION_ID = $ai_dataset_collection_id
AI_DATASET_COLLECTION_NAME = $ai_dataset_collection_name
NEW_AI_DATASET_COLLECTION_NAME = $new_ai_dataset_collection_name
NEW_AI_DATASET_COLLECTION_DESCRIPTION = $new_ai_dataset_collection_description
NEW_AI_DATASET_COLLECTION_ABBREVIATION = $new_ai_dataset_collection_abbreviation
NEW_AI_DATASET_COLLECTION_OWNER = $new_ai_dataset_collection_owner
FOLDER_ID = $folder_id

# List AI Dataset Collections in the project
ai_dataset_collections = list_ai_dataset_collections(
    connection=conn,
    project=PROJECT_NAME,
)
ai_dataset_collections_as_dicts = list_ai_dataset_collections(
    connection=conn,
    project=PROJECT_NAME,
    to_dictionary=True,
)

# Initialize an AI Dataset Collection by id or name
ai_dataset_collection = AIDatasetCollection(
    connection=conn,
    id=AI_DATASET_COLLECTION_ID,
)
ai_dataset_collection_by_name = AIDatasetCollection(
    connection=conn,
    name=AI_DATASET_COLLECTION_NAME,
)

# Get AI Dataset Collection properties
properties = ai_dataset_collection.list_properties()
print(properties)

# Alter AI Dataset Collection properties
ai_dataset_collection.alter(
    name=NEW_AI_DATASET_COLLECTION_NAME,
    description=NEW_AI_DATASET_COLLECTION_DESCRIPTION,
    abbreviation=NEW_AI_DATASET_COLLECTION_ABBREVIATION,
    owner=NEW_AI_DATASET_COLLECTION_OWNER,
)

# Create a copy of the AI Dataset Collection in the same folder
copied_collection = ai_dataset_collection.create_copy(
    name=NEW_AI_DATASET_COLLECTION_NAME,
)

# Create a copy in a different folder, if needed
copied_collection_in_folder = ai_dataset_collection.create_copy(
    name=NEW_AI_DATASET_COLLECTION_NAME,
    folder_id=FOLDER_ID,
)

# Move and delete AI Dataset Collections
ai_dataset_collection.move(FOLDER_ID)
ai_dataset_collection.delete(force=True)
