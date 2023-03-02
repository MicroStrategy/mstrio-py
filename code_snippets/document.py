"""This is the demo script to show how to manage documents. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.document import (
    Document, list_documents, list_documents_across_projects
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define variables which can be later used in a script
PROJECT_ID = $project_id # Insert project ID here
DOCUMENT_NAME = $document_name # Insert name of document on which you want to perform actions

# Document management
# Listing documents with different conditions
list_of_all_documents = list_documents(connection=conn)
print(list_of_all_documents)
list_of_all_documents_as_dicts = list_documents(connection=conn, to_dictionary=True)
print(list_of_all_documents_as_dicts)
list_of_all_documents_as_dataframes = list_documents(connection=conn, to_dataframe=True)
print(list_of_all_documents_as_dataframes)
list_of_documents_on_project_by_id = list_documents(connection=conn, project_id=PROJECT_ID)
print(list_of_documents_on_project_by_id)
list_of_documents_on_project_by_name = list_documents(connection=conn, project_name=PROJECT_NAME)
print(list_of_documents_on_project_by_name)
list_of_documents_by_name = list_documents(connection=conn, name=DOCUMENT_NAME)
print(list_of_documents_by_name)

# List of documents across projects, with examples of different conditions
list_of_documents_across_projects = list_documents_across_projects(connection=conn)
print(list_of_documents_across_projects)
list_of_documents_as_dataframes = list_documents_across_projects(connection=conn, to_dataframe=True)
print(list_of_documents_as_dataframes)
list_of_documents_as_dicts = list_documents_across_projects(connection=conn, to_dictionary=True)
print(list_of_documents_as_dicts)

# Define a variable which can be later used in a script
DOCUMENT_ID = $document_id  # Insert ID of document on which you want to perform actions

# Get single document by id
document = Document(connection=conn, id=DOCUMENT_ID)

# Get single document by name
document = Document(connection=conn, id=DOCUMENT_NAME)

# Listing properties of document
properties = document.list_properties()
print(properties)

# Define variables which can be later used in a script
DOCUMENT_NEW_NAME = $document_new_name  # Insert new name of edited document here
DOCUMENT_NEW_DESCRIPTION = $document_new_description  # Insert new description of edited document
FOLDER_ID = $folder_id  # Insert folder ID here here

# Alter document
document.alter(name=DOCUMENT_NEW_NAME)
document.alter(description=DOCUMENT_NEW_DESCRIPTION)
document.alter(folder_id=FOLDER_ID)

# Define a variable which can be later used in a script
USER_ID = $user_id  # Insert user ID here

# Publish document
document.publish()
document.publish(recipients=USER_ID)

# Unpublish document
document.unpublish()

# Listing schedules of document
schedules = document.list_available_schedules()
print(schedules)
schedules_as_dicts = document.list_available_schedules(to_dictionary=True)
print(schedules_as_dicts)

# Share document with given user
document.share_to(users=USER_ID)

# Listing cubes used by this document
cubes = document.get_connected_cubes()
print(cubes)

# Get list of document cache, with examples of different conditions
list_of_all_document_cache = Document.list_caches(connection=conn)
print(list_of_all_document_cache)
list_of_limited_document_cache = Document.list_caches(connection=conn, limit=5)
print(list_of_limited_document_cache)

# Define a variable which can be later used in a script
CACHE_ID = $cache_id  # Insert ID of cache on which you want to perform actions

list_of_document_cache_by_id = Document.list_caches(connection=conn, id=CACHE_ID)
print(list_of_document_cache_by_id)
list_of_document_caches_as_dicts = Document.list_caches(connection=conn, to_dictionary=True)
print(list_of_document_caches_as_dicts)

# Helper function to list all cache status
def show_caches_status():
    caches = Document.list_caches(conn)
    for cache in caches:
        print(f'Cache ID: {cache.id}, {cache.status}')

# List cache properties
cache = Document.list_caches(connection=conn)[0]
properties = cache.list_properties()
print(properties)

# Define a variable which can be later used in a script
OTHER_CACHE_ID = $other_cache_id  # Insert ID of cache on which you want to perform actions

# Unload multiple document caches
Document.unload_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Define variables which can be later used in a script
USER_NAME = $user_name # Insert user name here
CACHE_STATUS = $cache_status # Insert cache status here

# Unload all document caches with filter examples
Document.unload_all_caches(connection=conn)
show_caches_status()
Document.unload_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Document.unload_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Load multiple document caches
Document.load_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Load all document caches with filter examples
Document.load_all_caches(connection=conn)
show_caches_status()
Document.load_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Document.load_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Delete multiple document caches
Document.delete_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID], force=True)

# Delete all document caches with filter examples
Document.delete_all_caches(connection=conn, force=True)
Document.delete_all_caches(connection=conn, owner=USER_NAME, force=True)
Document.delete_all_caches(connection=conn, status=CACHE_STATUS, force=True)
