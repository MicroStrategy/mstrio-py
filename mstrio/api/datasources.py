from typing import Optional

from mstrio.connection import Connection
from mstrio.server.application import Application
from mstrio.utils.datasources import (alter_conn_list_resp, alter_conn_resp,
                                      alter_instance_list_resp, alter_instance_resp,
                                      alter_patch_req_body)
from mstrio.utils.helper import exception_handler, response_handler


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


def get_available_db_drivers(connection, error_msg=None):
    """Get information for all available database drivers.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    url = f"{connection.base_url}/api/dbobjects/drivers"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting available database drivers"
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
    response = alter_instance_resp(response)
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
    for op_dict in body["operationList"]:
        op_dict = alter_patch_req_body(op_dict, "/datasourceConnection", "/databaseConnectionId")
        op_dict = alter_patch_req_body(op_dict, "/primaryDatasource",
                                       "/databasePrimaryDatasourceId")
        op_dict = alter_patch_req_body(op_dict, "/dataMartDatasource",
                                       "/databaseDataMartDatasourceId")
        alter_patch_req_body(op_dict, "/dbms", "/dbmsId")
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
    response = alter_instance_resp(response)
    return response


def get_datasource_instances(connection, ids=None, database_type=None, application=None,
                             error_msg=None):
    """Get information for all database sources.

    Args:
        connection: MicroStrategy REST API connection object
        ids: list of datasources ids
        database_type: list of types (names) of databases
        application: id (str) of a project or instance of an Application class
            to search for the datasource instances in. When provided, both
            `ids` and `database_types` are ignored. By default `None`.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 200/400
    """
    application = application.id if isinstance(application, Application) else application
    application_provided = application is not None

    if application_provided:
        url = f"{connection.base_url}/api/projects/{application}/datasources"
        response = connection.session.get(url=url)
    else:
        database_type = None if database_type is None else database_type.join(",")
        ids = None if ids is None else ids.join(",")
        url = f"{connection.base_url}/api/datasources"
        response = connection.session.get(url=url, params={
            'id': ids,
            'database.type': database_type
        })
    if not response.ok:
        res = response.json()
        if application_provided and res.get("message") == "HTTP 404 Not Found":
            # aka application based endpoint not supported
            # try without filtering
            warning_msg = ("get_datasource_instances() warning: filtering by Application "
                           "is not yet supported on this version of the I-Server. "
                           "Returning all values.")
            exception_handler(warning_msg, Warning, 0)
            return get_datasource_instances(connection=connection, ids=ids,
                                            database_type=database_type, error_msg=error_msg)
        if error_msg is None:
            if application_provided \
                    and res.get('code') == "ERR006" \
                    and "not a valid value for Project ID" in res.get('message'):
                error_msg = f"{application} is not a valid Application class instance or ID"
                raise ValueError(error_msg)
            error_msg = "Error getting Datasource Instances"
            if application_provided:
                error_msg += f" within `{application}` Application"
        response_handler(response, error_msg)
    response = alter_instance_list_resp(response)
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
    response = alter_conn_list_resp(response)
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
    response = alter_conn_resp(response)
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
    for op_dict in body["operationList"]:
        alter_patch_req_body(op_dict, "/datasourceLogin", "/databaseLoginId")
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
    response = alter_conn_resp(response)
    return response


def test_datasource_connection(connection, body, error_msg=None):
    """Test a datasource connection. Either provide a connection id, or the
    connection parameters within connection object.

    Args:
        connection: MicroStrategy REST API connection object.
        body: Datasource Connection info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. HTTP STATUS 204/400
    """
    url = f"{connection.base_url}/api/datasources/connections/test"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error testing Datasource connection"
        response_handler(response, error_msg)
    return response


def get_datasource_mappings(connection: Connection, default_connection_map: Optional[bool] = False,
                            application_id: Optional[str] = None, error_msg: Optional[str] = None):
    """Get information for all datasource connection mappings.

    Args:
        connection: MicroStrategy REST API connection object
        default_connection_map (bool, optional): If True will get the default
            connection map for an application. Requires `application_id`
            parameter. Default False.
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


def create_datasource_mapping(connection: Connection, body, error_msg: Optional[str] = None):
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


def delete_datasource_mapping(connection: Connection, id: str, error_msg: Optional[str] = None):
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


def get_datasource_logins(connection: Connection, error_msg: Optional[str] = None):
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


def create_datasource_login(connection: Connection, body, error_msg: Optional[str] = None):
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


def get_datasource_login(connection: Connection, id: str, error_msg: Optional[str] = None):
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


def delete_datasource_login(connection: Connection, id: str, error_msg: Optional[str] = None):
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


def update_datasource_login(connection: Connection, id: str, body,
                            error_msg: Optional[str] = None):
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
