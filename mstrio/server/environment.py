import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

from pandas import DataFrame

from mstrio import config
from mstrio.api import administration as admin_api
from mstrio.api import change_journal as change_journal_api
from mstrio.api import monitors as monitors_api
from mstrio.helpers import IServerError
from mstrio.server.change_journal import _format_timestamp_for_api_purge
from mstrio.server.fence import Fence
from mstrio.server.fence import list_fences as _list_fences
from mstrio.server.project import Project, compare_project_settings
from mstrio.server.server import ServerSettings
from mstrio.server.storage import StorageService, StorageType
from mstrio.utils import helper
from mstrio.utils.enum_helper import AutoUpperName, get_enum_val
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import pa_statistics as pa_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


class PAStatisticsEnvLevel:
    """Class for handling PA Statistics operations at the Environment level.

    Note:
        It is not intended to be used directly.
        Use `Environment.pa_statistics` instead.
    """

    @dataclass
    class RepositoryInfo(helper.Dictable):
        repository_id: str
        pa_project_id: str

    @dataclass
    class TelemetryConfig(helper.Dictable):
        # basic
        basic_stats: bool | None = None
        client_telemetry: bool | None = None
        # advanced, also available from later release
        detailed_rep_jobs: bool | None = None
        detailed_doc_jobs: bool | None = None
        job_sql: bool | None = None
        columns_tables: bool | None = None
        mobile_clients: bool | None = None
        mobile_manipulation: bool | None = None
        mobile_client_location: bool | None = None

    @dataclass
    class TelemetryConnections(helper.Dictable):
        class Protocol(AutoUpperName):
            PLAINTEXT = auto()
            SASL_PLAINTEXT = auto()
            SASL_SSL = auto()
            SSL = auto()

        _FROM_DICT_MAP = {"protocol": Protocol}

        servers: list[str]
        protocol: str | Protocol = Protocol.PLAINTEXT

    #
    def __init__(self, parent: 'Environment'):
        self._parent = parent

    def get_repository_info(self) -> RepositoryInfo:
        """Retrieves repository information from the I-Server.

        Returns:
            RepositoryInfo: An object containing repository ID and
                PA Project ID.
        """

        return self.RepositoryInfo.from_dict(
            pa_processors.get_repository_info(self._connection)
        )

    def update_repository_info(self, new_info: RepositoryInfo | dict[str, str]) -> None:
        """Updates the repository information on the I-Server.

        Args:
            new_info (RepositoryInfo | dict): New repository information. Both
                `repository_id` and `pa_project_id` must be provided, either as
                a `RepositoryInfo` object or as a dictionary with keys
                `repository_id` and `pa_project_id`.
        """

        if isinstance(new_info, dict):
            new_info = self.RepositoryInfo.from_dict(new_info)

        result = pa_processors.update_repository_info(
            self._connection,
            repository_id=new_info.repository_id,
            pa_project_id=new_info.pa_project_id,
        )

        if config.verbose:
            if result:
                logger.info("Repository information updated successfully.")
            else:
                logger.warning("Failed to update repository information.")

    def get_telemetry_basic_configurations(self) -> dict[str, TelemetryConfig]:
        """Retrieves the telemetry basic configurations for all projects from
        the I-Server.

        Returns:
            dict[str, TelemetryConfig]: A dictionary containing telemetry
                configuration details for each project.
        """

        with (
            config.temp_verbose_disable(),
            self._connection.temporary_project_change(None),
        ):
            data = pa_processors.get_basic_telemetry_configuration(self._connection)

        for key, value in data.items():
            data[key] = self.TelemetryConfig.from_dict(value)

        return data

    def enable_basic_telemetry_for_all_projects(self) -> None:
        """Enables client telemetry and basic statistics for all projects on
        the environment.
        """

        result = pa_processors.update_telemetry_basic_configuration_for_all_projects(
            self._connection, to_enable=True
        )

        if config.verbose:
            if result:
                logger.info("Telemetry enabled for all projects successfully.")
            else:
                logger.warning("Failed to enable telemetry for all projects.")

    def disable_basic_telemetry_for_all_projects(self) -> None:
        """Disables client telemetry and basic statistics for all projects on
        the environment.
        """

        result = pa_processors.update_telemetry_basic_configuration_for_all_projects(
            self._connection, to_enable=False
        )

        if config.verbose:
            if result:
                logger.info("Telemetry disabled for all projects successfully.")
            else:
                logger.warning("Failed to disable telemetry for all projects.")

    def get_telemetry_connections_info(self) -> TelemetryConnections:
        """Retrieves the telemetry connections information from the I-Server.

        Returns:
            TelemetryConnections: An object containing telemetry connections
                information.
        """

        return self.TelemetryConnections.from_dict(
            pa_processors.get_telemetry_connections_info(self._connection)
        )

    def update_telemetry_connections_info(
        self, new_data: TelemetryConnections | dict
    ) -> None:
        """Updates the telemetry connections information on the I-Server.

        Args:
            new_data (TelemetryConnections | dict): New telemetry connections
                information. Must contain `servers` (list of server addresses)
                and `protocol` (connection protocol, either as a string or as a
                `Protocol` enum value. `protocol` is optional and defaults to
                `Protocol.PLAINTEXT`).

        Example:
            ```
            # Valid "servers" data -> <host:port>
            servers = ["host.com:9092"]
            ```
        """

        if isinstance(new_data, dict):
            new_data = self.TelemetryConnections.from_dict(new_data)

        result = pa_processors.update_telemetry_connections_info(
            self._connection,
            servers=new_data.servers,
            protocol=get_enum_val(
                new_data.protocol, self.TelemetryConnections.Protocol
            ),
        )

        if config.verbose:
            if result:
                logger.info("Telemetry connections information updated successfully.")
            else:
                logger.warning("Failed to update telemetry connections information.")

    def get_telemetry_connections_validation_info(
        self, connections_data: TelemetryConnections | dict | None = None
    ) -> dict[str, dict]:
        """Retrieves the telemetry connections validation information from
        the I-Server.

        Args:
            connections_data (TelemetryConnections | dict, optional): The
                telemetry connections information to validate. If not provided,
                the current telemetry connections information will be fetched
                and validated. Must contain `servers` (list of server addresses)
                and `protocol` (connection protocol, either as a string or as a
                `Protocol` enum value).

        Example:
            ```
            # Valid "servers" data -> <host:port>
            servers = ["host.com:9092"]
            ```

        Returns:
            dict[str, dict]: A dictionary containing validation results for the
                telemetry connections information. It contains server as key and
                validation result as value.
        """

        if connections_data is None:
            connections_data = self.get_telemetry_connections_info()

        if isinstance(connections_data, dict):
            connections_data = self.TelemetryConnections.from_dict(connections_data)

        return pa_processors.validate_telemetry_connections(
            self._connection,
            servers=connections_data.servers,
            protocol=get_enum_val(
                connections_data.protocol, self.TelemetryConnections.Protocol
            ),
        )

    def validate_telemetry_connections(
        self, connections_data: TelemetryConnections | dict | None = None
    ) -> dict[str, bool]:
        """Tests telemetry connections by sending the provided configuration
        to the server and checking connectivity.

        Args:
            connections_data (TelemetryConnections | dict, optional): The
                telemetry connections information to validate. If not provided,
                the current telemetry connections information will be fetched
                and validated. Must contain `servers` (list of server addresses)
                and `protocol` (connection protocol, either as a string or as a
                `Protocol` enum value).

        Example:
            ```
            # Valid "servers" data -> <host:port>
            servers = ["host.com:9092"]
            ```

        Returns:
            dict[str, bool]: A dictionary containing server as key and a boolean
                indicating whether the connection was successful as value.
        """

        validation_info = self.get_telemetry_connections_validation_info(
            connections_data
        )

        return {
            server: info.get('isConnectable', False)
            for server, info in validation_info.items()
        }

    @property
    def _connection(self) -> 'Connection':
        return self._parent.connection


