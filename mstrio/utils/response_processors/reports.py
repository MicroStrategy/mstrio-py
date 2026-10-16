from time import sleep, time

from requests import Response

from mstrio import config
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


def wait_for_report_ready(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    project_id: str | None = None,
    interval: int | float | None = None,
    timeout: int | float | None = None,
) -> Response:
    """Poll a report instance's status until its result is ready.

    Polls `GET /reports/{report_id}/instances/{instance_id}/status`, which
    returns HTTP 202 while the instance is still executing and HTTP 200 once
    the result is ready (in-body status 1) or prompts are pending (status 2).

    Args:
        connection: Strategy connection object returned by
            `connection.Connection()`.
        report_id (str): ID of the report.
        instance_id (str): ID of the report instance to poll.
        project_id (str, optional): ID of the project.
        interval (int | float, optional): Seconds to wait between polls.
            Defaults to `config.delay_between_polling`.
        timeout (int | float, optional): Maximum total time in seconds to wait
            for the result. If exceeded, `TimeoutError` is raised. Default is
            None (wait indefinitely), which is the point of async execution:
            heavy reports run as long as they need without a client-side cap.

    Returns:
        Complete HTTP response object with status code 200 when the report is
        ready or has pending prompts. The caller inspects the in-body `status`
        (1 = ready, 2 = prompts pending) to decide how to proceed.

    Raises:
        TimeoutError: If `timeout` is set and the total wait is exceeded.
        requests.HTTPError: If the server responds with an error (4xx or 5xx)
        at any point.
    """
    poll_interval = interval if interval is not None else config.delay_between_polling
    start_time = time()

    while True:
        response = reports_api.get_report_status(
            connection=connection,
            report_id=report_id,
            instance_id=instance_id,
            project_id=project_id,
        )

        if not response.ok:
            response.raise_for_status()

        if response.status_code != 202:
            # HTTP 200: result ready (in-body status 1) or prompts pending (2).
            return response

        _raise_if_timed_out(start_time, timeout, instance_id)
        sleep(poll_interval)


def _raise_if_timed_out(
    start_time: float, timeout: int | float | None, instance_id: str
) -> None:
    """Raise `TimeoutError` if the total elapsed wait has exceeded `timeout`."""
    if timeout is not None and (time() - start_time) >= timeout:
        raise TimeoutError(
            f"Timed out after {timeout}s waiting for report instance "
            f"'{instance_id}' to finish executing."
        )
