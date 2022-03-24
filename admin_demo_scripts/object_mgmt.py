from mstrio.connection import Connection
from mstrio.object_management import (
    Folder, full_search, get_search_results, list_folders, Object, quick_search,
    quick_search_from_object, SearchObject, SearchPattern, SearchResultsFormat, start_full_search
)
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import Rights


def object_management_workflow(conn: "Connection") -> None:
    # get folders list in particular folder
    print(list_folders(conn, project_id='project_id'))

    # get folder by id
    folder = Folder(conn, id='folder_id')
    print(folder)

    # get contents of a particular folder
    contents_objs = folder.get_contents()
    print(contents_objs)

    # add ACL right to the folder for the user and propagate
    # to children of folder
    folder.acl_add(Rights.EXECUTE, trustees="user_id", denied=False,
                   inheritable=True, propagate_to_children=True)

    # remove ACL from the folder for the user
    folder.acl_remove(Rights.EXECUTE, trustees="user_id", denied=False,
                      inheritable=True)

    # Delete folder.
    # When argument `force` is set to `False` (default value), then
    # deletion must be approved.
    folder.delete(force=True)

    # get object by id
    obj = Object(conn, id='report_id', type=ObjectTypes.REPORT_DEFINITION)
    print(obj)

    # modify an object
    obj.alter(abbreviation='report1')
    print(obj)

    # certify an object
    obj.certify()

    # create a copy of an object
    copied_obj = obj.create_copy(name='new_name')
    print(copied_obj)

    # delete an object
    obj.delete()

    # use the stored results of the Quick Search engine to return search results
    # and display them as a list (in this particular case all reports which name
    # begins with 'A')
    objects = quick_search(conn, "project_id", name='A',
                           pattern=SearchPattern.CONTAINS,
                           object_types=[ObjectTypes.REPORT_DEFINITION])
    print(objects)

    # initialize SearchObject
    search_object = SearchObject(conn, id="search_object_id")
    print(search_object)

    # perform quick search based on a predefined Search Object (include
    # ancestors and acl of returned objects)
    objects = quick_search_from_object(conn, "project_id", search_object,
                                       include_ancestors=True, include_acl=True)
    print(objects)

    # search the metadata for objects in a specific project that match specific
    # search criteria (e.g. super cubes which name ends with `cube`) and save
    # the results in I-Server memory
    start_search = start_full_search(conn, project="project_id", name="cube",
                                     pattern=SearchPattern.END_WITH,
                                     object_types=ObjectSubTypes.SUPER_CUBE)
    print(start_search)

    # Retrieve the results of a full metadata search in a tree format which were
    # previously obtained by `start_full_search`
    results = get_search_results(conn, search_id=start_search['id'],
                                 project='project_id',
                                 results_format=SearchResultsFormat.TREE)
    print(results)

    # perform full search in one call (instead of the two steps
    # presented above). Get all documents which name contains `document` and
    # return in a list format.
    # Perform search only in the root folder and its subfolders.
    results = full_search(conn, "project_id", name="document",
                          pattern=SearchPattern.CONTAINS,
                          object_types=ObjectTypes.DOCUMENT_DEFINITION,
                          root="root_folder_id")
    print(results)

    # return cubes that are used by the given dossier (it can be performed
    # with the function `full_search` or method `get_dependencies` from
    # `Entity` class)
    dossier = Object(conn, type=ObjectTypes.DOCUMENT_DEFINITION,
                     id="document_id")
    print(dossier)
    cubes = dossier.list_dependencies(
        project="project_id",
        object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE])
    print(cubes)
    cubes = full_search(conn, project="project_id",
                        object_types=[ObjectSubTypes.OLAP_CUBE,
                                      ObjectSubTypes.SUPER_CUBE],
                        used_by_object_id="document_id",
                        used_by_object_type=ObjectTypes.DOCUMENT_DEFINITION)

    print(cubes)
