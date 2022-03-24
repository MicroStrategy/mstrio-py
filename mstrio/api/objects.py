from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession


@ErrorHandler(err_msg='Error getting information for the object with ID {id}')
def get_object_info(connection, id, object_type, project_id=None, error_msg=None,
                    whitelist=[('ERR001 ', 500)]):
    """Get information for a specific object in a specific project; if you do
    not specify a project ID, you get information for the object in all
    projects.

    You identify the object with the object ID and object type. You specify
    the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): One of EnumDSSXMLObjectTypes. Ex. 34 (User or
        UserGroup), 44 (Security Role), 32 (Project), 8 (Folder), 36 (type of
        I-Server configuration), 58 (Security Filter)
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    if object_type == 32:
        headers = {'X-MSTR-ProjectID': None}
    elif project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.get(
        url=f'{connection.base_url}/api/objects/{id}',
        headers=headers,
        params={'type': object_type}
    )


@ErrorHandler(err_msg='Error deleting object with ID {id}')
def delete_object(connection, id, object_type, project_id=None, error_msg=None):
    """Get information for a specific object in a specific project; if you do
    not specify a project ID, you get information for the object in all
    projects.

    You identify the object with the object ID and object type. You specify
    the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): One of EnumDSSXMLObjectTypes. Ex. 34 (User or
        UserGroup), 44 (Security Role), 32 (Project), 8 (Folder), 36 (type of
        I-Server configuration)
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    if object_type == 32:
        headers = {'X-MSTR-ProjectID': str(id)}
    elif project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.delete(
        url=f'{connection.base_url}/api/objects/{id}',
        headers=headers,
        params={'type': object_type}
    )


@ErrorHandler(err_msg='Error updating object with ID {id}')
def update_object(connection, id, body, object_type, project_id=None,
                  error_msg=None, verbose=True):
    """Get information for a specific object in a specific project; if you do
    not specify a project ID, you get information for the object in all
    projects.

    You identify the object with the object ID and object type. You specify
    the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        body: (object): body of the response
        object_type (int): One of EnumDSSXMLObjectTypes. Ex. 34 (User or
        UserGroup), 44 (Security Role), 32 (Project), 8 (Folder), 36 (type of
        I-Server configuration)
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    if object_type == 32:
        headers = {'X-MSTR-ProjectID': str(id)}
    elif project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.put(
        url=f'{connection.base_url}/api/objects/{id}',
        headers=headers,
        params={'type': object_type},
        json=body
    )


@ErrorHandler(err_msg='Error creating a copy of object with ID {id}')
def copy_object(connection, id, name, folder_id, object_type, project_id=None, error_msg=None):
    """Create a copy of a specific object.

    You identify the object with the object ID and object type. You obtain the
    authorization token needed to execute the request using POST /auth/login;
    you obtain the project ID using GET /projects. You pass the authorization
    token and the project ID in the request header. You specify the object ID in
    the path of the request and object type as a query parameter; possible
    values for object type are provided in EnumDSSXMLObjectTypes. You specify
    the name and location (folder ID) of the new object in the body of the
    request. If you do not specify a new name, a default name is generated, such
    as 'Old Name (1)'. If you do not specify a folder ID, the object is saved in
    the same folder as the source object.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): One of EnumDSSXMLObjectTypes. Ex. 34 (User or
        UserGroup), 44 (Security Role), 32 (Project), 8 (Folder), 36 (type of
        I-Server configuration)
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    if object_type == 32:
        headers = {'X-MSTR-ProjectID': str(id)}
    elif project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    elif connection.project_id:
        headers = {'X-MSTR-ProjectID': connection.project_id}
    else:
        raise ValueError("Project needs to be specified.")

    body = {"name": name, "folderId": folder_id}
    return connection.post(
        url=f'{connection.base_url}/api/objects/{id}/copy',
        headers=headers,
        params={'type': object_type},
        json=body
    )


@ErrorHandler(err_msg='Error getting VLDB settings for object with ID {id}')
def get_vldb_settings(connection, id, object_type, project_id=None, error_msg=None):
    """Get vldb settings for an object.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): DssXmlTypeReportDefinition(3) for Dataset and
            DssXmlTypeDocumentDefinition(55) for document/dossier
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    headers = {}
    if project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        connection._validate_project_selected()
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.get(
        url=f"{connection.base_url}/api/objects/{id}/vldb/propertySets",
        params={'type': object_type},
        headers=headers,
    )


@ErrorHandler(err_msg='Error resetting all custom vldb settings for object with ID {id}')
def delete_vldb_settings(connection, id, object_type, project_id=None, error_msg=None):
    """Delete all customized vldb settings in one object, this operation will
    reset all vldb settings to default.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): DssXmlTypeReportDefinition(3) for Dataset and
            DssXmlTypeDocumentDefinition(55) for document/dossier
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    headers = {}
    if project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        connection._validate_project_selected()
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.delete(
        url=f"{connection.base_url}/api/objects/{id}/vldb/propertySets",
        params={'type': object_type},
        headers=headers,
    )


