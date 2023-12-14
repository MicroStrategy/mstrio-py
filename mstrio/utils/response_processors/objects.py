from mstrio.api import objects as objects_api
from mstrio.connection import Connection


def get_info(
    connection: Connection,
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
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        object_type (int): One of EnumDSSXMLObjectTypes.
        project_id (str): ID of a project in which the object is located.

    Returns:
        dict
    """
    obj_info = objects_api.get_object_info(
        connection, id, object_type, project_id
    ).json()
    obj_info['hidden'] = obj_info.get('hidden', False)

    return obj_info


def update(connection, id: str, body: dict, object_type: int, project_id: str = None):
    """Get information for a specific object in a specific project; if you do
    not specify a project ID, you get information for the object in all
    projects.

    You identify the object with the object ID and object type. You specify
    the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Object ID
        body: (dict): body of the response
        object_type (int): One of EnumDSSXMLObjectTypes
        project_id (str): ID of a project in which the object is located.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    body['ownerId'] = body.pop('owner') if body.get('owner') else None
    obj_info = objects_api.update_object(
        connection, id, body, object_type, project_id
    ).json()

    obj_info['hidden'] = obj_info.get('hidden', False)

    return obj_info


def update_translations(
    connection: Connection,
    target_id: str,
    project_id: str,
    body: dict,
    object_type: int,
):
    """Create a translation based on provided body.

    Args:
        connection(Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        target_id (str): ID of the Object the translation will be added for
        project_id (str): ID of the Project the Object is located in
        body (dict): json representation of the body for the request
        object_type (int): type of the Object the translation will be added for

    Returns:
        A dictionary representing list of translations for the Object.
    """
    return _prepare_rest_output_for_translations(
        objects_api.update_translations(
            connection=connection,
            project_id=project_id,
            id=target_id,
            object_type=object_type,
            body=body,
            fields=None,
        )
        .json()
        .get('localesAndTranslations')
    )


def get_translations(
    connection: Connection,
    project_id: str,
    target_id: str,
    object_type: int,
):
    """List translations of the Object.

    Args:
        connection(Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        target_id (str): ID of the Object the translation will be listed for
        project_id (str): ID of the Project the Object is located in
        object_type (int): type of the Object the translation will be listed for

    Returns:
        A dictionary representing list of translations for the Object.
    """
    return _prepare_rest_output_for_translations(
        objects_api.get_translations(
            connection=connection,
            project_id=project_id,
            id=target_id,
            object_type=object_type,
            fields=None,
        )
        .json()
        .get('localesAndTranslations')
    )


def _prepare_rest_output_for_translations(rest_output):
    raw_list = []

    for target in rest_output:
        translations_list = []
        for translation in rest_output.get(target).get('translationValues'):
            translations_list.append(
                {
                    'value': rest_output.get(target)
                    .get('translationValues')
                    .get(translation)
                    .get('translation'),
                    'language_lcid': translation,
                }
            )
        raw_list.append(
            {
                'translation_target_id': target,
                'translation_target_name': rest_output.get(target).get(
                    'translationTargetName'
                ),
                'translation_values': translations_list,
            }
        )

    return raw_list
