from typing import TYPE_CHECKING

from mstrio.api import incremental_refresh_reports as irr_api

if TYPE_CHECKING:
    from mstrio.connection import Connection


def execute_incremental_refresh_report(
    connection: 'Connection',
    id: str,
    project_id: str,
    fields: str | None = None,
    preview_only: bool = False,
):
    """Execute an Incremental Refresh Report.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (str): Incremental Refresh Report's ID
        project_id (str): ID of a project
        fields (str, optional): A whitelist of top-level fields separated
            by commas. Allows the client to selectively retrieve fields
            in the response.
        preview_only (bool, optional): If True, then the report will be executed
            only to preview data and not update the underlying report's dataset.
            Default is False.

    Returns:
        dict: Dictionary containing job and instance data.
    """

    # The execution_stage parameter, when set to "resolve_prompts", does not
    # update the underlying report's dataset. This behavior is independent of
    # whether the report has prompts or not.
    # Conversely, setting execution_stage to "execute_data" will update the
    # dataset, and any outstanding prompts can be resolved in the instance.

    return irr_api.execute_incremental_refresh_report(
        connection,
        id=id,
        project_id=project_id,
        fields=fields,
        execution_stage="resolve_prompts" if preview_only else "execute_data",
    ).json()
