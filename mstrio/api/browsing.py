from mstrio.utils.helper import response_handler
from typing import List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.browsing import SearchType, SearchDomain
    from mstrio.utils.entity import ObjectTypes, ObjectSubTypes


def store_search_instance(connection: "Connection", project_id: Optional[str] = None,
                          name: Optional[str] = None, pattern: Optional[Union["SearchType",
                                                                              int]] = None,
                          domain: Optional[Union["SearchDomain",
                                                 int]] = None, root: Optional[str] = None,
                          object_type: Optional[Union["ObjectTypes", "ObjectSubTypes", int,
                                                      List[Union["ObjectTypes", "ObjectSubTypes",
                                                                 int]]]] = None,
                          uses_object: Optional[str] = None, uses_recursive: bool = False,
                          used_by_object: Optional[str] = None,
                          used_by_recursive: Optional[bool] = None,
                          error_msg: Optional[str] = None):
    """
    Search the metadata and store an instance of search results.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        project_id(string, optional): Project ID
        name(string, optional): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with
            (pattern) B (name).
        pattern(integer or enum class object, optional): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchType. Default value is CONTAINS (4).
        domain(integer or enum class object, optional): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.browsing.SearchDomain. Default value is
            DOMAIN_PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        object_type(enum class object or integer or list of enum class objects
            or integers, optional): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.utils.entity.ObjectTypes and
            mstrio.utils.entity.ObjectSubTypes.
        uses_object(string, optional): Constrain the search to only return
            objects which use the given object. The value should be 'objectId;
            object type', for example 'E02FE6DC430378A8BBD315AA791FC580;3'. It
            is not allowed to use both 'uses_object' and 'used_by_object' in one
            request.
        uses_recursive(boolean, optional): Control the Intelligence server to
            also find objects that use the given objects indirectly. Default
            value is false.
        used_by_object(string, optional): Constrain the search to only return
            objects which are used by the given object. The value should be
            'object Id; object type', for example:
            'E02FE6DC430378A8BBD315AA791FC580;3'. It is not allowed to use both
            'uses_object' and 'used_by_object' in one request.
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        error_msg(string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response returned by the MicroStrategy REST server.
    """
    if not isinstance(object_type, list):
        object_type = [object_type]
    # convert enum values to integers
    object_type = [int(t) for t in object_type]
    if pattern is not None:
        pattern = int(pattern)
    if domain is not None:
        domain = int(domain)

    response = connection.session.post(
        url=f"{connection.base_url}/api/metadataSearches/results",
        headers={'X-MSTR-ProjectID': project_id}, params={
            'name': name,
            'pattern': pattern,
            'domain': domain,
            'root': root,
            'type': object_type,
            'usesObject': uses_object,
            'usesRecursive': uses_recursive,
            'usedByObject': used_by_object,
            'usedByRecursive': used_by_recursive
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error searching metadata."
        response_handler(response, error_msg)
    return response


def get_search_results(connection: "Connection", search_id: str, project_id: Optional[str] = None,
                       offset: int = 0, limit: int = -1, error_msg: Optional[str] = None):
    """
    Get search results in a list format.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id(string): Search ID (identifies the results fo a previous
            search stored in I-Server memory)
        project_id(string, optional): Project ID
        offset(integer, optional): Starting point within the collection of
            returned results. Used to control paging behavior. Default value
            is 0.
        limit(integer, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default value is -1.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response returned by the MicroStrategy REST server.
    """
    response = connection.session.get(
        url=f"{connection.base_url}/api/metadataSearches/results",
        headers={'X-MSTR-ProjectID': project_id}, params={
            'searchId': search_id,
            'offset': offset,
            'limit': limit
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting search result."
        response_handler(response, error_msg)
    return response


def get_search_results_async(future_session, connection, search_id, project_id=None, offset=0,
                             limit=-1):
    """Get search results in a list format asynchronously.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id(string): Search ID (identifies the results fo a previous
            search stored in I-Server memory)
        project_id(string, optional): Project ID
        offset(integer, optional): Starting point within the collection of
            returned results. Used to control paging behavior. Default value
            is 0.
        limit(integer, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default value is -1.

    Returns:
        Future with HTTP response returned by the MicroStrategy REST server as
        a result.
    """
    url = connection.base_url + '/api/objects'
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'searchId': search_id, 'offset': offset, 'limit': limit}
    future = future_session.get(url=url, headers=headers, params=params)
    return future
