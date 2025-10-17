from time import sleep, time

from requests import Response

from mstrio.api import reports as reports_api
from mstrio.connection import Connection


def get_report_status(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
    timeout: int = 60,
) -> Response:
    """Get stable status of a report instance.

    Args:
        connection: Strategy connection object returned by
            `connection.Connection()`.
        report_id (str): ID of the report.
        instance_id (str): ID of the report instance.
        project_id (str, optional): ID of the project.
        fields (str, optional): Comma-separated list of fields to be returned
            in the response.
        error_msg (str, optional): Custom error message to be displayed in case
            of an error.
        timeout (int): Maximum time in seconds to wait for the operation to
            complete. Defaults to 60.

    Returns:
        Complete HTTP response object. Status code 200 when report is ready.
        If timeout is exceeded, returns the last response as-is.
    """

    start_time = time()

    response = reports_api.get_report_status(
        connection=connection,
        report_id=report_id,
        instance_id=instance_id,
        project_id=project_id,
        fields=fields,
        error_msg=error_msg,
    )

    while response.ok and response.status_code == 202:
        # Check if timeout has been exceeded
        elapsed_time = time() - start_time
        if elapsed_time >= timeout:
            return response  # Return the current response instead of raising error

        retry_after = int(response.headers.get('Retry-After', 1))
        sleep(retry_after)

        response = reports_api.get_report_status(
            connection=connection,
            report_id=report_id,
            instance_id=instance_id,
            project_id=project_id,
            fields=fields,
            error_msg=error_msg,
        )

    return response
