"""REST API wrappers for Mosaic data models.

Note on path asymmetry: data model endpoints live under two different
path families. Modeling (definition) endpoints are scoped under
'/api/model/dataModels/...' and are changeset-based, while runtime
endpoints (instances, publish, publish status, attribute elements,
security filter members) are scoped under '/api/dataModels/...' and
never use changesets. A 404 on one path shape usually means the other
shape was intended. Object ACLs and translations are the exception:
they exist only under '/api/model/...'.

Note on identity tokens: some production tenant families additionally
expect an 'X-MSTR-IdentityToken' header on Mosaic modeling writes. The
OpenAPI contract does not require it and `Connection` does not send it.
If writes fail with authorization errors on such tenants,
`connection.get_identity_token()` exists as an escape hatch; it is not
sent by default.
"""

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.helper import response_handler

# --------------------------------------------------------------------------
# Runtime block ('/api/dataModels/...', no changesets)
# --------------------------------------------------------------------------


@ErrorHandler(err_msg="Error creating an instance of data model with ID: {id}")
def create_data_model_instance(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    show_invalid_cache_table_ids: bool = False,
):
    """Create a runtime instance of a data model.

    The response has no body (204). The ID of the new instance is
    returned ONLY in the 'X-MSTR-DataModelInstanceId' response header —
    never call `.json()` on the response.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        project_id: ID of a project; if omitted, the project selected
            on the connection is used
        show_invalid_cache_table_ids: Specifies whether to return IDs of
            tables with invalid caches

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint=f'/api/dataModels/{id}/instances',
        headers={'X-MSTR-ProjectID': project_id},
        params={'showInvalidCacheTableIds': show_invalid_cache_table_ids},
    )


@ErrorHandler(err_msg="Error deleting an instance of data model with ID: {id}")
def delete_data_model_instance(
    connection: Connection,
    id: str,
    instance_id: str,
    project_id: str | None = None,
):
    """Delete a runtime instance of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        instance_id: ID of a data model instance
        project_id: ID of a project; if omitted, the project selected
            on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.delete(
        endpoint=f'/api/dataModels/{id}/instances/{instance_id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(
    err_msg="Error getting elements of attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def get_data_model_attribute_elements(
    connection: Connection,
    id: str,
    attribute_id: str,
    project_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    search_pattern: str | None = None,
    element_id_format: str | None = None,
    fields: str | None = None,
):
    """Get elements of an attribute of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        project_id: ID of a project; if omitted, the project selected
            on the connection is used
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        search_pattern: Text that the returned elements must contain
        element_id_format: Format of the element IDs in the response.
            Available value: 'TERSE_LONG'
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=f'/api/dataModels/{id}/attributes/{attribute_id}/elements',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'offset': offset,
            'limit': limit,
            'searchPattern': search_pattern,
            'elementIdFormat': element_id_format,
            'fields': fields,
        },
    )


@ErrorHandler(
    err_msg="Error listing active security filters of data model with ID: {id}"
)
def list_active_security_filters(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
):
    """List active (runtime) security filters of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        project_id: ID of a project; if omitted, the project selected
            on the connection is used
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=f'/api/dataModels/{id}/securityFilters',
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit, 'fields': fields},
    )