@ErrorHandler(err_msg='Error resetting all custom vldb settings for object with ID {id}')
def set_vldb_settings(connection, id, object_type, name, body, project_id=None, error_msg=None):
    """Set vldb settings for one property set in one object.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): DssXmlTypeReportDefinition(3) for Dataset and
            DssXmlTypeDocumentDefinition(55) for document/dossier
        name: property set name
        body: [{"name": "string",
                "value": {}}]
        project_id(str): ID of a project in which the object is located.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    headers = {}
    if project_id:
        headers = {'X-MSTR-ProjectID': project_id}
    else:
        connection._validate_project_selected()
        headers = {'X-MSTR-ProjectID': connection.project_id}

    return connection.put(
        url=f"{connection.base_url}/api/objects/{id}/vldb/propertySets/{name}",
        params={'type': object_type},
        headers=headers,
        json=body,
    )


@ErrorHandler(err_msg='Error getting objects.')
def create_search_objects_instance(connection, name=None, pattern=4, domain=2, root=None,
                                   object_type=None, error_msg=None):
    """Create a search instance.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name: expression used with the pattern to do the search
        pattern: specifies the nature of the search. Possible values are defined
            in the EnumDSSXMLSearchTypes javadoc
        domain: search domain. specifies the domain/scope of the search.
            Possible values are defined in the EnumDSSXMLSearchDomain javadoc
        root: folder ID of the root in which the search is done
        object_type: specifies the type of objects to be searched. Possible
            values are defined in the EnumDSSObjectType javadoc
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response returned by the MicroStrategy REST server
    """
    connection._validate_project_selected()
    return connection.post(
        url=f"{connection.base_url}/api/objects",
        headers={'X-MSTR-ProjectID': connection.project_id},
        params={
            'name': name,
            'pattern': pattern,
            'domain': domain,
            'root': root,
            'type': object_type
        },
    )


@ErrorHandler(err_msg='Error getting objects using search with ID {search_id}')
def get_objects(connection, search_id, offset=0, limit=-1, get_tree=False, error_msg=None):
    """Get list of objects from metadata.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id: ID for the results of a previous search stored in I-Server
            memory
        offset: starting point within the collection of returned results. Used
            to control paging behavior.
        limit: maximum number of items returned for a single request. Used to
            control paging behavior
        get_tree: specifies that the search results should be displayed in
            a tree structure instead of a list. The ancestors of the searched
            objects are the nodes and the searched objects are the leaves of
            the tree.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response returned by the MicroStrategy REST server
    """
    connection._validate_project_selected
    return connection.get(
        url=f"{connection.base_url}/api/objects",
        headers={'X-MSTR-ProjectID': connection.project_id},
        params={
            'searchId': search_id,
            'offset': offset,
            'limit': limit,
            'getTree': get_tree
        },
    )


def get_objects_async(future_session: "FuturesSession", connection, search_id, offset=0, limit=-1,
                      get_tree=False, error_msg=None):
    """Get list of objects from metadata asynchronously.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_id: ID for the results of a previous search stored in I-Server
            memory
        offset: starting point within the collection of returned results. Used
            to control paging behavior.
        limit: maximum number of items returned for a single request. Used to
            control paging behavior.
        get_tree: specifies that the search results should be displayed in
            a tree structure instead of a list. The ancestors of the searched
            objects are the nodes and the searched objects are the leaves of
            the tree.

    Returns:
        HTTP response returned by the MicroStrategy REST server
    """
    connection._validate_project_selected()
    url = connection.base_url + '/api/objects'
    headers = {'X-MSTR-ProjectID': connection.project_id}
    params = {'searchId': search_id, 'offset': offset, 'limit': limit, 'getTree': get_tree}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


@ErrorHandler(err_msg='Error certifying object with ID {id}')
def toggle_certification(connection, id, object_type=3, certify=True):
    """Certify/Uncertify a multi-table dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Identifier of a pre-existing dataset. Used when
            certifying a pre-existing dataset.
        object_type (int, optional): Type of object to certify as integer;
            defaults to 3 (dataset)
        certify (bool, optional): boolean representing if the instruction is to
            certify (True) or decertify (False); defaults to True.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    url = f'{connection.base_url}/api/objects/{id}/certify/?type={str(object_type)}' \
          f'&certify={str(certify)}'
    return connection.put(
        url=url,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
    )