class LDAPBatchImport:
    """Class for handling LDAP batch import operations.

    This class is used to perform batch import operations on LDAP
    directories.

    Note:
        It is not intended to be used directly.
        Use `Environment.ldap_batch_import` instead.
    """

    class ImportStatus(Enum):
        NO_IMPORT = "No import"
        IN_PROGRESS = "In progress"
        FINISHED = "Finished"
        CANCELED = "Canceled"
        ERROR = "Error"
        UNKNOWN = "Unknown"  # local, not REST

    def __init__(self, parent: 'Environment'):
        """Initialize LDAPBatchImport object.

        Args:
            parent: Environment object to which this import belongs.
        """
        self._parent = parent
        self._cached_status = self.ImportStatus.UNKNOWN
        self._status_data: dict | None = None

    def start(self) -> bool:
        """Start the LDAP batch import operation.

        Returns:
            bool: True if the import operation was started successfully,
                False otherwise.
        """
        res = admin_api.do_ldap_batch_import(self._connection)
        if not res.ok:
            self._cached_status = self.ImportStatus.ERROR
        else:
            self._cached_status = self.ImportStatus.IN_PROGRESS

        return res.ok

    def check_status(self) -> 'ImportStatus':
        """Check the status of the LDAP batch import operation.

        Returns:
            ImportStatus: The current status of the import operation.
        """
        res = admin_api.get_ldap_batch_import_status(self._connection)
        if not res.ok:
            self._cached_status = self.ImportStatus.UNKNOWN
        else:
            self._status_data = res.json()
            try:
                self._cached_status = self.ImportStatus(
                    stat := self._status_data.get('statusDescription')
                )
            except (ValueError, KeyError):
                logger.warning(
                    "Unexpected status of LDAP batch import received from server: "
                    f"{stat}."
                )
                self._cached_status = self.ImportStatus.UNKNOWN

        return self._cached_status

    def stop(self) -> bool:
        """Stop the LDAP batch import operation.

        Returns:
            bool: True if the import operation was stopped successfully,
        """
        res = admin_api.stop_ldap_batch_import(self._connection)
        if not res.ok:
            self._cached_status = self.ImportStatus.UNKNOWN
        elif self._cached_status != self.ImportStatus.FINISHED:
            self._cached_status = self.ImportStatus.CANCELED
        # if finished already, do not override

        return res.ok

    def get_status_data(self) -> dict:
        """Get the status data of the LDAP batch import operation.

        Returns:
            dict: The status data of the import operation.
        """
        self.check_status()
        return self._status_data

    @property
    def _connection(self) -> 'Connection':
        """Return the connection object taken from environment."""
        return self._parent.connection

    @property
    def status(self) -> 'ImportStatus':
        """Get the current status of the LDAP batch import operation.

        This value is cached. If you want to check the current server status,
        use `check_status()` method.

        Returns:
            ImportStatus: The current status of the import operation.
        """
        if not self._cached_status or self._cached_status == self.ImportStatus.UNKNOWN:
            self.check_status()

        return self._cached_status