@ErrorHandler(
    err_msg="Error getting members of security filter with ID: "
    "{security_filter_id} of data model with ID: {id}"
)
def get_security_filter_members(
    connection: Connection,
    id: str,
    security_filter_id: str,
    project_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
):
    """Get users and user groups a data model security filter is applied to.

    The response contains split 'users' and 'userGroups' arrays with
    authoritative 'totalUsers' / 'totalUserGroups' counters.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        security_filter_id: ID of a security filter of the data model
        project_id: ID of a project; if omitted, the project selected
            on the connection is used
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=(f'/api/dataModels/{id}/securityFilters/{security_filter_id}/members'),
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit, 'fields': fields},
    )


@ErrorHandler(
    err_msg="Error updating members of security filter with ID: "
    "{security_filter_id} of data model with ID: {id}"
)
def update_security_filter_members(
    connection: Connection,
    id: str,
    security_filter_id: str,
    body: dict,
    project_id: str | None = None,
):
    """Update members of a data model security filter.

    The body must be of the form:
    `{'operationList': [{'op': <verb>, 'path': '/Members',
    'value': [<user or user group IDs>]}]}` where `op` MUST be one of
    the one-word camelCase verbs 'addElements', 'removeElements' or
    'replaceElements' (a plain 'add' is rejected) and `path` MUST be
    exactly '/Members' (leading slash, capital M). The response is
    204 with an empty body on success.

    Warning: this runtime path ('/api/dataModels/...') is the ONLY
    working members path — the '/api/model/...' variant 404s. Member
    assignment also requires the security filter's creation changeset
    to be committed first.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        security_filter_id: ID of a security filter of the data model
        body: Members update data ('operationList' shape above)
        project_id: ID of a project; if omitted, the project selected
            on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.patch(
        endpoint=(f'/api/dataModels/{id}/securityFilters/{security_filter_id}/members'),
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error getting publish status of data model with ID: {id}")
def get_publish_status(
    connection: Connection,
    id: str,
    instance_id: str,
    project_id: str | None = None,
    fields: str | None = None,
):
    """Poll the publish status of a data model instance.

    The instance ID is sent in the 'X-MSTR-DataModelInstanceId' header
    (required). Top-level 'status' semantics: 0 = all tables loaded,
    1 = queued/running, 5 = reserved, 6 = schema compared, negative =
    server error (e.g. -2147212544 = tenant-side QueryEngine stall —
    do not retry-loop; fall back to 'connect_live' serve mode).

    Warning (field-verified): instance IDs expire after ~2 minutes —
    a 404 ERR004 on this endpoint means the instance is gone; mint a
    new instance and re-publish.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        instance_id: ID of a data model instance (from the
            'X-MSTR-DataModelInstanceId' response header of
            `create_data_model_instance`)
        project_id: ID of a project; if omitted, the project selected
            on the connection is used
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=f'/api/dataModels/{id}/publishStatus',
        headers={
            'X-MSTR-DataModelInstanceId': instance_id,
            'X-MSTR-ProjectID': project_id,
        },
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error publishing data model with ID: {id}")
def publish_data_model(
    connection: Connection,
    id: str,
    instance_id: str,
    body: dict,
    project_id: str | None = None,
):
    """Publish a data model instance.

    The instance ID is sent in the 'X-MSTR-DataModelInstanceId' header
    (required). The body is required and must list every logical table:
    `{'tables': [{'id': <logical table ID>, 'refreshPolicy':
    'replace' | 'add' | 'delete' | 'update' | 'upsert' | ...}]}`
    (DataModelRefreshSetting schema). An empty body returns 400
    "tableRefreshSettings cannot be null".

    Warning (field-verified): the 204 response is fire-and-forget —
    never report success without polling `get_publish_status` until the
    top-level status is 0 and every table is 'loaded'.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        instance_id: ID of a data model instance (from the
            'X-MSTR-DataModelInstanceId' response header of
            `create_data_model_instance`)
        body: Publish data ('tables' shape above)
        project_id: ID of a project; if omitted, the project selected
            on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint=f'/api/dataModels/{id}/publish',
        headers={
            'X-MSTR-DataModelInstanceId': instance_id,
            'X-MSTR-ProjectID': project_id,
        },
        json=body,
    )


# --------------------------------------------------------------------------
# Modeling block ('/api/model/dataModels/...', changeset-scoped)
# --------------------------------------------------------------------------


@unpack_information
@ErrorHandler(err_msg="Error creating a data model")
def create_data_model(
    connection: Connection,
    body: dict,
    changeset_id: str | None = None,
):
    """Create a new data model in the changeset, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        body: Data model creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint='/api/model/dataModels',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint='/api/model/dataModels',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@unpack_information
@ErrorHandler(err_msg="Error getting data model with ID: {id}")
def get_data_model(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
):
    """Get the definition of a single data model by ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@unpack_information
