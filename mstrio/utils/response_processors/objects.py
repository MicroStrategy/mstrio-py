from mstrio.api import objects as objects_api


def get_info(
    connection,
    id: str,
    object_type: int,
    project_id: str = None,
) -> dict:
    """Get information for a specific object in a specific project; if you do
    not specify a project ID, you get information for the object just in the
    non-project area.

    You identify the object with the object ID and object type. You specify
    the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): One of EnumDSSXMLObjectTypes.
        project_id (str): ID of a project in which the object is located.

    Returns:
        dict
    """
    return objects_api.get_object_info(connection, id, object_type, project_id).json()
