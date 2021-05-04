from mstrio.utils.helper import response_handler


def create_folder(connection, name, parent_id, description, error_msg=None):
    """Create a folder.

    Args:
        connection: MicroStrategy REST API connection object
        name (string): name of folder to create
        parent_id (string): id of folder in which new folder will be created
        description (string, optional): description of folder to create
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    body = {
        "name": name,
        "description": description,
        "parent": parent_id,
    }
    response = connection.session.post(url=connection.base_url + '/api/folders',
                                       headers={'X-MSTR-ProjectID': connection.project_id},
                                       json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error while creating the folder"
        response_handler(response, error_msg)
    return response