@ErrorHandler(err_msg="Error updating data model with ID: {id}")
def update_data_model(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update a specific data model in the changeset, based on the
    definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Data model update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(err_msg="Error saving data model with ID: {id} as a new object")
def save_data_model_as(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Save a data model as a new object.

    The body is of the form `{'name': <name>,
    'destinationFolderId': <folder ID, optional>}`. The response body
    is the plain object ID string of the new data model (no
    'information' wrapper).

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Save-as data ('name', optional 'destinationFolderId')
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/saveAs',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/saveAs',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


# Folders


@ErrorHandler(err_msg="Error listing folders of data model with ID: {id}")
def list_data_model_folders(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
):
    """List folders of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/folders',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={'limit': limit, 'offset': offset},
    )


@ErrorHandler(err_msg="Error creating a folder in data model with ID: {id}")
def create_data_model_folder(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Create a new folder in a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Folder creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/folders',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/folders',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting folder with ID: {folder_id} " "of data model with ID: {id}"
)
def get_data_model_folder(
    connection: Connection,
    id: str,
    folder_id: str,
    changeset_id: str | None = None,
):
    """Get the definition of a folder of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        folder_id: ID of a folder of the data model
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/folders/{folder_id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error deleting folder with ID: {folder_id} " "of data model with ID: {id}"
)
def delete_data_model_folder(
    connection: Connection,
    id: str,
    folder_id: str,
    changeset_id: str | None = None,
):
    """Delete a folder of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        folder_id: ID of a folder of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/folders/{folder_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/folders/{folder_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@ErrorHandler(
    err_msg="Error updating folder with ID: {folder_id} " "of data model with ID: {id}"
)
def update_data_model_folder(
    connection: Connection,
    id: str,
    folder_id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update a folder of a data model, based on the definition provided
    in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        folder_id: ID of a folder of the data model
        body: Folder update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/folders/{folder_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/folders/{folder_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


# Tables


@ErrorHandler(err_msg="Error listing tables of data model with ID: {id}")
def list_data_model_tables(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
    show_expression_as: list[str] | None = None,
    show_derived_columns: bool | None = None,
    show_derived_forms: bool | None = None,
    show_relationship_candidates: bool | None = None,
):
    """List logical tables of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_derived_columns: Specifies whether to return derived columns
        show_derived_forms: Specifies whether to return derived forms
        show_relationship_candidates: Specifies whether to return
            relationship candidates

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/tables',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'showExpressionAs': show_expression_as,
            'showDerivedColumns': show_derived_columns,
            'showDerivedForms': show_derived_forms,
            'showRelationshipCandidates': show_relationship_candidates,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating a table in data model with ID: {id}")
def create_data_model_table(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
    fields: str | None = None,
    show_derived_columns: bool | None = None,
    show_derived_forms: bool | None = None,
):
    """Add a new logical table to a data model, based on the definition
    provided in the request body.

    Warning (field-verified): physical-table columns carrying
    warehouse-catalog sentinel data types ('variable_length_string' with
    precision -1, or decimal with scale -MIN_INT) make a later publish
    silently no-op — normalize column data types before creating.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Table creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_derived_columns: Specifies whether to return derived columns
        show_derived_forms: Specifies whether to return derived forms

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/tables',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'fields': fields,
                'showDerivedColumns': show_derived_columns,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/tables',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'fields': fields,
                'showDerivedColumns': show_derived_columns,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(
    err_msg="Error getting table with ID: {table_id} of data model with ID: {id}"
)
def get_data_model_table(
    connection: Connection,
    id: str,
    table_id: str,
    changeset_id: str | None = None,
    fields: str | None = None,
    show_expression_as: list[str] | None = None,
    show_derived_columns: bool | None = None,
    show_derived_forms: bool | None = None,
    show_relationship_candidates: bool | None = None,
):
    """Get the definition of a logical table of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        table_id: ID of a table of the data model
        changeset_id: ID of a changeset
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_derived_columns: Specifies whether to return derived columns
        show_derived_forms: Specifies whether to return derived forms
        show_relationship_candidates: Specifies whether to return
            relationship candidates

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/tables/{table_id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'fields': fields,
            'showExpressionAs': show_expression_as,
            'showDerivedColumns': show_derived_columns,
            'showDerivedForms': show_derived_forms,
            'showRelationshipCandidates': show_relationship_candidates,
        },
    )


@ErrorHandler(
    err_msg="Error deleting table with ID: {table_id} " "of data model with ID: {id}"
)
def delete_data_model_table(
    connection: Connection,
    id: str,
    table_id: str,
    changeset_id: str | None = None,
):
    """Delete a logical table of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        table_id: ID of a table of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/tables/{table_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/tables/{table_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@unpack_information
@ErrorHandler(
    err_msg="Error updating table with ID: {table_id} " "of data model with ID: {id}"
)
def update_data_model_table(
    connection: Connection,
    id: str,
    table_id: str,
    body: dict,
    changeset_id: str | None = None,
    fields: str | None = None,
    show_derived_columns: bool | None = None,
    show_derived_forms: bool | None = None,
):
    """Update a logical table of a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        table_id: ID of a table of the data model
        body: Table update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_derived_columns: Specifies whether to return derived columns
        show_derived_forms: Specifies whether to return derived forms

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/tables/{table_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'fields': fields,
                'showDerivedColumns': show_derived_columns,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/tables/{table_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'fields': fields,
                'showDerivedColumns': show_derived_columns,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )


# Metrics


@ErrorHandler(err_msg="Error listing metrics of data model with ID: {id}")
def list_data_model_metrics(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
    fields: str | None = None,
):
    """List metrics of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/metrics',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'limit': limit,
            'offset': offset,
            'showExpressionAs': show_expression_as,
            'showFilterTokens': show_filter_tokens,
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating a metric in data model with ID: {id}")
def create_data_model_metric(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
):
    """Create a new metric in a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Metric creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/metrics',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/metrics',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(
    err_msg="Error getting metric with ID: {metric_id} " "of data model with ID: {id}"
)
def get_data_model_metric(
    connection: Connection,
    id: str,
    metric_id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
):
    """Get the definition of a metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/metrics/{metric_id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': show_filter_tokens,
            'showAdvancedProperties': show_advanced_properties,
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(
    err_msg="Error updating metric with ID: {metric_id} " "of data model with ID: {id}"
)
def update_data_model_metric(
    connection: Connection,
    id: str,
    metric_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
):
    """Update a metric of a data model, based on the definition provided
    in the request body.

    This is a PUT — a full replace of the metric's definition; perform a
    read-modify-write to preserve fields you do not intend to change.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        body: Metric update data (full definition)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.put(
            endpoint=f'/api/model/dataModels/{id}/metrics/{metric_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/dataModels/{id}/metrics/{metric_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )


@ErrorHandler(
    err_msg="Error deleting metric with ID: {metric_id} " "of data model with ID: {id}"
)
def delete_data_model_metric(
    connection: Connection,
    id: str,
    metric_id: str,
    changeset_id: str | None = None,
):
    """Delete a metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/metrics/{metric_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/metrics/{metric_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@ErrorHandler(
    err_msg="Error getting applicable advanced properties of metric with ID: "
    "{metric_id} of data model with ID: {id}"
)
def get_metric_applicable_advanced_properties(
    connection: Connection,
    id: str,
    metric_id: str,
    changeset_id: str | None = None,
    show_sql_preview: bool | None = None,
):
    """Get the applicable advanced properties of a metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        changeset_id: ID of a changeset
        show_sql_preview: Specifies whether to return the SQL preview

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(
            f'/api/model/dataModels/{id}/metrics/{metric_id}'
            '/applicableAdvancedProperties'
        ),
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={'showSqlPreview': show_sql_preview},
    )


@ErrorHandler(
    err_msg="Error creating an embedded object in metric with ID: {metric_id} "
    "of data model with ID: {id}"
)
def create_metric_embedded_object(
    connection: Connection,
    id: str,
    metric_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
):
    """Create a new embedded object in a metric of a data model, based on
    the definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        body: Embedded object creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=(
                f'/api/model/dataModels/{id}/metrics/{metric_id}/embeddedObjects'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=(
                f'/api/model/dataModels/{id}/metrics/{metric_id}/embeddedObjects'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
            },
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting embedded object with ID: {embedded_object_id} "
    "of metric with ID: {metric_id} of data model with ID: {id}"
)
def get_metric_embedded_object(
    connection: Connection,
    id: str,
    metric_id: str,
    embedded_object_id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
):
    """Get the definition of an embedded object of a metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        embedded_object_id: ID of an embedded object of the metric
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(
            f'/api/model/dataModels/{id}/metrics/{metric_id}'
            f'/embeddedObjects/{embedded_object_id}'
        ),
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': show_filter_tokens,
        },
    )


