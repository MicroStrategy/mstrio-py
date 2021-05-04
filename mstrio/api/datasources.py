from typing import Optional
from mstrio.utils.helper import response_handler
from mstrio.connection import Connection


def get_available_dbms(connection, error_msg=None):
    """Get information for all available database management systems (DBMSs).

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/dbobjects/dbmss"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting available DBMSs"
        response_handler(response, error_msg)
    return response


def get_datasource_instance(connection, id, error_msg=None):
    """Get information for a specific database source.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources/{id}"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error getting Datasource Instance with ID: {id}"
        response_handler(response, error_msg)
    return response


def delete_datasource_instance(connection, id, error_msg=None):
    """Delete a specific database source based on id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 204/400
    """
    url = f"{connection.base_url}/api/datasources/{id}"
    response = connection.session.delete(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error deleting Datasource Instance with ID: {id}"
        response_handler(response, error_msg)
    return response


def update_datasource_instance(connection, id, body, error_msg=None):
    """Update a specific database source based on id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        body: update operation info
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources/{id}"
    response = connection.session.patch(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error updating Datasource Instance with ID: {id}"
        response_handler(response, error_msg)
    return response


def create_datasource_instance(connection, body, error_msg=None):
    """Create a specific database source.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        body: Datasource info
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 201/400
    """
    url = f"{connection.base_url}/api/datasources"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            name = body.get("name", "NA")
            error_msg = f"Error creating Datasource Instance: {name}"
        response_handler(response, error_msg)
    return response


def get_datasource_instances(connection, ids=None, database_type=None, error_msg=None):
    """Get information for all database sources.

    Args:
        connection: MicroStrategy REST API connection object
        id: Comma-separated string of datasources id
        database_type: list of types (names) of databases
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources"
    database_type = database_type if database_type is None else database_type.join(",")
    ids = ids if ids is None else ids.join(",")

    response = connection.session.get(url=url, params={'id': ids, 'database.type': database_type})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting Datasource Instances"
        response_handler(response, error_msg)
    return response


def get_datasource_connections(connection, error_msg=None):
    """Get information for all datasource connections.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources/connections"

    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting Datasource Connections"
        response_handler(response, error_msg)
    return response


def get_datasource_connection(connection, id, error_msg=None):
    """Get a datasource connection for given id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources/connections/{id}"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error getting Datasource Connection with ID: {id}"
        response_handler(response, error_msg)
    return response


def update_datasource_connection(connection, id, body, error_msg=None):
    """Update a datasource connection based on id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        body: update operation info
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/datasources/connections/{id}"
    response = connection.session.patch(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error updating Datasource Connection with ID: {id}"
        response_handler(response, error_msg)
    return response


def delete_datasource_connection(connection, id, error_msg=None):
    """Delete a datasource connection based on id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 204/400
    """
    url = f"{connection.base_url}/api/datasources/connections/{id}"
    response = connection.session.delete(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error deleting Datasource Connection with ID: {id}"
        response_handler(response, error_msg)
    return response


def create_datasource_connection(connection, body, error_msg=None):
    """Create a specific database connection.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID
        body: Datasource Connection info
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 201/400
    """
    url = f"{connection.base_url}/api/datasources/connections"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            name = body.get("name", "NA")
            error_msg = f"Error creating Datasource connection: {name}"
        response_handler(response, error_msg)
    return response


def get_datasource_mappings(connection: Connection, default_connection_map: Optional[bool] = None,
                            application_id: Optional[str] = None, error_msg: Optional[str] = None):
    """Get information for all datasource connection mappings.

    Args:
        connection: MicroStrategy REST API connection object
        default_connection_map (bool): If True will get the default connection
            map for an application. Requires application_id parameter.
        application_id: The application_id, required only for default connection
            map.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/datasources/mappings"
    response = connection.session.get(
        url=url, params={
            "defaultConnectionMap": default_connection_map,
            "projectId": application_id
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error fetching Datasource mappings"
        response_handler(response, error_msg)
    return response


def create_datasource_mapping(connection: Connection, body, error_msg: str = None):
    """Create a new datasource mapping.

    Args:
        connection: MicroStrategy REST API connection object
        body: Datasource Connection Map creation info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    url = f"{connection.base_url}/api/datasources/mappings"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating Datasource mapping"
        response_handler(response, error_msg)
    return response


def delete_datasource_mapping(connection: Connection, id: str, error_msg: str = None):
    """Delete a datasource mapping based on id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of the mapping meant to be deleted.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    url = f"{connection.base_url}/api/datasources/mappings/{id}"
    response = connection.session.delete(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error deleting Datasource mapping"
        response_handler(response, error_msg)
    return response


def get_datasource_logins(connection: Connection, error_msg: str = None):
    """Get information for all datasource logins.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/datasources/logins"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting Datasource logins"
        response_handler(response, error_msg)
    return response


def create_datasource_login(connection: Connection, body, error_msg: str = None):
    """Create a new datasource login.

    Args:
        connection: MicroStrategy REST API connection object
        body: Datasource login creation info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    url = f"{connection.base_url}/api/datasources/logins"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating Datasource login"
        response_handler(response, error_msg)
    return response


def get_datasource_login(connection: Connection, id: str, error_msg: str = None):
    """Get datasource login for a specific id.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the login
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/datasources/logins/{id}"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error getting Datasource login with ID {id}"
        response_handler(response, error_msg)
    return response


def delete_datasource_login(connection: Connection, id: str, error_msg: str = None):
    """Delete a datasource login.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the login
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    url = f"{connection.base_url}/api/datasources/logins/{id}"
    response = connection.session.delete(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error deleting Datasource login with ID {id}"
        response_handler(response, error_msg)
    return response


def update_datasource_login(connection: Connection, id: str, body, error_msg: str = None):
    """Update a datasource login.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the login
        body: Datasource Connection Map creation info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/datasources/logins/{id}"
    response = connection.session.patch(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating Datasource login"
        response_handler(response, error_msg)
    return response
