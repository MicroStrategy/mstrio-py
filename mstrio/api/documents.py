from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession


@ErrorHandler(err_msg='Error getting available dossiers.')
def get_dossiers(connection, search_term, certified_status, search_pattern='EXACTLY', offset=0,
                 limit=-1, fields=None, error_msg=None):
    """Get the list of available dossiers.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f'{connection.base_url}/api/dossiers'
    return connection.get(
        url=url,
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'fields': fields
        },
    )


def get_dossiers_async(future_session: "FuturesSession", connection, search_term, certified_status,
                       search_pattern='EXACTLY', offset=0, limit=-1, fields=None, error_msg=None):
    """Get the list of available dossiers asynchronously.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    url = f'{connection.base_url}/api/dossiers'
    params = {
        'searchTerm': search_term,
        'searchPattern': search_pattern,
        'offset': offset,
        'limit': limit,
        'fields': fields
    }
    return future_session.get(url=url, params=params)


@ErrorHandler(err_msg='Error getting available documents.')
def get_documents(connection, search_term, certified_status, search_pattern='EXACTLY', offset=0,
                  limit=-1, fields=None, error_msg=None):
    """Get the list of available documents.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f'{connection.base_url}/api/documents/'
    return connection.get(
        url=url,
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'fields': fields
        },
    )


def get_documents_async(future_session: "FuturesSession", connection, search_term,
                        certified_status, search_pattern='EXACTLY', offset=0, limit=-1,
                        fields=None, error_msg=None):
    """Get the list of available documents asynchronously.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f'{connection.base_url}/api/documents/'
    params = {
        'searchTerm': search_term,
        'searchPattern': search_pattern,
        'offset': offset,
        'limit': limit,
        'fields': fields
    }
    future = future_session.get(url=url, params=params)
    return future


@ErrorHandler(err_msg='Error getting document {document_id}')
def get_document_status(connection, document_id, instance_id, error_msg=None):
    """Get the status of a document or dossier instance.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/status"
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting prompts for document {document_id}')
def get_prompts_for_instance(connection, document_id, instance_id, error_msg=None):
    """Get the collection of prompts and their respective definitions from a
    document/dossier instance.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/prompts"  # noqa
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting attribute element for prompt {prompt_identifier}')
def get_attribute_element_for_prompt(connection, document_id, instance_id, prompt_identifier,
                                     error_msg=None):
    """Get available attribute element for document/dossier's attribute element
    prompt.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        prompt_identifier (string): Prompt key or ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/prompts​/{prompt_identifier}​/elements"  # noqa
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting available object for prompt {prompt_identifier}')
def get_available_object(connection, document_id, instance_id, prompt_identifier, error_msg=None):
    """Get available object for answering all kinds of prompts.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        prompt_identifier (string): Prompt key or ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api​/documents​/{document_id}​/instances​/{instance_id}​/prompts​/{prompt_identifier}​/objects"  # noqa
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error exporting visualization for document {document_id} to PDF file.')
def export_visualization_to_pdf(connection, document_id, instance_id, node_key, body,
                                error_msg=None):
    """Export a single visualization from a specific document instance to a PDF
    file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/visualizations​/{node_key}​/pdf"  # noqa
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error exporting visualization for document {document_id} to CSV file.')
def export_visualization_to_csv(connection, document_id, instance_id, node_key, body,
                                error_msg=None):
    """Export a single visualization from a specific document instance to a CSV
    file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        node_key (string): Visualization node key
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/visualizations​/{node_key}​/csv"  # noqa
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error exporting document {document_id} to PDF file.')
def export_document_to_pdf(connection, document_id, instance_id, body, error_msg=None):
    """Export a specific document instance to a PDF file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/pdf"
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error exporting document {document_id} to .mstr file')
def export_document_to_mstr(connection, document_id, instance_id, body, error_msg=None):
    """Export a specific document in a specific project to an .mstr file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/mstr"
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error exporting document {document_id} to Excel file.')
def export_document_to_excel(connection, document_id, instance_id, body, error_msg=None):
    """Export a document from a specific document instance to an Excel file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/excel"
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error setting document {document_id} to prompt status.')
def set_document_to_prompt_status(connection, document_id, instance_id, error_msg=None):
    """Export a document from a specific document instance to an Excel file.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/rePrompt"  # noqa
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting cubes used by document {document_id}')
def get_cubes_used_by_document(connection, document_id, error_msg=None):
    """Get the cubes used by a document in a specific project, either directly
    or indirectly.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/documents/{document_id}/cubes"
    return connection.get(url=url)


@ErrorHandler(err_msg='Error overwriting document {document_id}')
def overwrite_document(connection, document_id, instance_id, error_msg=None):
    """Save a document instance by overwriting an existing document.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​/save"
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error saving document {document_id}')
def save_document_as(connection, document_id, instance_id, error_msg=None):
    """Save a document instance by creating a new document.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api​/documents​/{document_id}​/instances​/{instance_id}​/saveAs"  # noqa
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error creating instance for document {document_id}')
def create_new_document_instance(connection, document_id, body, error_msg=None):
    """Execute a specific document in a specific project and create an instance
    of the document.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/documents/{document_id}/instances"
    return connection.post(url=url, json=body)