@ErrorHandler(
    err_msg="Error updating embedded object with ID: {embedded_object_id} "
    "of metric with ID: {metric_id} of data model with ID: {id}"
)
def update_metric_embedded_object(
    connection: Connection,
    id: str,
    metric_id: str,
    embedded_object_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool | None = None,
):
    """Update an embedded object of a metric of a data model, based on the
    definition provided in the request body.

    This is a PUT — a full replace of the embedded object's definition.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        metric_id: ID of a metric of the data model
        embedded_object_id: ID of an embedded object of the metric
        body: Embedded object update data (full definition)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/metrics/{metric_id}'
                f'/embeddedObjects/{embedded_object_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/metrics/{metric_id}'
                f'/embeddedObjects/{embedded_object_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': show_filter_tokens,
            },
            json=body,
        )


# Object governance (ACLs, translations)


@ErrorHandler(
    err_msg="Error getting ACL of object with ID: {object_id} "
    "of data model with ID: {id}"
)
def get_data_model_object_acl(
    connection: Connection,
    id: str,
    object_id: str,
    sub_type: str,
    changeset_id: str | None = None,
):
    """Get the ACL of an object of a data model.

    Warning (field-verified): the server returns 500 when 'subType' is
    omitted, and with a WRONG subType it silently returns a
    consistent-but-wrong facet — always pass the object's true subtype
    (e.g. 'attribute', 'metric', 'fact_metric', 'logical_table',
    'md_security_filter').

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        object_id: ID of an object of the data model
        sub_type: Subtype of the object, e.g. 'attribute', 'metric',
            'fact_metric', 'logical_table', 'md_security_filter'
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/objects/{object_id}/acl',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={'subType': sub_type},
    )


