import logging

from pandas import DataFrame

from mstrio import config
from mstrio.api import administration as admin_api
from mstrio.api import monitors as monitors_api
from mstrio.helpers import IServerError
from mstrio.server.project import Project, compare_project_settings
from mstrio.server.server import ServerSettings
from mstrio.server.storage import StorageService, StorageType
from mstrio.utils import helper
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@class_version_handler('11.3.0000')
class Environment:
    """Browse and manage Projects on the environment. List loaded
    projects, nodes (servers) and compare project settings on the
    environment. Browse and modify I-Server settings.

    Attributes:
        connection: A MicroStrategy connection object.
        server_settings: Intelligence Server settings object.
        nodes: List of I-Server nodes and their properties.
        node_names: List of I-Server node names.
    """

    def __init__(self, connection):
        """Initialize Environment object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
        """
        self.connection = connection
        self._nodes = None
        self._storage_service: StorageService | None = None

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
        self, name: str, description: str | None = None, force: bool = False
    ) -> 'Project | None':
        """Create a new project on the environment.

        Args:
            name: Name of Project.
            description: Description of Application.
            force: If `True`, overrides the prompt.
        """
        return Project._create(self.connection, name, description, force)

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
        node_name: str | None = None,
    ) -> list[dict]:
        """Return a list of I-Server nodes and their properties. Optionally
        filter by `project` or `node_name`.

        Args:
            project: ID of project or Project object
            node_name: Name of node
        """
        project_id = project.id if isinstance(project, Project) else project
        response = monitors_api.get_node_info(
            self.connection, project_id, node_name
        ).json()
        return response['nodes']

    def is_loaded(
        self, project_id: str | None = None, project_name: str | None = None
    ) -> bool:
        """Check if project is loaded, by passing project ID or name,
        returns True or False.

        Args:
            project_id: Project ID
            project_name: Project name
        """
        if project_id is None and project_name is None:
            helper.exception_handler(
                "Please specify either 'project_name' or 'project_id' argument."
            )
        if project_id is None:
            project_list = Project._list_project_ids(self.connection, name=project_name)
            if project_list:
                project_id = project_list[0]
            else:
                msg = f"There is no project with the given name: '{project_name}'"
                raise ValueError(msg)

        nodes = self.list_nodes(project=project_id)
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
        return len(self.nodes) > 1

    @property
    def nodes(self):
        if not self._nodes:
            self._nodes = self.list_nodes()

        return self._nodes

    @property
    def node_names(self):
        return [node['name'] for node in self.nodes]
