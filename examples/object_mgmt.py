"""This is the demo script to show how administrator can manage folders, objects
and their dependencies.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.object_management import (Folder, list_folders, get_predefined_folder_contents,
                                      get_my_personal_objects_contents, PredefinedFolders, Object,
                                      list_objects, SearchObject, get_search_suggestions,
                                      quick_search, quick_search_from_object, full_search,
                                      start_full_search, get_search_results, SearchPattern,
                                      SearchResultsFormat)
from mstrio.project_objects.dossier import Dossier
from mstrio.utils.entity import Rights
from mstrio.types import ObjectSubTypes, ObjectTypes

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# list folders from a particular project
list_folders(conn, project_id="project_id")

# list configuration-level folders
list_folders(conn)

# get contents of My Personal Objects in a specific folder
get_my_personal_objects_contents(conn, project_id="project_id")

# get contents of a pre-defined folder in a specific folder
get_predefined_folder_contents(conn, folder_type=PredefinedFolders.PUBLIC_REPORTS,
                               project_id="project_id")

# create new folder in a particular folder
new_folder = Folder.create(conn, name="New Folder", parent="parent_folder_id",
                           description="Description of New Folder")

# get folder with a given id
folder = Folder(conn, id="folder_id")

# get contents of a folder (optionally as a dictionary)
contents_objs = folder.get_contents()
contents_dict = folder.get_contents(to_dictionary=True)

# alter name and description of a folder
folder.alter(name="New name of folder", description="Folder with a new name")

# add ACL right to the folder for the user and propagate to children of folder
folder.acl_add(Rights.EXECUTE, trustees="user_id", denied=False, inheritable=True,
               propagate_to_children=True)

# remove ACL from the folder for the user
folder.acl_remove(Rights.EXECUTE, trustees="user_id", denied=False, inheritable=True)

# Delete folder. When argument `force` is set to `False` (default value), then
# deletion must be approved.
folder.delete(force=True)

# list objects of a given type
reports = list_objects(conn, ObjectTypes.REPORT_DEFINITION)
documents = list_objects(conn, ObjectTypes.DOCUMENT_DEFINITION)

# initialize an object of a given type (in this case `FOLDER`) with a given id
object = Object(conn, ObjectTypes.FOLDER, "object_id")

# alter name and description of an object
object.alter(name="New name", description="New description")

# certify object
Object(conn, ObjectTypes.REPORT_DEFINITION, "object_id").certify()

# decerttify object
Object(conn, ObjectTypes.REPORT_DEFINITION, "object_id").decertify()

# get object properties as a dictionary
object.to_dict()

# Delete objects of a given types (in this case `REPORT` and 'DOCUMENT)
# and given ids. When argument `force` is set to `False` (default value), then
# deletion must be approved.
Object(conn, ObjectTypes.REPORT_DEFINITION, "report id").delete()
Object(conn, ObjectTypes.DOCUMENT_DEFINITION, "document id").delete(force=True)

# initialize SearchObject and synchronize with server
search_object = SearchObject(conn, id="search_object_id")

# get search suggestions with the pattern set performed in all unique projects
# accross the cluster (ti takes effect only in I-Server with cluster nodes)
suggestions = get_search_suggestions(conn, project="project_id", key="search pattern",
                                     max_results=20, cross_cluster=True)

# use the stored results of the Quick Search engine to return search results
# and display them as a list (in this particular case all reports which name
# begins with 'A')
objects = quick_search(conn, "project_id", name='A', pattern=SearchPattern.BEGIN_WITH,
                       object_types=[ObjectTypes.REPORT_DEFINITION])

# perform quick search based on a predefined Search Object (include ancestors
# and acl of returned objects)
objects = quick_search_from_object(conn, "project_id", search_object, include_ancestors=True,
                                   include_acl=True)

# search the metadata for objects in a specific project that match specific
# search criteria (e.g. super cubes which name ends with `cube`) and save the
# results in I-Server memory
start_dict = start_full_search(conn, "project_id", name="cube", pattern=SearchPattern.END_WITH,
                               object_types=ObjectSubTypes.SUPER_CUBE)

# Retrieve the results of a full metadata search in a tree format which were
# previously obtained by `start_full_search`
results = get_search_results(conn, search_id=start_dict['id'],
                             results_format=SearchResultsFormat.TREE)

# perform full search in one call (instead of the two steps presented above).
# Get all documents which name contains `document` and return in a list format.
# Perform search only in the root folder and its subfolders.
results = full_search(conn, "project_id", name="document", pattern=SearchPattern.CONTAINS,
                      object_types=ObjectTypes.DOCUMENT_DEFINITION, root="folder_id")

# return cubes that are used by the given dossier (it can be performed with the
# function `full_search` or method `get_connected_cubes` from `Document` class
# or method `get_dependencies` from `Entity` class)
сubes = Dossier(conn, id="dossier_id").get_connected_cubes()
cubes = Dossier(conn, id="dossier_id").list_dependencies(
    project="project_id", object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE])
cubes = full_search(conn, project="project_id",
                    object_types=[ObjectSubTypes.OLAP_CUBE,
                                  ObjectSubTypes.SUPER_CUBE], used_by_object_id="dossier_id",
                    used_by_object_type=ObjectTypes.DOCUMENT_DEFINITION)

# we can also list cubes which uses given dossier
cubes_using_dossier = Dossier(conn, id="dossier_id").list_dependents(
    project="project_id", object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE])

# get all objects which uses (also recursive) metric with given id
objects = full_search(conn, project="project_id", uses_object_id="metric_id",
                      uses_object_type=ObjectTypes.METRIC, uses_recursive=True)