@ErrorHandler(
    err_msg="Error updating ACL of object with ID: {object_id} "
    "of data model with ID: {id}"
)
def update_data_model_object_acl(
    connection: Connection,
    id: str,
    object_id: str,
    sub_type: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update the ACL of an object of a data model.

    The body shape is `{'acl': {<trustee ID>: {'granted': <int mask>,
    'denied': <int mask>, 'subType': 'user' | 'user_group',
    'inheritable': <bool>}}}`. 255 is the server's magic "Full Control"
    mask (do not decompose it from flag names).

    Warning (field-verified): this PATCH is a wholesale replacement —
    trustees omitted from the body are REMOVED from the ACL. With a
    WRONG 'subType' it silently patches a consistent-but-wrong facet —
    always pass the object's true subtype.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        object_id: ID of an object of the data model
        sub_type: Subtype of the object, e.g. 'attribute', 'metric',
            'fact_metric', 'logical_table', 'md_security_filter'
        body: ACL update data ('acl' shape above)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/objects/{object_id}/acl',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={'subType': sub_type},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/objects/{object_id}/acl',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={'subType': sub_type},
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting translations of object with ID: {object_id} "
    "of data model with ID: {id}"
)
def get_data_model_object_translations(
    connection: Connection,
    id: str,
    object_id: str,
    sub_type: str,
    changeset_id: str | None = None,
):
    """Get the translations of an object of a data model.

    Warning (field-verified): the server returns 500 when 'subType' is
    omitted, and with a WRONG subType it silently returns a
    consistent-but-wrong facet — always pass the object's true subtype.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        object_id: ID of an object of the data model
        sub_type: Subtype of the object, e.g. 'attribute', 'metric',
            'fact_metric', 'logical_table', 'md_security_filter'
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(f'/api/model/dataModels/{id}/objects/{object_id}/translations'),
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={'subType': sub_type},
    )


@ErrorHandler(
    err_msg="Error updating translations of object with ID: {object_id} "
    "of data model with ID: {id}"
)
def update_data_model_object_translations(
    connection: Connection,
    id: str,
    object_id: str,
    sub_type: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update the translations of an object of a data model.

    Warning (field-verified): with a WRONG 'subType' the server silently
    patches a consistent-but-wrong facet — always pass the object's true
    subtype.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        object_id: ID of an object of the data model
        sub_type: Subtype of the object, e.g. 'attribute', 'metric',
            'fact_metric', 'logical_table', 'md_security_filter'
        body: Translations update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=(f'/api/model/dataModels/{id}/objects/{object_id}/translations'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={'subType': sub_type},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=(f'/api/model/dataModels/{id}/objects/{object_id}/translations'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={'subType': sub_type},
            json=body,
        )


# Security filters (modeling)


@ErrorHandler(err_msg="Error listing security filters of data model with ID: {id}")
def list_data_model_security_filters(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
):
    """List security filters of a data model (modeling collection).

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/securityFilters',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={'limit': limit, 'offset': offset},
    )


@unpack_information
@ErrorHandler(err_msg="Error creating a security filter in data model with ID: {id}")
def create_data_model_security_filter(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
    show_filter_tokens: bool | None = None,
    show_expression_as: list[str] | None = None,
):
    """Create a new security filter in a data model, based on the
    definition provided in the request body.

    Note: 'information.subType' must be 'md_security_filter' (not
    'security_filter'), and attribute form references in the
    qualification need `subType: 'attribute_form_system'`. Member
    assignment is performed via the runtime endpoint
    (`update_security_filter_members`) and requires the creation
    changeset to be committed first (this function commits its
    changeset automatically).

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Security filter creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/securityFilters',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showFilterTokens': show_filter_tokens,
                'showExpressionAs': show_expression_as,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/securityFilters',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showFilterTokens': show_filter_tokens,
                'showExpressionAs': show_expression_as,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(
    err_msg="Error getting security filter with ID: {security_filter_id} "
    "of data model with ID: {id}"
)
def get_data_model_security_filter(
    connection: Connection,
    id: str,
    security_filter_id: str,
    changeset_id: str | None = None,
    show_filter_tokens: bool | None = None,
    show_expression_as: list[str] | None = None,
):
    """Get the definition of a security filter of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        security_filter_id: ID of a security filter of the data model
        changeset_id: ID of a changeset
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(f'/api/model/dataModels/{id}/securityFilters/{security_filter_id}'),
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showFilterTokens': show_filter_tokens,
            'showExpressionAs': show_expression_as,
        },
    )


