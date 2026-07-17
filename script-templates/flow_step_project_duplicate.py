"""
Flow Step Template: Project Duplicate
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents Projects Duplication action.

The Script will return duplicated project ID.

The workflow currently assumes:
- That the source connection will be established via `get_connection`
- That the target connection will be established via URL / Username / Password,
    all provided via Variables. If not provided, same-env duplication will
    be performed
- Actions set for `DuplicationConfig` or `CrossDuplicationConfig` are hardcoded
    in the code below to their default values and can be edited in the
    code below.
- For cross-environment duplication, storage service has been configured for
    both source and target environments
"""

from mstrio.connection import get_connection, Connection
from mstrio.server import (
    DuplicationConfig,
    Project,
    CrossDuplicationConfig,
    ProjectDuplication,
)

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
source_conn = get_connection(connectionData)

PROJECT_NAME = $project_name
DUP_PROJECT_NAME = $dup_project_name

project = Project(source_conn, name=PROJECT_NAME)

# If target URL is provided, we assume inter-environment project duplication.
# Otherwise, the duplication will be within the Environment from source connection
if $target_base_url:
    target_conn = Connection(
        base_url=$target_base_url,
        username=$target_username,
        password=$target_password,
    )
else:
    target_conn = None


if not target_conn:  # same-env duplication
    # Both required and optional properties below are set to their defaults.
    # Feel free to change them to your needs. See `DuplicationConfig` in
    # mstrio-py documentation or source code for more details.
    duplication_config = DuplicationConfig()
    duplication = project.duplicate(
        target_name=DUP_PROJECT_NAME,
        duplication_config=duplication_config,
    )

    duplication.wait_for_stable_status()

    if "FAILED" in duplication.status.value:
        raise RuntimeError(
            f"Project duplication failed with status {duplication.status}"
        )

    result_project = Project(source_conn, name=DUP_PROJECT_NAME)

else:  # cross-env duplication
    # Both required and optional properties below are set to their defaults.
    # Feel free to change them to your needs. See `CrossDuplicationConfig` in
    # mstrio-py documentation or source code for more details.
    duplication_config = CrossDuplicationConfig()
    duplication = project.duplicate_to_other_environment(
        target_name=DUP_PROJECT_NAME,
        target_env=target_conn,
        cross_duplication_config=duplication_config,
        sync_with_target_env=True,
        keep_id=True,
    )

    duplication.wait_for_stable_status()

    if "FAILED" in duplication.status.value:
        raise RuntimeError(
            f"Project duplication failed on source env with "
            f"status {duplication.status}."
        )

    target_duplication = ProjectDuplication(target_conn, id=duplication.id)

    if target_duplication:
        target_duplication.wait_for_stable_status()

    if not target_duplication or "FAILED" in target_duplication.status.value:
        raise RuntimeError(
            f"Project duplication failed on target env with "
            f"status {target_duplication.status if target_duplication else "UNKNOWN"}."
        )

    result_project = Project(target_conn, name=DUP_PROJECT_NAME)


print(
    f"Project {project} have been duplicated successfully into "
    f"new project {DUP_PROJECT_NAME}"
)

def get_results():
    return result_project.id
