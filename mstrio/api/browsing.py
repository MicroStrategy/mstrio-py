import json
from typing import TYPE_CHECKING, Optional, Union

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.object_management import CertifiedStatus, SearchPattern
    from mstrio.types import ObjectSubTypes, TypeOrSubtype
    from mstrio.utils.sessions import FuturesSessionWithRenewal


@ErrorHandler(err_msg="Error searching metadata.")
def store_search_instance(
    connection: 'Connection',
    project_id: str | None = None,
    name: str | None = None,
    pattern: int | None = None,
    domain: int | None = None,
    root: str | None = None,
    object_types: list[int] | None = None,
    uses_object: str | None = None,
    uses_recursive: bool = False,
    uses_one_of: bool | None = None,
    used_by_object: str | None = None,
    used_by_recursive: bool | None = None,
    used_by_one_of: bool | None = None,
    error_msg: str | None = None,
):
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
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        domain(integer or enum class object, optional): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.object_management.SearchDomain.
            Default value is DOMAIN_PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        object_types(list of enum class objects or integers, optional):
            Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.types.ObjectTypes and
            mstrio.types.ObjectSubTypes.
        uses_object(string, optional): Constrain the search to only return
            objects which use the given object. The value should be 'objectId;
            object type', for example 'E02FE6DC430378A8BBD315AA791FC580;3'. It
            is not allowed to use both 'uses_object' and 'used_by_object' in one
            request.
        uses_recursive(boolean, optional): Control the Intelligence server to
            also find objects that use the given objects indirectly. Default
            value is false.
        uses_one_of(boolean): Control the Intelligence server to also find
            objects that use one of or all of given objects indirectly.
            Default value is false.
        used_by_object(string, optional): Constrain the search to only return
            objects which are used by the given object. The value should be
            'object Id; object type', for example:
            'E02FE6DC430378A8BBD315AA791FC580;3'. It is not allowed to use both
            'uses_object' and 'used_by_object' in one request.
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        used_by_one_of(boolean): Control the Intelligence server to also
            find objects that are used by one of or all of given objects
            indirectly. Default value is false.
        error_msg(string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response returned by the MicroStrategy REST server.
    """
    return connection.post(
        endpoint='/api/metadataSearches/results',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'name': name,
            'pattern': pattern,
            'domain': domain,
            'root': root,
            'type': object_types,
            'usesObject': uses_object,
            'usesRecursive': uses_recursive,
            'usedByObject': used_by_object,
            'usedByRecursive': used_by_recursive,
            'usesOneOf': uses_one_of,
            'usedByOneOf': used_by_one_of,
        },
    )


@ErrorHandler(err_msg="Error getting search result for search with ID {search_id}")
def get_search_results(
    connection: 'Connection',
    search_id: str,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = -1,
    error_msg: str | None = None,
):
    """
    Get search results in a list format.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id(string): Search ID (identifies the results for a previous
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
    return connection.get(
        endpoint='/api/metadataSearches/results',
        headers={'X-MSTR-ProjectID': project_id},
        params={'searchId': search_id, 'offset': offset, 'limit': limit},
    )


def get_search_results_async(
    future_session: 'FuturesSessionWithRenewal',
    search_id: str,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = -1,
):
    """Get search results in a list format asynchronously.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
        search_id(string): Search ID (identifies the results for a previous
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
    endpoint = '/api/objects'
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'searchId': search_id, 'offset': offset, 'limit': limit}
    future = future_session.get(endpoint=endpoint, headers=headers, params=params)
    return future


@ErrorHandler(
    err_msg="Error getting search result in atree format for search with ID {search_id}"
)
def get_search_results_tree_format(
    connection: 'Connection',
    search_id: str,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = -1,
    error_msg: str | None = None,
):
    """
    Get search results in a tree format.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id(string): Search ID (identifies the results for a previous
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
    return connection.get(
        endpoint='/api/metadataSearches/results/tree',
        headers={'X-MSTR-ProjectID': project_id},
        params={'searchId': search_id, 'offset': offset, 'limit': limit},
    )


@ErrorHandler(err_msg="Error getting quick search result.")
def get_quick_search_result(
    connection,
    project_id: str | None = None,
    name: str | None = None,
    root: str | None = None,
    object_types: Optional['TypeOrSubtype'] = None,
    pattern: Union['SearchPattern', int] | None = None,
    certified_status: Optional['CertifiedStatus'] = None,
    offset: int | None = None,
    limit: int | None = None,
    hidden: bool | None = None,
    get_ancestors: bool | None = None,
    cross_cluster: bool | None = None,
    error_msg: str | None = None,
):
    return connection.get(
        endpoint='/api/searches/results',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'name': name,
            'type': object_types,
            'pattern': pattern,
            'root': root,
            'offset': offset,
            'limit': limit,
            'getAncestors': get_ancestors,
            'certifiedStatus': certified_status,
            'result.hidden': hidden,
            'isCrossCluster': cross_cluster,
        },
    )


@ErrorHandler(
    err_msg="Error getting quick search result from search object with ID {"
    "search_object_id}"
)
def get_quick_search_result_from_object(
    connection: 'Connection',
    project_id: str,
    search_object_id: str,
    subtypes: None
    | Union['ObjectSubTypes', list['ObjectSubTypes'], int, list[int]] = None,
    include_ancestors: bool | None = None,
    include_acl: bool | None = None,
    limit: int | None = None,
    offset: int | None = None,
    error_msg: str | None = None,
):
    return connection.get(
        endpoint=f'/api/searchObjects/{search_object_id}/results',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'includeAncestors': include_ancestors,
            'includeAcl': include_acl,
            'result.subtypes': subtypes,
            'offset': offset,
            'limit': limit,
        },
    )


@ErrorHandler(err_msg="Error getting specified shortcuts.")
def get_shortcuts(
    connection: 'Connection',
    body: dict,
    shortcut_info_flag: int = 0,
    error_msg: str | None = None,
):
    """Retrieve information about specific published shortcuts
    in specific projects.

    Args:
        connection: MicroStrategy REST API connection object
        body: A dictionary specifying the projects and shortcuts in the form of
            {[
                {
                    'projectId': 'string',
                    'shortcutIds': [
                    'string'
                    ]
                }
            ]}.
        shortcut_info_flag: flag indicating what information about shortcut
                should be loaded
        error_msg: Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.post(
        endpoint=(
            f'/api/searches/library/shortcuts?shortcutInfoFlag={shortcut_info_flag}'
        ),
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )


@ErrorHandler(err_msg="Error getting shortcut with id {id}.")
def get_shortcut(
    connection: 'Connection',
    id: str,
    project_id: str,
    shortcut_info_flag: int = 2,
    error_msg: str | None = None,
):
    """Get information about specific published shortcut in specific project.

    Args:
        connection: MicroStrategy REST API connection object
        id: id of target shortcut
        project_id: id of project that the shortcut is in
        shortcut_info_flag: flag indicating what information about shortcut
                should be loaded
        error_msg: Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    response = connection.post(
        endpoint=(
            f'/api/searches/library/shortcuts?shortcutInfoFlag={shortcut_info_flag}'
        ),
        headers={'X-MSTR-ProjectID': None},
        json=[{'projectId': project_id, 'shortcutIds': [id]}],
    )

    if response.ok:
        response_json = response.json()
        if len(response_json) > 0:
            response_json = response_json[0]
        response.encoding, response._content = 'utf-8', json.dumps(
            response_json
        ).encode('utf-8')
    return response


@ErrorHandler(err_msg="Error getting search suggestions.")
def get_search_suggestions(
    connection: 'Connection',
    project_id: str | None = None,
    key: str | None = None,
    count: int = -1,
    is_cross_cluster: bool = None,
):
    """Store results of the Search engine to return search suggestions.

    Args:
        connection (object): MicroStrategy REST API connection object
        project_id (string, optional): project ID
        key (string, optional): value the search pattern is set to, which will
            be applied to the names of suggestions being searched
        count (int, optional): maximum number of items returned for a single
            request. Used to control paging behavior. Default value is `-1` for
            no limit.
        is_cross_cluster (bool, optional): perform search in all unique projects
            across the cluster, this parameter only takes effect for I-Server
            with cluster nodes. Default value is `None`
    """
    is_cross_cluster = str(is_cross_cluster).lower() if is_cross_cluster else None
    return connection.get(
        endpoint=(
            '/api/searches/suggestions'
            f'?key={key}?count={count}?isCrossCluster={is_cross_cluster}'
        ),
        headers={'X-MSTR-ProjectID': project_id},
    )