@unpack_information
@ErrorHandler(
    err_msg="Error updating security filter with ID: {security_filter_id} "
    "of data model with ID: {id}"
)
def update_data_model_security_filter(
    connection: Connection,
    id: str,
    security_filter_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_filter_tokens: bool | None = None,
    show_expression_as: list[str] | None = None,
):
    """Update a security filter of a data model, based on the definition
    provided in the request body.

    This is a PUT — a full replace of the security filter's definition.
    Member assignment is performed via the runtime endpoint
    (`update_security_filter_members`).

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        security_filter_id: ID of a security filter of the data model
        body: Security filter update data (full definition)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_filter_tokens: Specifies whether 'qualification' is returned
            in 'tokens' format, along with 'text' and 'tree' formats
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/securityFilters' f'/{security_filter_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showFilterTokens': show_filter_tokens,
                'showExpressionAs': show_expression_as,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/securityFilters' f'/{security_filter_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showFilterTokens': show_filter_tokens,
                'showExpressionAs': show_expression_as,
            },
            json=body,
        )


@ErrorHandler(
    err_msg="Error deleting security filter with ID: {security_filter_id} "
    "of data model with ID: {id}"
)
def delete_data_model_security_filter(
    connection: Connection,
    id: str,
    security_filter_id: str,
    changeset_id: str | None = None,
):
    """Delete a security filter of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        security_filter_id: ID of a security filter of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=(
                f'/api/model/dataModels/{id}/securityFilters' f'/{security_filter_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=(
                f'/api/model/dataModels/{id}/securityFilters' f'/{security_filter_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


# Hierarchy


@ErrorHandler(err_msg="Error getting hierarchy of data model with ID: {id}")
def get_data_model_hierarchy(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
):
    """Get the hierarchy of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/hierarchy',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


# Attributes


@ErrorHandler(err_msg="Error listing attributes of data model with ID: {id}")
def list_data_model_attributes(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
    show_expression_as: list[str] | None = None,
    show_derived_forms: bool | None = None,
    show_subscription_filter_candidates_only: bool | None = None,
):
    """List attributes of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_derived_forms: Specifies whether to return derived forms
        show_subscription_filter_candidates_only: Specifies whether to
            return only attributes that are subscription filter candidates

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/attributes',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'showExpressionAs': show_expression_as,
            'showDerivedForms': show_derived_forms,
            'showSubscriptionFilterCandidatesOnly': (
                show_subscription_filter_candidates_only
            ),
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating an attribute in data model with ID: {id}")
def create_data_model_attribute(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    fields: str | None = None,
    allow_link: bool | None = None,
    show_derived_forms: bool | None = None,
):
    """Create a new attribute in a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Attribute creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        allow_link: Specifies whether linking is allowed
        show_derived_forms: Specifies whether to return derived forms

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/attributes',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'fields': fields,
                'allowLink': allow_link,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/attributes',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'fields': fields,
                'allowLink': allow_link,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(
    err_msg="Error getting attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def get_data_model_attribute(
    connection: Connection,
    id: str,
    attribute_id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
    show_derived_forms: bool | None = None,
):
    """Get the definition of an attribute of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        show_derived_forms: Specifies whether to return derived forms

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/attributes/{attribute_id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showAdvancedProperties': show_advanced_properties,
            'fields': fields,
            'showDerivedForms': show_derived_forms,
        },
    )