@class_version_handler('11.3.0000')
class Environment:
    """Browse and manage Projects on the environment. List loaded
    projects, nodes (servers) and compare project settings on the
    environment. Browse and modify I-Server settings.

    Attributes:
        connection: A Strategy One connection object.
        server_settings: Intelligence Server settings object.
        nodes: List of I-Server nodes and their properties.
        node_names: List of I-Server node names.
    """

    _ldap_batch_import_engine: LDAPBatchImport | None = None
    _pa_stats_engine: PAStatisticsEnvLevel | None = None

    def __init__(self, connection: 'Connection'):
        """Initialize Environment object.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`.
        """
        self.connection = connection
        self._nodes = None
        self._storage_service: StorageService | None = None
        self._ldap_batch_import_engine = LDAPBatchImport(self)
        self._pa_stats_engine = PAStatisticsEnvLevel(self)

    @property
    def server_settings(self) -> ServerSettings:
        """`ServerSettings` object storing I-Server settings.

        Settings can be listed by using `list_properties()` method.
        Settings can be modified directly by settings the values in the
        object.
        """
        if not hasattr(self, "_server_settings"):
            self._server_settings = ServerSettings(self.connection)
        return self._server_settings

    @server_settings.setter
    def server_settings(self, server_settings: ServerSettings) -> None:
        self._server_settings = server_settings

    def update_settings(self):
        """Update the current server settings saved in the ServerSettings
        object."""
        self.server_settings.update()

    def fetch_settings(self) -> None:
        """Fetch the current server settings from the environment."""
        self.server_settings.fetch()

    @property
    @method_version_handler('11.3.10')
    def storage_service(self) -> StorageService:
        """`StorageService` object with configuration of the Storage Service.
        object.
        """
        if not self._storage_service:
            response = admin_api.storage_service_get_configs(self.connection).json()
            self._storage_service = StorageService.from_dict(
                response['sharedFileStore'], self.connection
            )

        return self._storage_service

    def update_storage_service(
        self,
        storage_type: StorageType | None = None,
        alias: str | None = None,
        location: str | None = None,
        s3_region: str | None = None,
        aws_access_id: str | None = None,
        aws_secret_key: str | None = None,
        azure_storage_account_name: str | None = None,
        azure_secret_key: str | None = None,
        gcs_service_account_key: str | None = None,
        skip_validation: bool = False,
        validate_only: bool = False,
    ) -> None:
        """Update the storage service configuration on the environment.
        If new values aren't provided for any parameter, the config stored
        in the object will be used.

        Args:
            storage_type (StorageType, optional): Type of storage service.
            alias (str, optional): Alias of the storage configuration,
            location (str, optional): Storage location, e.g.
                bucket name for S3, absolute path of folder for File System
            s3_region (str, optional): S3 bucket region
            aws_access_id (str, optional): Access ID for AWS S3
            aws_secret_key (str, optional): Access key for AWS S3
            azure_storage_account_name (str, optional): Account name for Azure
            azure_secret_key (str, optional): Access key for Azure

            skip_validation: Whether to skip validation of the storage service
                configuration prior to updating.
            validate_only: If True, validate the configuration without updating.
        """
        validation_failed_msg = (
            "The storage service configuration failed validation. "
            "If this configuration is accepted by the I-Server, "
            "it will be applied, but the existing packages "
            "in the previous location will not be available."
        )
        if all(
            arg is None
            for arg in [
                storage_type,
                alias,
                location,
                s3_region,
                aws_access_id,
                aws_secret_key,
                azure_storage_account_name,
                azure_secret_key,
                gcs_service_account_key,
            ]
        ):
            config_delta = self.storage_service.to_dict()
        else:
            config_delta = {
                'type': storage_type.value if storage_type else None,
                'alias': alias,
                'location': location,
                's3Region': s3_region,
                'awsAccessId': aws_access_id,
                'awsSecretKey': aws_secret_key,
                'azureStorageAccountName': azure_storage_account_name,
                'azureSecretKey': azure_secret_key,
                'gcsServiceAccountKey': gcs_service_account_key,
            }
            config_delta = {k: v for k, v in config_delta.items() if v is not None}

        same_type = (
            'type' not in config_delta
            or config_delta['type'] == self.storage_service.type
        )
        old_config_dict = self._storage_service.to_dict() if same_type else {}
        new_config_dict = old_config_dict | config_delta
        storage_service_body = {'sharedFileStore': new_config_dict}
        try:
            admin_api.storage_service_validate_configs(
                self.connection, storage_service_body, error_msg=validation_failed_msg
            )
        except IServerError as e:
            self.fetch_storage_service()
            if e.http_code != 400 or not skip_validation:
                raise e

        if not validate_only:
            admin_api.storage_service_update_configs(
                self.connection, storage_service_body
            )

        self.fetch_storage_service()

    def fetch_storage_service(self) -> None:
        """Fetch the current configuration for Storage Service
        from the environment.
        """
        response = admin_api.storage_service_get_configs(self.connection).json()
        self._storage_service = StorageService.from_dict(
            response['sharedFileStore'], self.connection
        )

    def create_project(
        self,
        name: str,
        description: str | None = None,
        force: bool = False,
        async_request: bool = False,
    ) -> 'Project | None':
        """Create a new project on the environment.

        Args:
            name (str): Name of the new project.
            description (str, optional): Description of the new project.
            force (bool, optional): Whether to skip confirmation prompt.
                Defaults to False.
            async_request (bool, optional): Whether to create the project
                asynchronously (not wait for it before returning).
                Defaults to False.

        Returns:
            Project: The created Project object (unless prompted to abort or
            create asynchronously).
        """
        return Project._create(self.connection, name, description, force, async_request)

    def list_projects(
        self, to_dictionary: bool = False, limit: int | None = None, **filters
    ) -> list["Project"] | list[dict]:
        """Return list of project objects or project dicts if
        `to_dictionary=True`. Optionally filter the Projects by specifying
        the `filters` keyword arguments.

        Args:
            to_dictionary: If True returns list of project dicts.
            limit: limit the number of elements returned. If `None`, all objects
                are returned.
            **filters: Available filter parameters: ['name', 'id',
                'description', 'date_created', 'date_modified', 'owner'].
        """
        return Project._list_projects(
            connection=self.connection,
            to_dictionary=to_dictionary,
            limit=limit,
            **filters,
        )

    def list_loaded_projects(
        self, to_dictionary: bool = False, **filters
    ) -> list["Project"] | list[dict]:
        """Return list of all loaded project objects or project dicts
        if `to_dictionary=True` that the user has access to. Optionally filter
        the Projects by specifying the `filters` keyword arguments.

        Args:
            to_dictionary: If True, returns list of project dicts
            **filters: Available filter parameters: ['acg', 'id', 'name',
                'status', 'alias', 'description', 'date_created',
                'date_modified', 'owner']
        """
        return Project._list_loaded_projects(
            connection=self.connection,
            to_dictionary=to_dictionary,
            **filters,
        )

    @method_version_handler('11.3.0800')
    def delete_server_object_cache(self) -> None:
        """Delete object cache for all projects on the environment."""
        for project in self.list_loaded_projects():
            project.delete_object_cache()
        if config.verbose:
            logger.info('Server object cache deleted.')

    @method_version_handler('11.3.0800')
    def delete_server_element_cache(self) -> None:
        """Delete element cache for all projects on the environment."""
        for project in self.list_loaded_projects():
            project.delete_element_cache()
        if config.verbose:
            logger.info('Server element cache deleted.')

    def list_nodes(
        self,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        node_name: str | None = None,
    ) -> list[dict]:
        """Return a list of I-Server nodes and their properties. Optionally
        filter by `project` or `node_name`.

        Args:
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            node_name (str, optional): Name of node
        """
        proj_id = get_project_id_from_params_set(
            self.connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )
        response = monitors_api.get_node_info(
            self.connection, proj_id, node_name
        ).json()
        return response['nodes']

    def list_fences(
        self, to_dictionary: bool = False, limit: int | None = None, **filters
    ) -> list['Fence'] | list[dict]:
        """Get list of fences.

        Args:
            to_dictionary (bool, optional): If True returns dicts, by default
                (False) returns objects.
            limit (int, optional): limit the number of elements returned.
                If `None` (default), all objects are returned.
            **filters: Available filter parameters:
                ['name', 'id', 'type', 'rank']

        Returns:
            A list of content group objects or dictionaries representing them.
        """

        return _list_fences(self.connection, to_dictionary, limit, **filters)

    def is_loaded(
        self,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> bool:
        """Check if project is loaded, by passing project ID or name,
        returns True or False.

        Args:
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            bool: True if project is loaded, False otherwise.
        """
        nodes = self.list_nodes(
            project=project, project_id=project_id, project_name=project_name
        )
        loaded = False

        for node in nodes:
            status = node['projects'][0]['status']
            loaded = status == 'loaded'
            if loaded:
                break

        return loaded

    def compare_settings(
        self,
        projects: list[str] | list["Project"] = None,
        show_diff_only: bool = False,
    ) -> DataFrame:
        """Compare project' settings to the first project in the
        provided list.

        Args:
            projects (list of names or project objects, optional): List
                of project objects or names to be compared. First element of
                list is the one to which the rest is compared. If None, all
                projects on the environment will be compared.
            show_diff_only(bool, optional): Whether to display all settings or
                only different from first project in list.

        Returns:
            Dataframe with values of selected project' settings.
        """

        def not_exist_warning(wrong_name):
            helper.exception_handler(
                f"Project '{wrong_name}' does not exist and will be skipped.",
                exception_type=Warning,
            )

        if projects:
            just_objects = [
                project for project in projects if isinstance(project, Project)
            ]
        else:
            just_objects = []
        if len(just_objects) == len(projects):
            return compare_project_settings(projects, show_diff_only)

        all_projects = self.list_projects()
        if isinstance(projects, list):
            if len(projects) < 2:
                helper.exception_handler(
                    "Provide more than one project object or name in list",
                    exception_type=TypeError,
                )

            # extract project names from either project object or strings
            project_names = [
                project.name if isinstance(project, Project) else str(project)
                for project in projects
            ]
            # filter only valid projects
            all_project_names = [project.name for project in all_projects]
            [
                not_exist_warning(a_name)
                for a_name in project_names
                if a_name not in all_project_names
            ]

            projects = list(
                filter(lambda project: project.name in project_names, all_projects)
            )
            projects = sorted(projects, key=lambda x: project_names.index(x.name))

        elif projects is None:
            projects = all_projects
        else:
            helper.exception_handler(
                "The 'projects' parameter needs to be a list of len > 1 or None.",
                exception_type=TypeError,
            )

        return compare_project_settings(projects, show_diff_only)

    def is_cluster(self):
        """Checks if the Environment is a cluster (aka has more than 1 node)."""

        return len(self.nodes) > 1

    @method_version_handler('11.4.0900')
    def purge_all_change_journals(
        self, comment: str | None = None, timestamp: str | datetime | None = None
    ) -> None:
        """Purge change journal entries for all projects on the environment
            including configuration change journal entries.

        Note:
            Only change journal entries older than a week can be purged.

        Args:
            comment (str, optional): Comment for the purge action.
            timestamp (str, datetime, optional): Timestamp for purging entries.
                If string, must be in 'MM/DD/YYYY HH:MM:SS AM/PM' format.
                If datetime object, will be converted to required format.
                Entries before this timestamp will be purged. If not provided,
                all entries will be purged.
        """

        if isinstance(timestamp, datetime):
            timestamp = _format_timestamp_for_api_purge(timestamp)

        res = change_journal_api.purge_change_journal_entries(
            connection=self.connection,
            timestamp=timestamp,
            comment=comment,
            all_projects=True,
        )

        if config.verbose and res.ok:
            logger.info(
                "Request to purge change journal entries for all projects on "
                "this environment was successfully sent."
            )

    @method_version_handler('11.4.0900')
    def purge_configuration_change_journals(
        self, comment: str | None = None, timestamp: str | datetime | None = None
    ) -> None:
        """Purge configuration change journal entries.

        Note:
            Only change journal entries older than a week can be purged.

        Args:
            comment (str, optional): Comment for the purge action.
            timestamp (str, datetime, optional): Timestamp for purging entries.
                If string, must be in 'MM/DD/YYYY HH:MM:SS AM/PM' format.
                If datetime object, will be converted to required format.
                Entries before this timestamp will be purged. If not provided,
                all entries will be purged.
        """

        if isinstance(timestamp, datetime):
            timestamp = _format_timestamp_for_api_purge(timestamp)

        res = change_journal_api.purge_change_journal_entries(
            connection=self.connection,
            timestamp=timestamp,
            comment=comment,
            all_projects=False,
        )

        if config.verbose and res.ok:
            logger.info(
                "Request to purge configuration change journal entries "
                "was successfully sent."
            )

    @property
    def nodes(self) -> list[dict]:
        if not self._nodes:
            self._nodes = self.list_nodes()

        return self._nodes

    @property
    def node_names(self) -> list[str]:
        return [node['name'] for node in self.nodes]

    @property
    def ldap_batch_import(self) -> LDAPBatchImport:
        """Engine handling LDAP Batch Import for this Environment."""

        if not self._ldap_batch_import_engine:
            self._ldap_batch_import_engine = LDAPBatchImport(self)

        return self._ldap_batch_import_engine

    @property
    def pa_statistics(self) -> PAStatisticsEnvLevel:
        """Engine handling PA Statistics operations for this Environment."""

        if not self._pa_stats_engine:
            self._pa_stats_engine = PAStatisticsEnvLevel(self)

        return self._pa_stats_engine
