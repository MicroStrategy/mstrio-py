"""This is the demo script to show how administrator can manage folders, objects
and their dependencies.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.object_management import (
    Folder,
    full_search,
    get_my_personal_objects_contents,
    get_predefined_folder_contents,
    get_search_results,
    get_search_suggestions,
    list_folders,
    list_objects,
    Object,
    PredefinedFolders,
    quick_search,
    quick_search_from_object,
    SearchObject,
    SearchPattern,
    SearchResultsFormat,
    start_full_search
)
from mstrio.project_objects import Dossier
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import Rights

from mstrio.connection import get_connection

# Define variables which can be later used in a script
PROJECT_NAME = $project_name
PROJECT_ID = $project_id

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# list folders from a particular project
list_folders(conn, project_id=PROJECT_ID)

# list configuration-level folders
list_folders(conn)

# get contents of My Personal Objects in a specific folder
get_my_personal_objects_contents(conn, project_id=PROJECT_ID)

# get contents of a pre-defined folder in a specific folder
get_predefined_folder_contents(
    conn, folder_type=PredefinedFolders.PUBLIC_REPORTS, project_id=PROJECT_ID
)

# Define variables which can be later used in a script
FOLDER_NAME = $folder_name
FOLDER_PARENT_ID = $folder_parent_id
FOLDER_DESCRIPTION = $folder_description

# create new folder in a particular folder
new_folder = Folder.create(
    conn, name=FOLDER_NAME, parent=FOLDER_PARENT_ID, description=FOLDER_DESCRIPTION
)

# Define variables which can be later used in a script
FOLDER_ID = $folder_id  # ID for Folder object lookup
TRUSTED_USER_ID = $trusted_user_id

# get folder with a given ID
folder = Folder(conn, id=FOLDER_ID)

# get contents of a folder (optionally as a dictionary)
contents_objs = folder.get_contents()
contents_dict = folder.get_contents(to_dictionary=True)

# alter name and description of a folder
folder.alter(name=FOLDER_NAME, description=FOLDER_DESCRIPTION)

# add ACL right to the folder for the user and propagate to children of folder
folder.acl_add(
    Rights.EXECUTE,
    trustees=TRUSTED_USER_ID,
    denied=False,
    inheritable=True,
    propagate_to_children=True
)  # see utils/acl.py for Rights values

# remove ACL from the folder for the user
folder.acl_remove(Rights.EXECUTE, trustees=TRUSTED_USER_ID, denied=False, inheritable=True)
# see utils/acl.py for Rights values

# Delete folder. When argument `force` is set to `False` (default value), then
# deletion must be approved.
folder.delete(force=True)

# list objects of a given type
reports = list_objects(conn, ObjectTypes.REPORT_DEFINITION)  # see types.py for ObjectTypes values
documents = list_objects(conn, ObjectTypes.DOCUMENT_DEFINITION)

# Define variables which can be later used in a script
OBJECT_ID = $object_id
OBJECT_NAME = $object_name
OBJECT_DESCRIPTION = $object_description

# initialize an object of a given type (in this case `FOLDER`) with a given id
object = Object(conn, ObjectTypes.FOLDER, OBJECT_ID)  # see types.py for ObjectTypes values

# alter name and description of an object
object.alter(name=OBJECT_NAME, description=OBJECT_DESCRIPTION)

# Define variables which can be later used in a script
REPORT_ID = $report_id
DOCUMENT_ID = $document_id
DOSSIER_ID = $dossier_id

# certify object
Object(conn, ObjectTypes.REPORT_DEFINITION, REPORT_ID).certify()

# decertify object
Object(conn, ObjectTypes.REPORT_DEFINITION, REPORT_ID).decertify()

# get object properties as a dictionary
object.to_dict()

# create copy of the object in the same folder with the default name
new_object = object.create_copy()

# create copy of the object in the same folder with provided name
new_object = object.create_copy(OBJECT_NAME)

# create copy of the object in another folder with provided name
new_object = object.create_copy(OBJECT_NAME, FOLDER_ID)

# move the object to another folder
object.move(FOLDER_ID)

# Delete objects of a given types (in this case `REPORT` and 'DOCUMENT)
# and given ids. When argument `force` is set to `False` (default value), then
# deletion must be approved.
Object(conn, ObjectTypes.REPORT_DEFINITION, REPORT_ID).delete()
Object(conn, ObjectTypes.DOCUMENT_DEFINITION, DOCUMENT_ID).delete(force=True)

# Define variables which can be later used in a script
SEARCH_OBJECT_ID = $search_object_id
SEARCH_PATTERN = $search_pattern  # string to get search suggestions for

# initialize SearchObject and synchronize with server
search_object = SearchObject(conn, id=SEARCH_OBJECT_ID)

# get search suggestions with the pattern set performed in all unique projects
# across the cluster (it takes effect only in I-Server with cluster nodes)
suggestions = get_search_suggestions(
    conn, project=PROJECT_ID, key=SEARCH_PATTERN, max_results=20, cross_cluster=True
)

# use the stored results of the Quick Search engine to return search results
# and display them as a list (in this particular case all reports which name
# begins with 'A')
objects = quick_search(
    conn,
    PROJECT_ID,
    name='A',
    pattern=SearchPattern.BEGIN_WITH,
    object_types=[ObjectTypes.REPORT_DEFINITION]
)

# perform quick search based on a predefined Search Object (include ancestors
# and acl of returned objects)
objects = quick_search_from_object(
    conn, PROJECT_ID, search_object, include_ancestors=True, include_acl=True
)

# search the metadata for objects in a specific project that match specific
# search criteria (e.g. super cubes which name ends with `cube`) and save the
# results in I-Server memory
start_dict = start_full_search(
    conn,
    PROJECT_ID,
    name='cube',
    pattern=SearchPattern.END_WITH,
    object_types=ObjectSubTypes.SUPER_CUBE
)

# Retrieve the results of a full metadata search in a tree format which were
# previously obtained by `start_full_search`
results = get_search_results(
    conn, search_id=start_dict['id'], results_format=SearchResultsFormat.TREE
)

# perform full search in one call (instead of the two steps presented above).
# Get all documents which name contains `document` and return in a list format.
# Perform search only in the root folder and its subfolders.
results = full_search(
    conn,
    PROJECT_ID,
    name='document',
    pattern=SearchPattern.CONTAINS,
    object_types=ObjectTypes.DOCUMENT_DEFINITION,
    root=FOLDER_ID
)

# return cubes that are used by the given dossier (it can be performed with the
# function `full_search` or method `get_connected_cubes` from `Document` class
# or method `get_dependencies` from `Entity` class)
cubes = Dossier(conn, id=DOSSIER_ID).get_connected_cubes()
cubes = Dossier(conn, id=DOSSIER_ID).list_dependencies(
    project=PROJECT_ID, object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE]
)
cubes = full_search(
    conn,
    project=PROJECT_ID,
    object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE],
    used_by_object_id=DOCUMENT_ID,
    used_by_object_type=ObjectTypes.DOCUMENT_DEFINITION
)

# we can also list cubes that use given dossier
cubes_using_dossier = Dossier(conn, id=DOSSIER_ID).list_dependents(
    project=PROJECT_ID, object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE]
)

# Define a variable which can be later used in a script
METRIC_ID = $metric_id

# get all objects that use (also recursive) metric with given id
objects = full_search(
    conn,
    project=PROJECT_ID,
    uses_object_id=METRIC_ID,
    uses_object_type=ObjectTypes.METRIC,
    uses_recursive=True
)