@ErrorHandler(
    err_msg="Error deleting attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def delete_data_model_attribute(
    connection: Connection,
    id: str,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Delete an attribute of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/attributes/{attribute_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=f'/api/model/dataModels/{id}/attributes/{attribute_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@unpack_information
@ErrorHandler(
    err_msg="Error updating attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def update_data_model_attribute(
    connection: Connection,
    id: str,
    attribute_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    fields: str | None = None,
    allow_link: bool | None = None,
    show_derived_forms: bool | None = None,
):
    """Update an attribute of a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        body: Attribute update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        allow_link: Specifies whether linking is allowed
        show_derived_forms: Specifies whether to return derived forms

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/attributes/{attribute_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'fields': fields,
                'allowLink': allow_link,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/dataModels/{id}/attributes/{attribute_id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'fields': fields,
                'allowLink': allow_link,
                'showDerivedForms': show_derived_forms,
            },
            json=body,
        )


@ErrorHandler(
    err_msg="Error getting relationships of attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def get_data_model_attribute_relationships(
    connection: Connection,
    id: str,
    attribute_id: str,
    changeset_id: str | None = None,
):
    """Get the relationships of an attribute of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=(
            f'/api/model/dataModels/{id}/attributes/{attribute_id}' '/relationships'
        ),
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error updating relationships of attribute with ID: {attribute_id} "
    "of data model with ID: {id}"
)
def update_data_model_attribute_relationships(
    connection: Connection,
    id: str,
    attribute_id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update the relationships of an attribute of a data model.

    Warning (field-verified): this PUT replaces the attribute's ENTIRE
    relationship list — any existing relationship omitted from the body
    is DELETED. Always read the current relationships first and perform
    a read-modify-write.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        attribute_id: ID of an attribute of the data model
        body: Relationships update data (full list)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/attributes/{attribute_id}' '/relationships'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=(
                f'/api/model/dataModels/{id}/attributes/{attribute_id}' '/relationships'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


# Fact metrics


@ErrorHandler(err_msg="Error listing fact metrics of data model with ID: {id}")
def list_data_model_fact_metrics(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    show_expression_as: list[str] | None = None,
    fields: str | None = None,
):
    """List fact metrics of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/factMetrics',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'limit': limit,
            'offset': offset,
            'showExpressionAs': show_expression_as,
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating a fact metric in data model with ID: {id}")
def create_data_model_fact_metric(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_advanced_properties: bool | None = None,
    allow_link: bool | None = None,
    fields: str | None = None,
):
    """Create a new fact metric in a data model, based on the definition
    provided in the request body.

    Note: this endpoint also creates compound, conditional and
    transformation metrics — the differentiator is which top-level body
    keys are set.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Fact metric creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        allow_link: Specifies whether linking is allowed
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/factMetrics',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showAdvancedProperties': show_advanced_properties,
                'allowLink': allow_link,
                'fields': fields,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/factMetrics',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showAdvancedProperties': show_advanced_properties,
                'allowLink': allow_link,
                'fields': fields,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(
    err_msg="Error getting fact metric with ID: {fact_metric_id} "
    "of data model with ID: {id}"
)
def get_data_model_fact_metric(
    connection: Connection,
    id: str,
    fact_metric_id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
):
    """Get the definition of a fact metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        fact_metric_id: ID of a fact metric of the data model
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/factMetrics/{fact_metric_id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showAdvancedProperties': show_advanced_properties,
            'fields': fields,
        },
    )


@ErrorHandler(
    err_msg="Error deleting fact metric with ID: {fact_metric_id} "
    "of data model with ID: {id}"
)
def delete_data_model_fact_metric(
    connection: Connection,
    id: str,
    fact_metric_id: str,
    changeset_id: str | None = None,
):
    """Delete a fact metric of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        fact_metric_id: ID of a fact metric of the data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=(f'/api/model/dataModels/{id}/factMetrics/{fact_metric_id}'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=(f'/api/model/dataModels/{id}/factMetrics/{fact_metric_id}'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@unpack_information
@ErrorHandler(
    err_msg="Error updating fact metric with ID: {fact_metric_id} "
    "of data model with ID: {id}"
)
def update_data_model_fact_metric(
    connection: Connection,
    id: str,
    fact_metric_id: str,
    body: dict,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_advanced_properties: bool | None = None,
    fields: str | None = None,
):
    """Update a fact metric of a data model, based on the definition
    provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        fact_metric_id: ID of a fact metric of the data model
        body: Fact metric update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.
        show_expression_as: Specifies the format in which the expressions
            are returned in response.
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format.
        show_advanced_properties: Specifies whether to retrieve the values
            of the advanced properties
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=(f'/api/model/dataModels/{id}/factMetrics/{fact_metric_id}'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=(f'/api/model/dataModels/{id}/factMetrics/{fact_metric_id}'),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showAdvancedProperties': show_advanced_properties,
                'fields': fields,
            },
            json=body,
        )


# Links


@ErrorHandler(err_msg="Error listing links of data model with ID: {id}")
def list_data_model_links(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
):
    """List links of a data model.

    Quirk: unlike other modeling GETs, this endpoint REQUIRES the
    'X-MSTR-MS-Changeset' header even on the GET. When `changeset_id`
    is None, a temporary changeset is opened (and committed — harmless
    for a read) around the call.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset; if omitted, a temporary
            changeset is created automatically
        offset: Starting point within the collection of returned results.
            Used to control paging behavior.
        limit: Maximum number of items returned for a single request.
            Used to control paging behavior.

    Return:
        HTTP response object. Expected status: 200
    """
    params = {'limit': limit, 'offset': offset}
    if changeset_id is None:
        with changeset_manager(connection) as changeset_id:
            return connection.get(
                endpoint=f'/api/model/dataModels/{id}/links',
                headers={'X-MSTR-MS-Changeset': changeset_id},
                params=params,
            )
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/links',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params=params,
    )


@ErrorHandler(err_msg="Error updating links of data model with ID: {id}")
def update_data_model_links(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update the links of a data model.

    Warning: this PUT replaces ALL links of the data model — any
    existing link omitted from the body is DELETED. Perform a
    read-modify-write.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Links update data (full list)
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.put(
            endpoint=f'/api/model/dataModels/{id}/links',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/dataModels/{id}/links',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(err_msg="Error creating a link in data model with ID: {id}")
def create_data_model_link(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Create a new link in a data model, based on the definition provided
    in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: Link creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/links',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/links',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


# External data models


@ErrorHandler(err_msg="Error listing external data models of data model with ID: {id}")
def list_external_data_models(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
):
    """List external data models of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/dataModels/{id}/externalDataModels',
        headers={'X-MSTR-MS-Changeset': changeset_id},
    )


@ErrorHandler(
    err_msg="Error creating an external data model in data model with ID: {id}"
)
def create_external_data_model(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Add a new external data model to a data model, based on the
    definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        body: External data model creation data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 201
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/externalDataModels',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/externalDataModels',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error deleting external data model with ID: "
    "{external_data_model_id} of data model with ID: {id}"
)
def delete_external_data_model(
    connection: Connection,
    id: str,
    external_data_model_id: str,
    changeset_id: str | None = None,
):
    """Delete an external data model of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        external_data_model_id: ID of an external data model of the
            data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 204
    """
    if changeset_id is not None:
        return connection.delete(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.delete(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@ErrorHandler(
    err_msg="Error updating external data model with ID: "
    "{external_data_model_id} of data model with ID: {id}"
)
def update_external_data_model(
    connection: Connection,
    id: str,
    external_data_model_id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update an external data model of a data model, based on the
    definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        external_data_model_id: ID of an external data model of the
            data model
        body: External data model update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error updating object with ID: {object_id} of external data "
    "model with ID: {external_data_model_id} of data model with ID: {id}"
)
def update_external_data_model_object(
    connection: Connection,
    id: str,
    external_data_model_id: str,
    object_id: str,
    body: dict,
    changeset_id: str | None = None,
):
    """Update an object of an external data model of a data model, based
    on the definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        external_data_model_id: ID of an external data model of the
            data model
        object_id: ID of an object of the external data model
        body: External data model object update data
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.patch(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}/objects/{object_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )
    with changeset_manager(connection, body=body) as changeset_id:
        return connection.patch(
            endpoint=(
                f'/api/model/dataModels/{id}/externalDataModels'
                f'/{external_data_model_id}/objects/{object_id}'
            ),
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
        )


@ErrorHandler(
    err_msg="Error refreshing external data models of data model with ID: {id}"
)
def refresh_external_data_models(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
):
    """Refresh the external data models of a data model.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/externalDataModels/refresh',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/externalDataModels/refresh',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


# Export / restore


def export_data_model(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
):
    """Export a data model to YAML.

    The 200 response body is 'application/yaml' TEXT, not JSON — use
    `response.text` on the returned object; never call `.json()`.
    When `changeset_id` is None, a temporary changeset is opened (and
    committed — harmless for an export) around the call.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        changeset_id: ID of a changeset; if omitted, a temporary
            changeset is created automatically

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is None:
        with changeset_manager(connection) as new_changeset_id:
            response = connection.post(
                endpoint=f'/api/model/dataModels/{id}/export',
                headers={'X-MSTR-MS-Changeset': new_changeset_id},
            )
    else:
        response = connection.post(
            endpoint=f'/api/model/dataModels/{id}/export',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
    if not response.ok:
        response_handler(response, msg=f"Error exporting data model with ID: {id}")
    return response


@ErrorHandler(err_msg="Error restoring data model with ID: {id}")
def restore_data_model(
    connection: Connection,
    id: str,
    file: bytes | str,
    file_name: str = 'data_model.yaml',
    changeset_id: str | None = None,
):
    """Restore a data model from a YAML export.

    The request is 'multipart/form-data' with a single part named
    'dataModelFile' containing the binary YAML content.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a data model
        file: YAML content of the data model (bytes or string)
        file_name: Name of the uploaded file part
        changeset_id: ID of an already-open changeset to run this
            operation in; when omitted, a changeset is opened and
            committed automatically.

    Return:
        HTTP response object. Expected status: 200
    """
    if changeset_id is not None:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/restore',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            files={'dataModelFile': (file_name, file)},
        )
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/dataModels/{id}/restore',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            files={'dataModelFile': (file_name, file)},
        )
