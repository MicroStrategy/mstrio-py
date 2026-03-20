import json
from typing import TYPE_CHECKING

from mstrio.api import administration as admin_api
from mstrio.api import configurations as config_api
from mstrio.helpers import NotSupportedError, int_dict_to_bool_dict
from mstrio.utils.helper import delete_none_values, snake_to_camel

if TYPE_CHECKING:
    from mstrio.connection import Connection


def _telemetry_conns_to_dict(data: dict[str, str]) -> dict:
    """Converts raw Telemetry Connections data from REST API to
    readable dictionary.
    """

    if data.get("kafkaProperties.bootstrap.servers") != data.get(
        "iserver.bootstrap.servers"
    ):
        raise NotSupportedError(
            "Found unrecognized Telemetry Configuration where data for I-Server "
            "servers and Kafka Properties servers do not match."
        )

    return {
        'servers': data.get("kafkaProperties.bootstrap.servers", "").split(","),
        'protocol': data.get("kafkaProperties.security.protocol"),
    }


def _data_to_telemetry_conns(servers: list[str], protocol: str) -> dict[str, str]:
    """Converts readable Telemetry Connections dictionary to format expected
    by REST API.
    """

    servers_str = ",".join(servers)

    return {
        "kafkaProperties.bootstrap.servers": servers_str,
        "kafkaProperties.security.protocol": protocol,
        "iserver.bootstrap.servers": servers_str,
    }


def get_repository_info(connection: 'Connection') -> dict[str, str]:
    """Retrieves repository information from the I-Server.

    Fetches the repository ID and Platform Analytics Project ID from the
    connected I-Server's repository configuration.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.

    Returns:
        Dictionary containing:
            - repository_id (str): Unique identifier for the repository.
            - pa_project_id (str): Platform Analytics Project ID associated
                with the repository.
    """

    ret: dict = config_api.get_repository_info(connection).json()

    return {
        "repository_id": ret.get("id"),
        "pa_project_id": ret.get("platformAnalyticsProjectId"),
    }


def update_repository_info(
    connection: 'Connection',
    repository_id: str,
    pa_project_id: str,
) -> bool:
    """Updates the repository information on the I-Server.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        repository_id (str): The unique identifier of the repository.
        pa_project_id (str): The Platform Analytics project ID to associate
            with the repository.

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    body = {
        "id": repository_id,
        "platformAnalyticsProjectId": pa_project_id,
        "platformAnalyticsEnvInfo": json.dumps({"projectID": pa_project_id}),
    }

    return config_api.update_repository_info(connection, body).ok


def get_basic_telemetry_configuration(
    connection: 'Connection',
) -> dict[str, dict[str, bool]]:
    """Retrieves telemetry configuration.

    Note:
        If a project is selected in the connection, only its telemetry
        configuration is retrieved. Otherwise telemetry configurations for
        all projects are retrieved.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.

    Returns:
        dict[str, dict[str, bool]]: A dictionary where keys are project IDs
            and values are dictionaries representing telemetry settings with
            boolean values.
    """

    ret: dict[str, dict] = admin_api.OLD_get_telemetry_configuration(
        connection=connection,
        project_id=connection.project_id,
        is_live=True,
    ).json()

    for key, proj_data in ret.items():
        ret[key] = int_dict_to_bool_dict(proj_data)

    return ret


def get_telemetry_configuration_for_project(
    connection: 'Connection',
    project_id: str | None = None,
) -> dict[str, bool]:
    """Retrieves telemetry configuration for a specific project.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str, optional): The ID of the project to retrieve the
            telemetry configuration for. If None, the currently selected project
            in the connection will be used.

    Returns:
        dict[str, bool]: A dictionary representing the telemetry settings
            for the specified project with boolean values.
    """

    if not project_id:
        connection._validate_project_selected()
        project_id = connection.project_id

    return admin_api.get_telemetry_configuration_for_project(
        connection, project_id=project_id
    ).json()


def update_telemetry_basic_configuration_for_all_projects(
    connection: 'Connection',
    to_enable: bool,
) -> bool:
    """Updates telemetry configuration.

    Note:
        It applies only to "basic stats" and "client telemetry" properties.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        to_enable (bool): Whether to enable (True) or disable (False)
            client telemetry for all projects.

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    return admin_api.update_telemetry_basic_configuration(
        connection=connection,
        body={"enableClientTelemetryForAll": int(to_enable)},
    ).ok


def update_telemetry_configuration_for_project(
    connection: 'Connection',
    project_id: str | None = None,
    **properties: bool,
) -> bool:
    """Updates telemetry configuration for a specific project.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str, optional): The ID of the project to update the
            telemetry configuration for. If None, the currently selected project
            in the connection will be used.
        **properties: Telemetry configuration properties to update with
            boolean values. Possible keys can be found in
            `PAStatisticsEnvLevel.TelemetryConfig` dataclass.

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    from mstrio.server.environment import PAStatisticsEnvLevel

    final_data = PAStatisticsEnvLevel.TelemetryConfig.from_dict(
        snake_to_camel(properties)
    ).to_dict()
    final_data = delete_none_values(final_data, recursion=True)

    if "jobSql" in final_data:
        final_data["jobSQL"] = final_data["jobSql"]
        del final_data["jobSql"]

    if not final_data:
        return True

    if not project_id:
        connection._validate_project_selected()
        project_id = connection.project_id

    return admin_api.update_telemetry_configuration_for_project(
        connection, project_id=project_id, body=final_data
    ).ok


def get_telemetry_connections_info(
    connection: 'Connection',
) -> dict[str, list[str] | str]:
    """Retrieves telemetry connections information.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.

    Returns:
        dict[str, list[str] | str]: A dictionary containing:
            - servers (list[str]): List of Kafka bootstrap servers.
            - protocol (str): Kafka security protocol.
    """

    ret: dict[str, str] = admin_api.get_telemetry_connections_info(connection).json()

    return _telemetry_conns_to_dict(ret)


def update_telemetry_connections_info(
    connection: 'Connection',
    servers: list[str],
    protocol: str = 'PLAINTEXT',
) -> bool:
    """Updates telemetry connections information.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        servers (list[str]): List of Kafka bootstrap servers.
        protocol (str, optional): Kafka security protocol.
            Default is 'PLAINTEXT'.

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    return admin_api.update_telemetry_connections_info(
        connection=connection,
        body=_data_to_telemetry_conns(
            servers=servers,
            protocol=protocol,
        ),
    ).ok


def validate_telemetry_connections(
    connection: 'Connection',
    servers: list[str],
    protocol: str = 'PLAINTEXT',
) -> dict[str, dict]:
    """Tests telemetry connections by sending the provided configuration to the
    server and checking connectivity.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        servers (list[str]): List of Kafka bootstrap servers.
        protocol (str, optional): Kafka security protocol.
            Default is 'PLAINTEXT'. Available entries: ['PLAINTEXT',
            'SASL_PLAINTEXT', 'SASL_SSL', 'SSL']

    Returns:
        dict[str, dict]: A dictionary where keys are server addresses and
            values are dictionaries containing the test results for each server.

    Examples:
    ```
    {'addr1:9092': {'clusteredNodes': [{'id': 0,
                                        'host': '<host>',
                                        'port': 9092}],
                    'clusterId': '11111111-1111-1111-1111-111111111111',
                    'isConnectable': True,
                    'isClustered': False},
     'addr2:6969': {'clusteredNodes': [],
                    'exceptions': "Error occurred. Please check logs on server
                        for more details. No resolvable bootstrap urls given
                        in bootstrap.servers",
                    'isConnectable': False,
                    'isClustered': False}}
    ```
    """

    body = _data_to_telemetry_conns(
        servers=servers,
        protocol=protocol,
    )

    data = admin_api.validate_telemetry_connections(connection, body).json()

    if "kafkaConnectionStatusMap" not in data:
        raise ValueError(
            "Telemetry Connections Validation Response has unexpected structure."
        )

    return data["kafkaConnectionStatusMap"]
