from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(
    err_msg="Error getting smart attributes for attribute with ID: {attribute_id}"
)
def list_smart_attributes(
    connection: Connection,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Get a list of references to all smart attributes derived from
    the base attribute.

    Args:
        connection: Strategy One REST API connection object
        attribute_id: ID of the base attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/attributes/{attribute_id}/smartAttributes',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error updating smart attributes for attribute with ID: {attribute_id}"
)
def update_smart_attributes(
    connection: Connection,
    attribute_id: str,
    body: dict,
):
    """Reconcile the service-managed smart attributes for the attribute
    based on its key form.

    Note:
        This PUT is a reconcile/merge, not a wholesale replacement. If
        `smartAttributes` entries are provided in the body, applicable
        entries are merged into the service-managed set so fields such as
        `objectId`, `name` and `hidden` are respected. Omitted existing
        applicable entries are kept as-is; omitted missing applicable
        entries are auto-created, and existing non-applicable smart
        attributes may be removed. Passing an empty or omitted list lets
        the service regenerate the set.

    Args:
        connection: Strategy One REST API connection object
        attribute_id: ID of the base attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        body: Smart attributes reconciliation data in the form:
            `{'smartAttributes': [<ms-SmartAttribute>, ...]}`

    Return:
        HTTP response object. Expected status: 200
    """
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/attributes/{attribute_id}/smartAttributes',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting smart attribute templates for attribute "
    "with ID: {attribute_id}"
)
def list_smart_attribute_templates(
    connection: Connection,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Get a list of smart attribute templates that can be created
    for the base attribute.

    Args:
        connection: Strategy One REST API connection object
        attribute_id: ID of the base attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/attributes/{attribute_id}/smartAttributes/templates',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error getting smart attributes for attribute with ID: {attribute_id} "
    "in data model with ID: {data_model_id}"
)
def list_data_model_smart_attributes(
    connection: Connection,
    data_model_id: str,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Get the smart attributes associated with a specified attribute
    in the data model.

    Args:
        connection: Strategy One REST API connection object
        data_model_id: ID of the data model
        attribute_id: ID of the attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(
            f'/api/model/dataModels/{data_model_id}/attributes/{attribute_id}'
            '/smartAttributes'
        ),
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error updating smart attributes for attribute with ID: {attribute_id} "
    "in data model with ID: {data_model_id}"
)
def update_data_model_smart_attributes(
    connection: Connection,
    data_model_id: str,
    attribute_id: str,
    body: dict,
):
    """Reconcile the service-managed smart attributes for a specified
    data model attribute based on its key form.

    Note:
        This PUT is a reconcile/merge, not a wholesale replacement. If
        `smartAttributes` entries are provided in the body, applicable
        entries are merged into the service-managed set so fields such as
        `objectId`, `name` and `hidden` are respected. Omitted existing
        applicable entries are kept as-is; omitted missing applicable
        entries are auto-created, and existing non-applicable smart
        attributes may be removed. Passing an empty or omitted list lets
        the service regenerate the set.

    Args:
        connection: Strategy One REST API connection object
        data_model_id: ID of the data model
        attribute_id: ID of the attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        body: Smart attributes reconciliation data in the form:
            `{'smartAttributes': [<ms-SmartAttribute>, ...]}`

    Return:
        HTTP response object. Expected status: 200
    """
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{data_model_id}/attributes/{attribute_id}'
                '/smartAttributes'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting smart attribute templates for attribute "
    "with ID: {attribute_id} in data model with ID: {data_model_id}"
)
def list_data_model_smart_attribute_templates(
    connection: Connection,
    data_model_id: str,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Get the available smart attribute templates for a specified
    attribute in the data model.

    Args:
        connection: Strategy One REST API connection object
        data_model_id: ID of the data model
        attribute_id: ID of the attribute. The ID can be the object ID
            used in metadata or the object ID used in the changeset,
            but not yet committed to metadata.
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(
            f'/api/model/dataModels/{data_model_id}/attributes/{attribute_id}'
            '/smartAttributes/templates'
        ),
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )
