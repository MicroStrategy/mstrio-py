from enum import IntEnum
from typing import Union, List, TYPE_CHECKING
from mstrio.utils.entity import ObjectTypes, ObjectSubTypes
from mstrio.utils import helper
from mstrio.api import browsing

if TYPE_CHECKING:
    from mstrio.connection import Connection


class SearchType(IntEnum):
    """Enumeration constants used to specify searchType used to control BI
    Search. More details can be found in EnumDSSXMLSearchTypes in a browser."""
    BEGIN_WITH = 1,
    BEGIN_WITH_PHRASE = 3,
    CONTAINS = 4,
    CONTAINS_ANY_WORD = 0,
    END_WITH = 5,
    EXACTLY = 2,


class SearchDomain(IntEnum):
    """Enumeration constants used to specify the search domains. More details
     can be found in EnumDSSXMLSearchDomain in a browser."""
    CONFIGURATION_AND_ALL_PROJECTS = 5,
    DOMAIN_CONFIGURATION = 4,
    DOMAIN_LOCAL = 1,
    DOMAIN_PROJECT = 2,
    DOMAIN_REPOSITORY = 3,


def list_objects(connection: "Connection", object_type: Union[ObjectTypes, ObjectSubTypes, int,
                                                              List[Union[ObjectTypes,
                                                                         ObjectSubTypes, int]]],
                 application_id: str = None, name: str = None,
                 pattern: Union[SearchType, int] = None, domain: Union[SearchDomain, int] = None,
                 root: str = None, uses_object: str = None, uses_recursive: bool = False,
                 used_by_object: str = None, used_by_recursive: bool = None, limit: int = None,
                 chunk_size: int = 1000, err_msg_instance: str = None, err_msg_results: str = None,
                 **filters) -> List[dict]:
    """List objects based on provided type. We need to use endpoint from
    Browsing API.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        object_type(enum class object or integer or list of enum class objects
            or integers, optional): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.utils.entity.ObjectTypes and
            mstrio.utils.entity.ObjectSubTypes.
        application_id(string, optional): Application (aka Project) ID in which
            search will be done.
        name(string, optional): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with (patter)
            B (name).
        pattern(integer or enum class object, optional): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchType. Default value is CONTAINS (4).
        domain(integer or enum class object, optional): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.browsing.SearchDomain. Default value is
            DOMAIN_PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        uses_object(string, optional): Constrain the search to only return
            objects which use the given object. The value should be 'objectId;
            object type', for example 'E02FE6DC430378A8BBD315AA791FC580;3'. It
            is not allowed to use both 'usesObject' and 'usedByObject' in one
            request.
        uses_recursive(boolean, optional): Control the Intelligence server to
            also find objects that use the given objects indirectly. Default
            value is false.
        used_by_object(string, optional): Constrain the search to only return
            objects which are used by the given object. The value should be
            'object Id; object type', for example:
            'E02FE6DC430378A8BBD315AA791FC580;3'. It is not allowed to use both
            'usesObject' and 'usedByObject' in one request.
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        limit(integer, optional): Cut-off value for the number of objects
            returned.
        chunk_size(integer, optional): Number of objects in each chunk. Default
            value is 1000.
        err_msg_instance(string, optional): Error message for request to create
            search instance.
        err_msg_results(string, optional): Error message for request to get
            results of searching.
        filters: optional keyword arguments to filter results

    Returns:
        list of dictionaries with basic information of objects returned from the
        metadata.
    """
    if not isinstance(object_type, list):
        object_type = [object_type]
    # convert enum values to integers
    object_type = [int(t) for t in object_type]
    if pattern is not None:
        pattern = int(pattern)
    if domain is not None:
        domain = int(domain)
    res_inst = browsing.store_search_instance(
        connection=connection, project_id=application_id, name=name, pattern=pattern,
        domain=domain, root=root, object_type=object_type, uses_object=uses_object,
        uses_recursive=uses_recursive, used_by_object=used_by_object,
        used_by_recursive=used_by_recursive, error_msg=err_msg_instance)
    search_id = res_inst.json()['id']
    res = helper.fetch_objects_async(connection=connection, api=browsing.get_search_results,
                                     async_api=browsing.get_search_results_async, limit=limit,
                                     chunk_size=chunk_size, error_msg=err_msg_results,
                                     search_id=search_id, project_id=application_id,
                                     dict_unpack_value=None, filters=filters)
    return res