@ErrorHandler(err_msg='Error deleting document instance {instance_id}')
def delete_document_instance(connection, document_id, instance_id, error_msg=None):
    """Save a document instance by overwriting an existing document.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances​/{instance_id}​"
    return connection.delete(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error refreshing document instance {instance_id}')
def refresh_document_instance(connection, document_id, instance_id, error_msg=None):
    """Execute a specific document in a specific project and create an instance
    of the document.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/instances/{instance_id}/refresh​"
    return connection.put(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting collection of prompts for document {document_id}')
def get_prompts(connection, document_id, error_msg=None):
    """Get the collection of prompts and their respective definitions from a
    document/dossier definition.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/documents​/{document_id}​/prompts"
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error answering prompt for instance {instance_id}')
def answer_prompts(connection, document_id, instance_id, body, error_msg=None):
    """Answer specified prompts on the document/dossier instance, prompts can
    either be answered with default answers(if available), the appropriate
    answers, or if the prompt is not required the prompt can simply be closed.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api​/documents​/{document_id}​/instances/{instance_id}/prompts/answers"  # noqa
    return connection.put(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error retrieving document shortcut for document {document_id}')
def get_document_shortcut(connection, document_id, instance_id, error_msg=None):
    """Retrieve a published shortcut from a specific document instance.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api​/documents​/{document_id}​/instances/{instance_id}/shortcut"
    return connection.get(url=url)


@ErrorHandler(err_msg='Error creating instance for dossier {dossier_id}')
def create_dossier_instance(connection, dossier_id, body, error_msg=None):
    """Execute a specific dossier and create an instance of the dossier.

    Args:
        connection: MicroStrategy REST API connection object
        dossier_id (string): Dossier ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}​/api​/dossiers/{dossier_id}​/instances​"
    return connection.post(url=url, headers={'X-MSTR-ProjectID': None}, json=body)


@ErrorHandler(err_msg='Error getting hierarchy for dossier {id}')
def get_dossier_hierarchy(connection, id, error_msg=None):
    """Get the hierarchy of a specific dossier in a specific project.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Dossier ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/v2/dossiers/{id}/definition/"
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting definition of document {id}')
def get_document_definition(connection, id, error_msg=None):
    """Get the hierarchy of a specific dossier in a specific project.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Dossier ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/v2/documents/{id}"
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting dossier hierarchy from instance {instance_id}')
def get_dossier_hierarchy_from_instance(connection, dossier_id, instance_id, error_msg=None):
    """Get the hierarchy of a specific dossier in a specific project from
    instance.

    Args:
        connection: MicroStrategy REST API connection object
        dossier_id (string): Dossier ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api​/v2/dossiers/{dossier_id}/​instances/{instance_id}/definition"  # noqa
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})


@ErrorHandler(err_msg='Error getting definition and results for dossier {dossier_id}')
def get_definition_and_results_of_visualization(connection, dossier_id, instance_id, chapter_key,
                                                visualization_key, error_msg=None):
    """Get the definition and data result of a grid/graph visualization in a
    specific dossier in a specific project.

    Args:
        connection: MicroStrategy REST API connection object
        dossier_id (string): Dossier ID
        instance_id (string): Document Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/​v2/dossiers​/{dossier_id}​/instances​/{instance_id}​/chapters​/{chapter_key}​/visualizations​/{visualization_key}"  # noqa
    return connection.get(url=url, headers={'X-MSTR-ProjectID': None})
