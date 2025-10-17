from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.utils.sessions import FuturesSessionWithRenewal


@ErrorHandler(err_msg="Error getting available dashboards.")
def get_dashboards(
    connection: 'Connection',
    offset: int = 0,
    limit: int = -1,
    search_term: str | None = None,
    certified_status: str | None = None,
    search_pattern: str | None = None,
    fields: str | None = None,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get the list of available dashboards.

    Args:
        connection(object): Strategy One REST API connection object
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single request.
            Used to control paging behavior.
        search_term(str, optional): The value that the search searchPattern is
            set to.
        certified_status(str, optional): Define a search criteria of the
            certified status of the object
        search_pattern(str, optional): The kind of search pattern that will be
            applied to the search,
        fields(str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.
        project_id (string, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = '/api/dossiers'
    return connection.get(
        endpoint=endpoint,
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'certifiedStatus': certified_status,
            'fields': fields,
        },
    )


def get_dashboards_async(
    future_session: 'FuturesSessionWithRenewal',
    offset: int = 0,
    limit: int = -1,
    search_term: str | None = None,
    certified_status: str | None = None,
    search_pattern: str | None = None,
    fields: str | None = None,
    project_id: str | None = None,
):
    """Get the list of available dashboards asynchronously.

    Args:
        future_session: FuturesSessionWithRenewal object
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single request.
            Used to control paging behavior.
        search_term(str, optional): The value that the search searchPattern is
            set to.
        certified_status(str, optional): Define a search criteria of the
            certified status of the object
        search_pattern(str, optional): The kind of search pattern that will be
            applied to the search,
        fields(str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.
        project_id(str, optional): Project ID of the project to use. If not
            set then the project selected in `connection` will be used.

    Returns:
        Complete HTTP response object.
    """
    future_session.connection._validate_project_selected()
    endpoint = '/api/dossiers'
    headers = ({'X-MSTR-ProjectID': project_id},)
    params = {
        'searchTerm': search_term,
        'searchPattern': search_pattern,
        'offset': offset,
        'limit': limit,
        'certifiedStatus': certified_status,
        'fields': fields,
    }
    return future_session.get(endpoint=endpoint, params=params, headers=headers)


@ErrorHandler(err_msg="Error getting available documents.")
def get_documents(
    connection: 'Connection',
    offset: int = 0,
    limit: int = -1,
    search_pattern: str = None,
    search_term: str | None = None,
    certified_status: str | None = None,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get the list of available documents.

    Args:
        connection: Strategy One REST API connection object
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single request.
            Used to control paging behavior.
        search_pattern(str, optional): The kind of search pattern that will be
            applied to the search,
        search_term(str, optional): The value that the search searchPattern is
            set to.
        certified_status(str, optional): Define a search criteria of the
            certified status of the object
        project_id(str, optional): Project ID
        fields(str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = '/api/documents/'
    return connection.get(
        endpoint=endpoint,
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'certifiedStatus': certified_status,
            'fields': fields,
        },
    )


def get_documents_async(
    future_session: 'FuturesSessionWithRenewal',
    offset: int = 0,
    limit: int = -1,
    search_pattern: str = None,
    search_term: str | None = None,
    project_id: str | None = None,
    certified_status: str | None = None,
    fields: str | None = None,
):
    """Get the list of available documents asynchronously.

    Args:
        future_session: FutureSession object
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single request.
            Used to control paging behavior.
        search_pattern(str, optional): The kind of search pattern that will be
            applied to the search,
        search_term(str, optional): The value that the search searchPattern is
            set to.
        project_id(str, optional): Project ID
        certified_status(str, optional): Define a search criteria of the
            certified status of the object
        fields(str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.

    Returns:
        Complete HTTP response object.
    """
    endpoint = '/api/documents/'
    params = {
        'searchTerm': search_term,
        'searchPattern': search_pattern,
        'offset': offset,
        'limit': limit,
        'certifiedStatus': certified_status,
        'fields': fields,
    }
    headers = {'X-MSTR-ProjectID': project_id}
    future = future_session.get(endpoint=endpoint, params=params, headers=headers)
    return future


@ErrorHandler(err_msg="Error getting document {document_id}")
def get_document_status(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get the status of a dashboard or document instance.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        project_id (string, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        endpoint=f'/api/documents/{document_id}/instances/{instance_id}/status',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting prompts for document {document_id}")
def get_prompts_for_instance(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    closed: bool | None = None,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get the collection of prompts and their respective definitions from a
    dashboard/document instance.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        closed(bool, optional): Prompt status, true means get closed prompt,
            false means get open prompt
        project_id (string, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/prompts'
    return connection.get(
        endpoint=endpoint,
        headers={'X-MSTR-ProjectID': project_id},
        params={'closed': closed},
    )


@ErrorHandler(err_msg="Error getting attribute element for prompt {prompt_identifier}")
def get_attribute_element_for_prompt(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    prompt_identifier: str,
    error_msg: str | None = None,
    project_id: str | None = None,
) -> 'Response':
    """Get available attribute element for dashboard/document's
    attribute element prompt.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        prompt_identifier (string): Prompt key or ID
        error_msg (string, optional): Custom Error Message for Error Handling
        project_id (string, optional): Project ID

    Returns:
        Complete HTTP response object.
    """
    if not project_id:
        project_id = connection.project_id
    endpoint = (
        f'/api/documents/{document_id}/instances/{instance_id}'
        f'/prompts/{prompt_identifier}/elements'
    )
    return connection.get(endpoint=endpoint, headers={'X-MSTR-ProjectID': project_id})


@ErrorHandler(err_msg="Error getting available object for prompt {prompt_identifier}")
def get_available_object(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    prompt_identifier: str,
    error_msg: str | None = None,
) -> 'Response':
    """Get available object for answering all kinds of prompts.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        prompt_identifier (string): Prompt key or ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = (
        f'api/documents/{document_id}/instances/'
        f'{instance_id}/prompts/{prompt_identifier}/objects'
    )
    return connection.get(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(
    err_msg="Error exporting visualization for document {document_id} to PDF file."
)
def export_visualization_to_pdf(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    node_key: str,
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Export a single visualization from a specific document instance to a PDF
    file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        node_key (string): Visualization node key
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = (
        f'/api/documents/{document_id}/instances/{instance_id}'
        f'/visualizations/{node_key}/pdf'
    )
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': None}, json=body
    )


@ErrorHandler(
    err_msg="Error exporting visualization for document {document_id} to CSV file."
)
def export_visualization_to_csv(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    node_key: str,
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Export a single visualization from a specific document instance to a CSV
    file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        node_key (string): Visualization node key
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = (
        f'/api/documents/{document_id}/instances/{instance_id}'
        f'/visualizations/{node_key}/csv'
    )
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': None}, json=body
    )


@ErrorHandler(err_msg="Error exporting document {document_id} to PDF file.")
def export_document_to_pdf(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Export a specific document instance to a PDF file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    project_id = connection.project_id
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/pdf'
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': project_id}, json=body
    )


@ErrorHandler(err_msg="Error exporting document {document_id} to .mstr file")
def export_document_to_mstr(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Export a specific document in a specific project to an .mstr file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    project_id = connection.project_id
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/mstr'
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': project_id}, json=body
    )


@ErrorHandler(err_msg="Error exporting document {document_id} to Excel file.")
def export_document_to_excel(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Export a document from a specific document instance to an Excel file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    project_id = connection.project_id
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/excel'
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': project_id}, json=body
    )


@ErrorHandler(err_msg="Error setting document {document_id} to prompt status.")
def set_document_to_prompt_status(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Export a document from a specific document instance to an Excel file.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/rePrompt'
    return connection.post(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error getting cubes used by document {document_id}")
def get_cubes_used_by_document(
    connection: 'Connection', document_id: str, error_msg: str | None = None
) -> 'Response':
    """Get the cubes used by a document in a specific project, either directly
    or indirectly.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/cubes'
    return connection.get(endpoint=endpoint)


@ErrorHandler(err_msg="Error overwriting document {document_id}")
def overwrite_document(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Save a document instance by overwriting an existing document.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/save'
    return connection.post(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error saving document {document_id}")
def save_document_as(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Save a document instance by creating a new document.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/saveAs'
    return connection.post(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error creating instance for document {document_id}")
def create_new_document_instance(
    connection: 'Connection', document_id: str, body: dict, error_msg: str | None = None
) -> 'Response':
    """Execute a specific document in a specific project and create an instance
    of the document.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances'
    return connection.post(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error deleting document instance {instance_id}")
def delete_document_instance(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Save a document instance by overwriting an existing document.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}'
    return connection.delete(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error refreshing document instance {instance_id}")
def refresh_document_instance(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Execute a specific document in a specific project and create an instance
    of the document.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/refresh'
    return connection.put(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error getting collection of prompts for document {document_id}")
def get_prompts(
    connection: 'Connection',
    document_id: str,
    project_id: str | None = None,
    closed: bool | None = None,
    error_msg=None,
) -> 'Response':
    """Get the collection of prompts and their respective definitions from a
    dashboard/document definition.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        project_id (string, optional): Project ID
        closed (bool, optional): Prompt status, true means get closed prompt,
            false means get open prompt
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/prompts'
    return connection.get(
        endpoint=endpoint,
        headers={'X-MSTR-ProjectID': project_id},
        params={'closed': closed},
    )


@ErrorHandler(err_msg="Error answering prompt for instance {instance_id}")
def answer_prompts(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    body: dict,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Answer specified prompts on the dashboard/document instance, prompts can
    either be answered with default answers(if available), the appropriate
    answers, or if the prompt is not required the prompt can simply be closed.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        project_id (string, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/prompts/answers'
    return connection.put(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': project_id}, json=body
    )


@ErrorHandler(err_msg="Error retrieving document shortcut for document {document_id}")
def get_document_shortcut(
    connection: 'Connection',
    document_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Retrieve a published shortcut from a specific document instance.

    Args:
        connection: Strategy One REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/documents/{document_id}/instances/{instance_id}/shortcut'
    return connection.get(endpoint=endpoint)


@ErrorHandler(err_msg="Error creating instance for dashboard {dashboard_id}")
def create_dashboard_instance(
    connection: 'Connection',
    dashboard_id: str,
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Execute a specific dashboard and create an instance of the dashboard.

    Args:
        connection: Strategy One REST API connection object
        dashboard_id (string): Dashboard ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/dossiers/{dashboard_id}/instances'
    return connection.post(
        endpoint=endpoint, headers={'X-MSTR-ProjectID': None}, json=body
    )


@ErrorHandler(err_msg="Error getting hierarchy for dashboard {id}")
def get_dashboard_hierarchy(connection: 'Connection', id: str) -> Response:
    """Get the hierarchy of a specific dashboard in a specific project.

    Args:
        connection: Strategy One REST API connection object
        id (string): Dashboard ID

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/v2/dossiers/{id}/definition/'
    return connection.get(endpoint=endpoint)


@ErrorHandler(err_msg="Error getting definition of document {id}")
def get_document_definition(
    connection: 'Connection', id: str, error_msg: str | None = None
) -> 'Response':
    """Get details about a specific document.

    Args:
        connection: Strategy One REST API connection object
        id (string): Document ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/v2/documents/{id}'
    return connection.get(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg="Error getting dashboard hierarchy from instance {instance_id}")
def get_dashboard_hierarchy_from_instance(
    connection: 'Connection',
    dashboard_id: str,
    instance_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Get the hierarchy of a specific dashboard in a specific project from
    instance.

    Args:
        connection: Strategy One REST API connection object
        dashboard_id (string): Dashboard ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'api/v2/dossiers/{dashboard_id}/instances/{instance_id}/definition'
    return connection.get(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(
    err_msg="Error getting definition and results for dashboard {dashboard_id}"
)
def get_definition_and_results_of_visualization(
    connection: 'Connection',
    instance_id: str,
    chapter_key: str,
    visualization_key: str,
    dashboard_id: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get the definition and data result of a grid/graph visualization in a
    specific dashboard in a specific project.

    Args:
        connection: Strategy One REST API connection object
        instance_id (string): Document Instance ID
        chapter_key (string): Chapter Key
        visualization_key (string): Visualization Key
        dashboard_id (string, optional): Dashboard ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    endpoint = (
        f'/api/v2/dossiers/{dashboard_id}'
        f'/instances/{instance_id}/chapters/{chapter_key}'
        f'/visualizations/{visualization_key}'
    )
    return connection.get(endpoint=endpoint, headers={'X-MSTR-ProjectID': None})
