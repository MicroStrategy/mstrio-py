from mstrio.utils.helper import response_handler


def dataset_definition(connection, dataset_id, fields=None, whitelist=[]):
    """Get the definition of a dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        fields(list, optional): Specifies object types to be returned. Possible
            values include tables, columns, attributes, and metrics. If no value
            is set, attributes and metrics are returned.
        whitelist(list): list of errors for which we skip printing error
            messages

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    connection._validate_project_selected()
    response = connection.session.get(url=connection.base_url + '/api/datasets/' + dataset_id,
                                      params={'fields': fields})
    if not response.ok:
        msg = "Error loading dataset '{}'. Check dataset ID.".format(
            dataset_id)
        response_handler(response, msg, whitelist=whitelist)
    return response


def create_dataset(connection, body):
    """Create a single-table dataset from external data uploaded to the
    MicroStrategy Intelligence Server.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        body (str): JSON-formatted definition of the dataset. Generated by
            `utils.formjson()`.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.post(url=connection.base_url + '/api/datasets',
                                       json=body)

    if not response.ok:
        response_handler(response, "Error creating new dataset model.")
    return response


def update_dataset(connection, dataset_id, table_name, update_policy, body, table_id=None):
    """Update a single-table dataset with external data uploaded to the
    MicroStrategy Intelligence Server.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        table_id (str): Identifier of the table to update within the
            MicroStrategy dataset.
        update_policy (str):  Update operation type: 'Add' (inserts new, unique
            rows), 'Update' (updates data in existing rows and columns),
            'Upsert' (updates existing data and inserts new rows), 'Replace'
            (similar to truncate, replaces the existing data with new data).
        body (str): JSON-formatted definition of the dataset. Generated by
            `utils.formjson()`.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.patch(url=connection.base_url + '/api/datasets/' + dataset_id + '/tables/'
                                        + table_name,
                                        headers={'updatePolicy': update_policy},
                                        json=body)
    if not response.ok:
        response_handler(response, "Error updating dataset.")
    return response


def delete_dataset(connection, dataset_id):
    """Delete a dataset previously created using the REST API.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.delete(url=connection.base_url + '/api/objects/' + dataset_id + '?type=3')

    if not response.ok:
        response_handler(response, msg="Error deleting dataset with ID: '{}'".format(dataset_id))
    return response


def create_multitable_dataset(connection, body):
    """Create the definition of a multi-table dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        body (dict): JSON-formatted payload containing the body of the request.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.post(url=connection.base_url + '/api/datasets/models',
                                       json=body)

    if not response.ok:
        response_handler(response, "Error creating new dataset model.")
    return response


def upload_session(connection, dataset_id, body):
    """Create a multi-table dataset upload session.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        body (dict): JSON-formatted payload containing the body of the request.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.post(url=connection.base_url + '/api/datasets/' + dataset_id + '/uploadSessions',
                                       json=body)
    if not response.ok:
        response_handler(response, "Error creating new data upload session.")
    return response


def upload(connection, dataset_id, session_id, body):
    """Upload data to a multi-table dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        session_id (str): Identifer of the server session used for collecting
            uploaded data.
        body (dict): JSON-formatted payload containing the body of the request.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.put(url=connection.base_url + '/api/datasets/' + dataset_id + '/uploadSessions/' +
                                      session_id,
                                      json=body)
    if not response.ok:
        response_handler(response, "Error uploading data.", throw_error=False)
    return response


def publish(connection, dataset_id, session_id):
    """Publish a multi-table dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        session_id (str): Identifer for the server session used for collecting
            uploaded data.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.post(url=connection.base_url + '/api/datasets/' + dataset_id + '/uploadSessions/' +
                                       session_id + '/publish')
    if not response.ok:
        response_handler(response, "Error publishing uploaded data. Cancelling publication.", throw_error=False)
    return response


def toggle_certification(connection, dataset_id, dataset_type=3, certify=True):
    """Certify/Uncertify a multi-table dataset.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            certifying a pre-existing dataset.
        dataset_type (int, optional): Type of dataset to certify as integer;
            defaults to 3.
        certify (bool, optional): boolean representing if the instruction is to
            certify (True) or decertify (False); defaults to True.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.put(url=connection.base_url + '/api/objects/' + dataset_id + '/certify/?type=' +
                                      str(dataset_type) + '&certify=' + str(certify),
                                      headers={'Content-Type': 'application/json',
                                               'Accept': 'application/json'})
    if not response.ok:
        error_msg = "Error certifying dataset with ID: '{}'".format(dataset_id)
        response_handler(response, error_msg)
    return response


def publish_status(connection, dataset_id, session_id):
    """Get multi-table dataset publication status.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        session_id (str): Identifer for the server session used for collecting
            uploaded data.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    response = connection.session.get(url=connection.base_url + '/api/datasets/' + dataset_id + '/uploadSessions/' +
                                      session_id + '/publishStatus')
    if not response.ok:
        response_handler(response, "Failed to check the publish status.")
    return response


def publish_cancel(connection, dataset_id, session_id):
    """Delete a multi-table dataset upload session and cancel publication.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        dataset_id (str): Identifier of a pre-existing dataset. Used when
            updating a pre-existing dataset.
        session_id (str): Identifer for the server session used for collecting
            uploaded data.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    response = connection.session.delete(
        url=connection.base_url + '/api/datasets/' + dataset_id + '/uploadSessions/' + session_id)
    if not response.ok:
        response_handler(response, "Failed to cancel the publication.")
    return response
