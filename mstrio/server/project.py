import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING

from pandas import DataFrame, Series
from tqdm import tqdm

from mstrio import config
from mstrio.api import datasources as datasources_api
from mstrio.api import monitors, objects, projects
from mstrio.connection import Connection
from mstrio.helpers import IServerError, VersionException
from mstrio.server.project_languages import (
    DataLanguageSettings,
    MetadataLanguageSettings,
)
from mstrio.utils import helper, time_helper
from mstrio.utils.entity import DeleteMixin, Entity, EntityBase, ObjectTypes
from mstrio.utils.enum_helper import AutoName, AutoUpperName, get_enum_val
from mstrio.utils.response_processors import datasources as datasources_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.response_processors import projects as projects_processors
from mstrio.utils.settings.base_settings import BaseSettings
from mstrio.utils.time_helper import DatetimeFormats
from mstrio.utils.version_helper import (
    is_server_min_version,
    method_version_handler,
)
from mstrio.utils.vldb_mixin import ModelVldbMixin
from mstrio.utils.wip import wip

if TYPE_CHECKING:
    from mstrio.datasources import DatasourceInstance
    from mstrio.server.environment import Environment
    from mstrio.server.node import Node
    from mstrio.users_and_groups import User

logger = logging.getLogger(__name__)

SYSTEM_OBJECTS_VERSION_PROPERTY_SET_ID = "C02146A211D46D60C0001786395B684F"
AE_VERSION_PROPERTY_INDEX = 8


class ProjectStatus(IntEnum):
    ACTIVE = 0
    ERRORSTATE = -3
    EXECIDLE = 1
    FULLIDLE = 7
    OFFLINE = -1
    OFFLINEPENDING = -2
    ONLINEPENDING = -4
    REQUESTIDLE = 2
    WHEXECIDLE = 4


class IdleMode(AutoName):
    """Used to specify the exact behaviour of `idle` request.

    `REQUEST` (Request Idle): all executing and queued jobs finish executing
        and any newly submitted jobs are rejected.
    `EXECUTION` (Execution Idle for All Jobs): all executing, queued, and
        newly submitted jobs are placed in the queue, to be executed when
        the project resumes.
    `WAREHOUSEEXEC` (Execution Idle for Warehouse jobs): all executing,
        queued, and newly submitted jobs that require SQL to be submitted
        to the data warehouse are placed in the queue, to be executed when
        the project resumes. Any jobs that do not require SQL to be
        executed against the data warehouse are executed.
    `FULL` (Request Idle and Execution Idle for All jobs): all executing and
        queued jobs are canceled, and any newly submitted jobs are rejected.
    `PARTIAL` (Request Idle and Execution Idle for Warehouse jobs): all
        executing and queued jobs that do not submit SQL against the data
        warehouse are canceled, and any newly submitted jobs are rejected.
        Any currently executing and queued jobs that do not require SQL to
        be executed against the data warehouse are executed.
    """

    REQUEST = "request_idle"
    EXECUTION = "exec_idle"
    WAREHOUSEEXEC = "wh_exec_idle"
    FULL = "partial_idle"
    PARTIAL = "full_idle"
    UNLOADED = auto()
    LOADED = auto()
    UNLOADED_PENDING = auto()
    LOADED_PENDING = auto()
    PENDING = auto()
    UNKNOWN = auto()


class LockType(AutoName):
    """Enum representing the type of lock applied to a project.

    `TEMPORAL_INDIVIDUAL`: A temporary lock that restricts all other sessions
        except the current user's session from editing the project.
        This lock disappears when the user's session expires.
    `TEMPORAL_CONSTITUENT`: A temporary lock that restricts all other sessions
        except the current user's session from editing the project and all
        objects in the project. This lock disappears when the user's session
        expires.
    `PERMANENT_INDIVIDUAL`: A permanent lock that prevents all users from
        editing the project. This lock does not expire and must be removed
        before the project can be edited again.
    `PERMANENT_CONSTITUENT`: A permanent lock that prevents all users from
        editing the project and all objects in the project. This lock does not
        expire and must be removed before the project and its objects can be
        edited again.
    `NOT_LOCKED`: Represents the state where the project is not locked
        and can be edited by users.
    """

    TEMPORAL_INDIVIDUAL = auto()
    TEMPORAL_CONSTITUENT = auto()
    PERMANENT_INDIVIDUAL = auto()
    PERMANENT_CONSTITUENT = auto()
    NOT_LOCKED = auto()


def compare_project_settings(
    projects: list["Project"], show_diff_only: bool = False
) -> DataFrame:
    """Compares settings of project objects.

    Args:
        projects (List[Project]): List of project objects
            to compare.
        show_diff_only (bool, optional): Whether to display all settings
            or only different from first project in list.
    """
    to_be_compared = {}
    df = DataFrame({}, columns=['initial'])

    for project in projects:
        to_be_compared[project.name] = project.settings.to_dataframe().reset_index()
        if df.empty:
            df.columns = ['setting']
            df['setting'] = to_be_compared[project.name]['setting']
        df[project.name] = to_be_compared[project.name]['value']

    if show_diff_only:
        index = Series([True] * len(df['setting']))
        base = projects[0].name
        for project_name in to_be_compared.keys():
            compare = df[base].eq(df[project_name])
            index = compare & index
        df = df[~index]
        if df.empty and config.verbose:
            project_names = list(to_be_compared.keys())
            project_names.remove(base)
            msg = (
                f"There is no difference in settings between project '{base}' and "
                f"remaining projects: '{project_names}'"
            )
            logger.info(msg)
    return df


def list_projects(
    # allows for `conn` to be Env to support `list_projects(env)` syntax
    conn: "Connection | Environment | None" = None,
    env: "Environment | None" = None,
    *args,
    **kwargs,
):
    """Return list of project objects or project dicts if `to_dictionary=True`.
    Optionally filter the Projects by specifying the filters keyword arguments.

    This is a helper method using `Environment.list_projects()` under the hood.
    See `Environment.list_projects()` documentation for more details.

    Either `conn` or `env` must be provided.

    Attributes:
        conn (Connection, optional): A Strategy One connection object.
        env (Environment, optional): Environment object instance.
        ... (optional): Additional parameters to pass to
            `Environment.list_projects()`.
    """
    if conn is None and env is None:
        raise ValueError("Either connection or environment must be provided.")

    from mstrio.server.environment import Environment

    if not env and isinstance(conn, Environment):
        env = conn

    if env:
        return env.list_projects(*args, **kwargs)

    return Project._list_projects(conn, *args, **kwargs)


class Project(Entity, ModelVldbMixin, DeleteMixin):
    """Object representation of Strategy One Project (Project) object.

    Attributes:
        connection: A Strategy One connection object
        settings: Project settings object
        id: Project ID
        name: Project name
        description: Project description
        alias: Project alias
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        nodes: List of nodes on which project is loaded
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd
        version: Version ID
        owner: owner ID and name
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        status: Project
        ancestors: List of ancestor folders
        data_language_settings: Project data language settings
        metadata_language_settings: Project metadata language settings
    """

    @dataclass
    class LockStatus(helper.Dictable):
        """Object representation of Project Lock Status.

        Attributes:
            lock_type: Lock type
            lock_time: Lock time
            comment: Lock comment
            machine_name: Machine name
            owner: User object
        """

        @staticmethod
        def _parse_owner(source, connection):
            """Parses owner from the API response."""
            from mstrio.users_and_groups import User

            return User.from_dict(source, connection)

        _FROM_DICT_MAP = {
            'lock_type': LockType,
            'lock_time': DatetimeFormats.FULLDATETIME,
            'owner': _parse_owner,
        }

        lock_type: LockType
        lock_time: datetime | None = None
        comment: str | None = None
        machine_name: str | None = None
        owner: 'User | None' = None

    _OBJECT_TYPE = ObjectTypes.PROJECT
    _API_GETTERS = {
        **Entity._API_GETTERS,
        ('status', 'alias'): projects.get_project,
        'nodes': monitors.get_node_info,
        (
            'data_language_settings',
            'metadata_language_settings',
        ): projects_processors.get_project_internalization,
        'lock_status': projects_processors.get_project_lock,
    }
    _API_PATCH = {
        **Entity._API_PATCH,
        'alias': (projects.update_project, 'patch'),
        (
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }
    _PATCH_PATH_TYPES = {
        **Entity._PATCH_PATH_TYPES,
        'alias': str,
    }
    _API_DELETE = staticmethod(projects.delete_project)
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'status': ProjectStatus,
        'data_language_settings': DataLanguageSettings.from_dict,
        'metadata_language_settings': MetadataLanguageSettings.from_dict,
        'lock_status': LockStatus.from_dict,
    }
    _STATUS_PATH = "/status"
    _MODEL_VLDB_API = {
        'GET_ADVANCED': projects.get_vldb_settings,
        'PUT_ADVANCED': projects.update_vldb_settings,
        'GET_APPLICABLE': projects.get_applicable_vldb_settings,
    }
    _REST_ATTR_MAP = {
        'data': 'data_language_settings',
        'metadata': 'metadata_language_settings',
    }

    def __init__(
        self,
        connection: Connection,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """Initialize Project object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            name: Project name
            id: Project ID
        """

        # initialize either by ID or Project Name
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.",
                exception_type=ValueError,
            )

        if id is None:
            project_list = Project._list_project_ids(connection, name=name)
            if project_list:
                id = project_list[0]
            else:
                helper.exception_handler(
                    f"There is no project with the given name: '{name}'",
                    exception_type=ValueError,
                )

        try:
            super().__init__(connection=connection, object_id=id, name=name)
        except IServerError as e:
            if not self.is_loaded():
                helper.exception_handler(
                    (
                        "Some projects are either unloaded or idled. Change "
                        "status using the 'load()' or 'resume()' method to use "
                        "all functionality."
                    ),
                    exception_type=UserWarning,
                )
            else:
                raise e

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._status = kwargs.get("status")
        self._alias = kwargs.get("alias")
        self._nodes = kwargs.get("nodes")
        self._data_language_settings = kwargs.get("data_language_settings")
        self._metadata_language_settings = kwargs.get("metadata_language_settings")
        self._lock_status = kwargs.get("lock_status")

    @classmethod
    def _create(
        cls,
        connection: Connection,
        name: str,
        description: str | None = None,
        force: bool = False,
    ) -> 'Project | None':
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to create new project '{name}'? [Y/N]: "
            )

        if force or user_input == 'Y':
            # Create new project
            with tqdm(
                desc=f"Please wait while Project '{name}' is being created.",
                bar_format='{desc}',
                leave=False,
                disable=config.verbose,
            ):
                projects.create_project(
                    connection, {"name": name, "description": description}
                )
                http_status, i_server_status = 500, 'ERR001'
                while http_status == 500 and i_server_status == 'ERR001':
                    time.sleep(1)
                    response = projects.get_project(
                        connection, name, whitelist=[('ERR001', 500)]
                    )
                    http_status = response.status_code
                    data = response.json()
                    i_server_status = data.get('code')
            if config.verbose:
                logger.info(f"Project '{name}' successfully created.")
            return cls.from_dict(data, connection=connection)
        else:
            return None

    @classmethod
    @method_version_handler('11.2.0000')
    def _list_projects(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        limit: int | None = None,
        **filters,
    ) -> list["Project"] | list[dict]:
        msg = "Error getting information for a set of Projects."
        objects = helper.fetch_objects_async(
            connection,
            monitors.get_projects,
            monitors.get_projects_async,
            dict_unpack_value='projects',
            limit=limit,
            chunk_size=1000,
            error_msg=msg,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            projects = [
                cls.from_dict(source=obj, connection=connection) for obj in objects
            ]
            projects_loaded = Project._list_loaded_projects(
                connection, to_dictionary=True
            )
            projects_loaded_ids = [project['id'] for project in projects_loaded]
            unloaded = [
                project for project in projects if project.id not in projects_loaded_ids
            ]

            if unloaded:
                msg = (
                    f"Projects {[project.name for project in unloaded]} are either "
                    f"unloaded or idled. Change status using the 'load()' or 'resume()'"
                    f" method to use all functionality."
                )
                helper.exception_handler(msg, exception_type=UserWarning)
            return projects

    @classmethod
    def _list_project_ids(
        cls, connection: Connection, limit: int | None = None, **filters
    ) -> list[str]:
        project_dicts = Project._list_projects(
            connection=connection,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [project['id'] for project in project_dicts]

    @classmethod
    def _list_loaded_projects(
        cls, connection: Connection, to_dictionary: bool = False, **filters
    ) -> list["Project"] | list[dict]:
        response = projects.get_projects(connection, whitelist=[('ERR014', 403)])
        list_of_dicts = response.json() if response.ok else []
        list_of_dicts = helper.camel_to_snake(list_of_dicts)  # Convert keys
        raw_project = helper.filter_list_of_dicts(list_of_dicts, **filters)

        if to_dictionary:
            # return list of project names
            return raw_project
        else:
            # return list of Project objects
            return [
                cls.from_dict(source=obj, connection=connection) for obj in raw_project
            ]

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        comments: str | None = None,
        owner: 'str | User | None' = None,
        alias: str | None = None,
    ) -> None:
        """Alter project name or/and description.

        Args:
            name (str, optional): new name of the project.
            description (str, optional): new description of the project.
            comments (str, optional): long description of the project.
            owner: (str, User, optional): owner of the project.
            alias (str, optional): new alias of the project.
        """
        from mstrio.users_and_groups import User

        if alias and not is_server_min_version(self.connection, '11.5.0300'):
            msg = (
                "Environments must run IServer version `11.5.0300` or newer. "
                "Please update your environments to alter project alias."
            )
            raise VersionException(msg)
        if isinstance(owner, User):
            owner = owner.id

        properties = helper.filter_params_for_func(
            self.alter, locals(), exclude=['self']
        )

        self._alter_properties(**properties)

    def __change_project_state(
        self, func, on_nodes: str | list[str] | None = None, **mode
    ):
        if isinstance(on_nodes, list):
            for node in on_nodes:
                func(node, **mode)
        elif isinstance(on_nodes, str):
            func(on_nodes, **mode)
        elif on_nodes is None:
            for node in self.nodes:
                func(node.get('name'), **mode)  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list[str], str, NoneType]",
                exception_type=TypeError,
            )

    @method_version_handler('11.2.0000')
    def idle(
        self,
        on_nodes: str | list[str] | None = None,
        mode: IdleMode | str = IdleMode.REQUEST,
    ) -> None:
        """Request to idle a specific cluster node. Idle project with mode
        options.

        Args:
            on_nodes: Name of node, if not passed, project will be idled on
                all of the nodes.
            mode: One of: `IdleMode` values.
        """

        def idle_project(node: str, mode: IdleMode):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": mode.value}
                ]
            }
            response = monitors.update_node_properties(
                self.connection, node, self.id, body
            )
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != mode.value:
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(
                        f"Project '{self.id}' changed status to '{mode}' on node "
                        f"'{node}'."
                    )

        if not isinstance(mode, IdleMode):
            # Previously `mode` was just a string with possible values
            # corresponding to the member names of the current IdleMode enum.
            # This attempts to convert it to avoid breaking backwards compat.
            if mode in IdleMode.__members__.values():
                mode = IdleMode(mode)
            elif mode in IdleMode.__members__:
                mode = IdleMode[mode]
            else:
                helper.exception_handler(
                    "Unsupported mode, please provide a valid `IdleMode` value.",
                    KeyError,
                )

        self.__change_project_state(func=idle_project, on_nodes=on_nodes, mode=mode)

    @method_version_handler('11.2.0000')
    def resume(self, on_nodes: str | list[str] | None = None) -> None:
        """Request to resume the project on the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, project will be resumed
                on all of the nodes.
        """

        def resume_project(node):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": "loaded"}
                ]
            }
            response = monitors.update_node_properties(
                self.connection, node, self.id, body
            )
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'loaded':
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(f"Project '{self.id}' resumed on node '{node}'.")

        self.__change_project_state(func=resume_project, on_nodes=on_nodes)

    @staticmethod
    def _normalize_nodes(
        on_nodes: 'str | list[str] | Node | list[Node] | None',
    ) -> str | list[str] | None:
        from mstrio.server.node import Node

        if isinstance(on_nodes, list):
            return [node.name if isinstance(node, Node) else node for node in on_nodes]
        return on_nodes.name if isinstance(on_nodes, Node) else on_nodes

    @method_version_handler('11.2.0000')
    def load(
        self, on_nodes: 'str | list[str] | Node | list[Node] | None' = None
    ) -> None:
        """Request to load the project onto the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, project will be loaded
                on all of the nodes.
        """
        on_nodes = self._normalize_nodes(on_nodes)

        def load_project(node):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": "loaded"}
                ]
            }
            response = monitors.update_node_properties(
                self.connection, node, self.id, body
            )
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'loaded':
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(f"Project '{self.id}' loaded on node '{node}'.")

        self.__change_project_state(func=load_project, on_nodes=on_nodes)

    @method_version_handler('11.2.0000')
    def unload(
        self, on_nodes: 'str | list[str] | Node | list[Node] | None' = None
    ) -> None:
        """Request to unload the project from the chosen cluster nodes. If
        nodes are not specified, the project will be unloaded on all nodes.
        The unload action cannot be performed until all jobs and connections
        for project are completed. Once these processes have finished,
        pending project will be automatically unloaded.

        Args:
            on_nodes: Name of node, if not passed, project will be unloaded
                on all of the nodes.
        """
        on_nodes = self._normalize_nodes(on_nodes)

        def unload_project(node):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": "unloaded"}
                ]
            }
            response = monitors.update_node_properties(
                self.connection, node, self.id, body, whitelist=[('ERR001', 500)]
            )
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'unloaded':
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(f"Project '{self.id}' unloaded on node '{node}'.")
            if response.status_code == 500 and config.verbose:  # handle whitelisted
                logger.warning(
                    f"Project '{self.id}' already unloaded on node '{node}'."
                )

        self.__change_project_state(func=unload_project, on_nodes=on_nodes)

    @method_version_handler('11.3.0800')
    def delete(self: Entity) -> bool:
        """Delete project.

        Returns:
            True if project was deleted, False otherwise.
        """
        self._DELETE_CONFIRM_MSG = (
            f"Are you sure you want to delete project "
            f"'{self.name}' with ID: {self._id}?\n"
            "All objects will be permanently deleted. This cannot be undone.\n"
            "Please type the project name to confirm: "
        )
        self._DELETE_SUCCESS_MSG = (
            f"Project '{self.name}' has been successfully deleted."
        )
        self._DELETE_PROMPT_ANSWER = self.name

        return super().delete(force=False)

    @method_version_handler('11.3.0000')
    def register(self, on_nodes: str | list | None = None) -> None:
        """Register project on nodes.

        A registered project will load on node (server) startup.

        Args:
            on_nodes: Name of node, if not passed, project will be loaded
                on all available nodes on startup.
        """
        if on_nodes is None:
            value = [node['name'] for node in self.nodes]
        else:
            on_nodes = on_nodes if isinstance(on_nodes, list) else [on_nodes]
            value = list(set(self.load_on_startup) | set(on_nodes))
        self._register(on_nodes=value)

    @method_version_handler('11.3.0000')
    def unregister(self, on_nodes: str | list | None = None) -> None:
        """Unregister project on nodes.

        An unregistered project will not load on node (server) startup.

        Args:
            on_nodes (str or list, optional): Name of node, if not passed,
                project will not be loaded on any nodes on startup.
        """
        if on_nodes is None:
            value = []
        else:
            on_nodes = on_nodes if isinstance(on_nodes, list) else [on_nodes]
            value = list(set(self.load_on_startup) - set(on_nodes))
        self._register(on_nodes=value)

    def update_settings(self) -> None:
        """Update the current project settings on the I-Server."""
        self.settings.update(self.id)

    def enable_caching(self) -> None:
        """Enable caching settings for the current project on the I-Server."""
        self.settings.enable_caching()
        self.update_settings()

    def disable_caching(self) -> None:
        """Disable caching settings for the current project on the I-Server."""
        self.settings.disable_caching()
        self.update_settings()

    @method_version_handler('11.3.0800')
    def delete_object_cache(self) -> None:
        """Delete object cache for the current project on the I-Server."""
        monitors.delete_caches(self.connection, self.id, 'object')
        if config.verbose:
            logger.info(
                f"Object cache was successfully deleted for project '{self.id}'"
            )

    @method_version_handler('11.3.0800')
    def delete_element_cache(self) -> None:
        """Delete element cache for the current project on the I-Server."""
        monitors.delete_caches(self.connection, self.id, 'element')
        if config.verbose:
            logger.info(
                f"Element cache was successfully deleted for project '{self.id}'"
            )

    def fetch_settings(self) -> None:
        """Fetch the current project settings from the I-Server."""
        self.settings.fetch(self.id)

    def list_caching_settings(self) -> dict:
        """
        Fetch current project settings connected with caching from I-Server
        """
        return self.settings.list_caching_properties()

    def is_loaded(self) -> bool:
        """Check if the project is loaded on any node (server)."""
        loaded = False
        self.fetch('nodes')
        if not isinstance(self.nodes, list):
            helper.exception_handler(
                "Could not retrieve current project status.",
                exception_type=ConnectionError,
            )
        for node in self.nodes:
            projects = node.get('projects')
            if projects:
                status = projects[0].get('status')
                loaded = status == 'loaded'
                if loaded:
                    break
        return loaded

    def get_data_engine_versions(self) -> dict:
        """Fetch the currently available data engine versions for project."""

        return projects.get_engine_settings(self.connection, self.id).json()['engine'][
            'versions'
        ]

    def get_current_engine_version(self):
        res = objects.get_property_set(
            self.connection,
            id=self.id,
            obj_type=self._OBJECT_TYPE.value,
            property_set_id=SYSTEM_OBJECTS_VERSION_PROPERTY_SET_ID,
        ).json()
        current_in_list = [
            prop for prop in res if prop['id'] == AE_VERSION_PROPERTY_INDEX
        ]
        current = current_in_list[0]['value'] if current_in_list else None

        return current

    def update_data_engine_version(self, new_version: str) -> None:
        """Update data engine version for project."""

        body = [
            {
                "properties": [{"value": new_version, "id": AE_VERSION_PROPERTY_INDEX}],
                "id": SYSTEM_OBJECTS_VERSION_PROPERTY_SET_ID,
            }
        ]
        objects.update_property_set(
            self.connection, id=self.id, obj_type=self._OBJECT_TYPE.value, body=body
        )

    def _register(self, on_nodes: list) -> None:
        path = f"/projects/{self.id}/nodes"
        body = {"operationList": [{"op": "replace", "path": path, "value": on_nodes}]}
        projects.update_projects_on_startup(self.connection, body)
        if config.verbose:
            if on_nodes:
                logger.info(f'Project will load on startup of: {on_nodes}')
            else:
                logger.warning('Project will not load on startup.')

    @method_version_handler('11.3.0100')
    def add_datasource(
        self, datasources: list['DatasourceInstance | str']
    ) -> list['DatasourceInstance']:
        """Add datasources to the project.

        Args:
            datasources (list["DatasourceInstance", str]): List of datasource
                objects or datasource IDs to be added to the project.

        Returns:
            List of datasource objects for the project.
        """
        from mstrio.datasources import DatasourceInstance, list_datasource_instances

        operation_list = []
        valid_datasource_ids = [
            datasource.id for datasource in list_datasource_instances(self.connection)
        ]
        datasource_ids = [
            datasource.id if isinstance(datasource, DatasourceInstance) else datasource
            for datasource in datasources
        ]

        for datasource_id in datasource_ids:
            if datasource_id not in valid_datasource_ids:
                raise ValueError(f"Datasource with ID {datasource_id} doesn't exist.")

            operation_list.append(
                {
                    'op': 'add',
                    'path': '/id',
                    'value': datasource_id,
                }
            )

        response = datasources_processors.update_project_datasources(
            connection=self.connection,
            id=self.id,
            body={'operationList': operation_list},
        )

        if config.verbose:
            logger.info(
                f"Datasources were successfully added to the project {self.id}."
            )

        return [
            DatasourceInstance.from_dict(datasource, self.connection)
            for datasource in response
        ]

    @method_version_handler('11.3.0100')
    def remove_datasource(self, datasources: list['DatasourceInstance | str']) -> None:
        """Remove datasources from the project.

        Args:
            datasources (list["DatasourceInstance", str]): List of datasource
                objects or datasource IDs to be removed from the project.
        """
        from mstrio.datasources import DatasourceInstance, list_datasource_instances

        operation_list = []
        valid_datasource_ids = [
            datasource.id
            for datasource in list_datasource_instances(
                self.connection, project=self.id
            )
        ]
        datasource_ids = [
            datasource.id if isinstance(datasource, DatasourceInstance) else datasource
            for datasource in datasources
        ]

        for datasource_id in datasource_ids:
            if datasource_id not in valid_datasource_ids:
                raise ValueError(
                    f"Datasource with ID {datasource_id} does not exist in the "
                    f"project {self.id}."
                )

            operation_list.append(
                {
                    'op': 'remove',
                    'path': '/id',
                    'value': datasource_id,
                }
            )

        datasources_api.update_project_datasources(
            connection=self.connection,
            id=self.id,
            body={'operationList': operation_list},
        )

        if config.verbose:
            logger.info(
                f"Datasources were successfully removed from the project {self.id}."
            )

    @method_version_handler('11.3.0600')
    def lock(self, lock_type: str | LockType, lock_id: str | None = None) -> None:
        """Lock the project.

        Args:
            lock_type (str, LockType): Lock type.
            lock_id (str, optional): Lock ID.
        """
        self.fetch('lock_status')

        if self.lock_status.lock_type != LockType.NOT_LOCKED:
            msg = (
                f"Project '{self.id}' is already locked with the lock type "
                f"`{self.lock_status.lock_type}`. "
                f"Please unlock it before applying a new lock."
            )
            raise ValueError(msg)

        lock_type = get_enum_val(lock_type, LockType)

        projects.update_project_lock(
            self.connection, self.id, {'lockType': lock_type, 'lockId': lock_id}
        )

        if config.verbose:
            logger.info(f"Project '{self.id}' locked.")

    @method_version_handler('11.3.0600')
    def unlock(
        self,
        lock_type: str | LockType | None = None,
        lock_id: str | None = None,
        force: bool = False,
    ) -> None:
        """Unlock the project.

        Args:
            lock_type (str, LockType, optional): Lock type.  Optional only if
                `force` is set to True.
            lock_id (str, optional): Lock ID.
            force (bool, optional): Whether to force unlock the project.
        """
        self.fetch('lock_status')

        if self.lock_status.lock_type == LockType.NOT_LOCKED:
            msg = f"Project '{self.id}' is not locked."
            raise ValueError(msg)

        if not force and not (lock_id and lock_type):
            msg = (
                "`lock_id` and `lock_type` must be provided to unlock the project "
                "when `force` is False."
            )
            raise ValueError(msg)

        if force and not lock_type:
            lock_type = self.lock_status.lock_type

        lock_type = get_enum_val(lock_type, LockType)

        projects.delete_project_lock(
            self.connection,
            self.id,
            lock_type=lock_type,
            lock_id=lock_id,
            force=force,
        )

        if config.verbose:
            logger.info(f"Project '{self.id}' unlocked.")

    def get_status_on_node(self, node: 'str | Node') -> IdleMode:
        """Get status of the project of specific node in the connected
        Intelligence server cluster.

        Args:
            node (str, Node): Name of the node or Node object.

        Returns:
            IdleMode: Status of the project on the node.
        """
        node_name = node if isinstance(node, str) else node.name
        return IdleMode(
            monitors.get_project_status_on_node(
                self.connection, node_name, self.id
            ).json()['status']
        )

    @method_version_handler('11.5.0700')
    def duplicate(
        self,
        target_name: str,
        duplication_config: 'dict | DuplicationConfig | None' = None,
    ) -> 'ProjectDuplication':
        """Duplicate the project with a new name.

        Args:
            target_name (str): New name for the duplicated project.
            duplication_config (dict, DuplicationConfig, optional):
                Configuration for the duplication process. If not provided
                `DuplicationConfig()` with default values will be used.

        Returns:
            ProjectDuplication object.
        """

        if not duplication_config:
            duplication_config = DuplicationConfig()
        if isinstance(duplication_config, DuplicationConfig):
            duplication_config = duplication_config.to_dict()
        body = {
            "source": {
                "environment": {
                    "id": self.connection.base_url,
                    "name": self.connection.base_url,
                },
                "project": {
                    "id": self.id,
                    "name": self.name,
                },
            },
            "target": {
                "environment": {
                    "id": self.connection.base_url,
                    "name": self.connection.base_url,
                },
                "project": {"name": target_name},
            },
            "settings": duplication_config,
        }
        resp = projects.trigger_project_duplication(self.connection, self.id, body)
        return ProjectDuplication.from_dict(
            helper.get_response_json(resp), connection=self.connection
        )

    @property
    def load_on_startup(self):
        """View nodes (servers) to load project on startup."""
        response = projects.get_projects_on_startup(self.connection).json()
        return response['projects'][self.id]['nodes']

    @property
    def settings(self) -> "ProjectSettings":
        """`Settings` object storing Project settings.

        Settings can be listed by using `list_properties()` method.
        Settings can be modified directly by setting the values in the
        object.
        """

        if not hasattr(self, "_settings"):
            super(Entity, self).__setattr__(
                "_settings", ProjectSettings(self.connection, self.id)
            )
        return self._settings

    @settings.setter
    def settings(self, settings: "ProjectSettings") -> None:
        super(Entity, self).__setattr__("_settings", settings)

    @property
    def status(self):
        return self._status

    @property
    def alias(self):
        return self._alias

    @property
    def nodes(self):
        return self._nodes

    @property
    @method_version_handler(version='11.3.1200')
    def data_language_settings(self) -> DataLanguageSettings:
        if not hasattr(self._data_language_settings, '_connection'):
            self._data_language_settings._connection = self.connection
        if not hasattr(self._data_language_settings, '_project_id'):
            self._data_language_settings._project_id = self.id
        return self._data_language_settings

    @property
    @method_version_handler(version='11.3.1200')
    def metadata_language_settings(self) -> MetadataLanguageSettings:
        if not hasattr(self._metadata_language_settings, '_connection'):
            self._metadata_language_settings._connection = self.connection
        if not hasattr(self._metadata_language_settings, '_project_id'):
            self._metadata_language_settings._project_id = self.id
        return self._metadata_language_settings

    @property
    @method_version_handler('11.3.0600')
    def lock_status(self) -> LockStatus:
        return self._lock_status


class ProjectSettings(BaseSettings):
    """Object representation of Strategy One Project (Project) Settings.

    Used to fetch, view, modify, update, export to file, import from file and
    validate Project settings.

    The object can be optionally initialized with `connection` and
    `project_id`, which will automatically fetch the current settings for
    the specified project. If not specified, settings can be loaded from
    file using `import_from()` method. Object attributes (representing settings)
    can be modified manually. Lastly, the object can be applied to any
    project using the `update()` method.

    Attributes:
        connection: A Strategy One connection object
    """

    _TYPE = "allProjectSettings"
    _CONVERSION_MAP = {
        'maxCubeSizeForDownload': 'B',
        'maxDataUploadSize': 'B',
        'maxMstrFileSize': 'B',
        'maxHistoryListInboxMessage': 'B',
        'maxMemoryPerDataFetch': 'B',
        'maxElementCacheMemoryConsumption': 'B',
        'maxObjectCacheMemoryConsumption': 'B',
        'maxRWDCacheMemoryConsumption': 'B',
        'maxReportCacheMemoryConsumption': 'B',
        'maxCubeQuota': 'B',
        'maxCubeMemUsage': 'B',
        'maxSqlGenerationMemoryConsumption': 'B',
        'reportCacheLifeTime': 'hour',
        'maxWarehouseJobExecTime': 'sec',
        'maxReportExecutionTime': 'sec',
        'maxScheduledReportExecutionTime': 'sec',
        'statisticsPurgeTimeout': 'sec',
        'maxPromptWaitingTime': 'sec',
        'maxRAMForReportRWDCacheIndex': '%',
        'cubeIndexGrowthUpperBound': '%',
    }
    _CACHING_SETTINGS_TO_ENABLE = (
        "enableReportServerCaching",
        "enableCachingForPromptedReportDocument",
        "enableCachingForNonPromptedReportDocument",
        "enableXmlCachingForReport",
    )
    _CACHING_SETTINGS_TO_DISABLE = _CACHING_SETTINGS_TO_ENABLE + (
        "recordPromptAnswersForCacheMonitoring",
        "enableDocumentOutputCachingInXml",
        "enableDocumentOutputCachingInHtml",
        "enableDocumentOutputCachingInPdf",
        "enableDocumentOutputCachingInExcel",
    )

    def __init__(self, connection: Connection, project_id: str | None = None):
        """Initialize `ProjectSettings` object.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            project_id: Project ID
        """
        super(BaseSettings, self).__setattr__('_connection', connection)
        super(BaseSettings, self).__setattr__('_project_id', project_id)
        self._configure_settings()

        if project_id:
            self.fetch()

    def fetch(self, project_id: str | None = None) -> None:
        """Fetch current project settings from I-Server and update this
        `ProjectSettings` object.

        Args:
            project_id: Project ID
        """
        self._check_params(project_id)
        super().fetch()

    def update(self, project_id: str | None = None) -> None:
        """Update the current project settings on I-Server using this
        Settings object.

        Args:
            project_id: Project ID
        """
        self._check_params(project_id)
        set_dict = self._prepare_settings_push()
        if not set_dict and config.verbose:
            logger.info('No settings to update.')
            return
        response = projects.update_project_settings(
            self._connection, self._project_id, set_dict
        )
        if config.verbose:
            if response.status_code == 200:
                logger.info('Project settings updated.')
            elif response.status_code == 207:
                partial_succ = response.json()
                logging.info(f'Project settings partially successful.\n{partial_succ}')
        super().update()

    def __setattr__(self, key, value) -> None:
        if isinstance(value, Enum):
            value = get_enum_val(value, type(value))

        if isinstance(value, list):
            value = [
                get_enum_val(v, type(v)) if isinstance(v, Enum) else v for v in value
            ]

        super().__setattr__(key, value)

    @wip()
    def enable_caching(self) -> None:
        """
        Enable caching settings for the current project on I-Server
        using this Settings object
        """
        for setting in self._CACHING_SETTINGS_TO_ENABLE:
            if hasattr(self, setting):
                self.__setattr__(setting, True)

    @wip()
    def disable_caching(self) -> None:
        """
        Disable caching settings for the current project on I-Server
        using this Settings object
        """
        for setting in self._CACHING_SETTINGS_TO_DISABLE:
            if hasattr(self, setting):
                self.__setattr__(setting, False)

    def _fetch(self) -> dict:
        response = projects.get_project_settings(
            self._connection, self._project_id, whitelist=[('ERR001', 404)]
        )
        settings = response.json() if response.ok else {}
        if not response.ok:
            msg = (
                "Settings could not be fetched. It may be because the project is not "
                "loaded in the Intelligence Server or the project is idle."
            )
            helper.exception_handler(msg, Warning)
        return self._prepare_settings_fetch(settings)

    def _get_config(self):
        if not ProjectSettings._CONFIG:
            project_id = self._project_id
            if not project_id:
                project_id = Project._list_loaded_projects(
                    self._connection, to_dictionary=True
                )['id'][0]
            response = projects.get_project_settings_config(
                self._connection, project_id
            )
            ProjectSettings._CONFIG = response.json()
            super()._get_config()

    def _check_params(self, project_id: str | None = None):
        if project_id:
            super(BaseSettings, self).__setattr__('_project_id', project_id)
        if not self._connection or not self._project_id:
            raise AttributeError(
                "Please provide `connection` and `project_id` parameter"
            )

    @wip()
    def list_caching_properties(self, show_description: bool = False) -> dict:
        """
        Fetch current project settings connected with caching from I-Server

        Args:
            show_description (bool): if True return, description and value
                for each setting, else, return values only
        """
        self.fetch()
        return {
            k: v
            for (k, v) in self.list_properties(
                show_description=show_description
            ).items()
            if any(word in k.lower() for word in ("cache", "caching"))
        }


@dataclass
class DuplicationConfig(helper.Dictable):
    """Configuration for project duplication.

    Attributes:
        schema_objects_only (bool, optional): If True, only schema objects will
            be duplicated.
        skip_empty_profile_folders (bool, optional): Whether to skip empty
            profile folders during duplication.
        include_user_subscriptions (bool, optional): Whether to include user
            subscriptions in the duplication.
        include_contact_subscriptions (bool, optional): Whether to include
            contact subscriptions in the duplication.
        import_description (str, optional): Description for the import operation
            to be stored in ProjectDuplication class object.
        import_default_locale (int, optional): Locale used for
            internationalization in imported project. Please provide Language
            object 'lcid' attribute.
        import_locales (list[int], optional): List of locale ids for imported
            project. Please provide Language object 'lcid' attribute.
    """

    schema_objects_only: bool = True
    skip_empty_profile_folders: bool = True
    include_user_subscriptions: bool = True
    include_contact_subscriptions: bool = True
    import_description: str | None = 'Project Duplication'
    import_default_locale: int | None = 0
    import_locales: list[int] | None = field(default_factory=lambda: [0])

    def __post_init__(self):
        if self.import_default_locale not in self.import_locales:
            raise ValueError("Default locale must be included in the import locales.")

    def to_dict(self) -> dict:
        """Convert the duplication configuration to a dictionary accepted by
        the API."""
        settings = {
            "export": {
                "projectObjectsPreference": {
                    "schemaObjectsOnly": self.schema_objects_only,
                    "skipEmptyProfileFolders": self.skip_empty_profile_folders,
                },
                "subscriptionPreferences": {
                    "includeUserSubscriptions": self.include_user_subscriptions,
                    "includeContactSubscriptions": self.include_contact_subscriptions,
                },
            },
            "import": {
                "description": self.import_description,
                "defaultLocale": self.import_default_locale,
                "locales": self.import_locales,
            },
        }
        return settings

    @classmethod
    def from_dict(cls, source, **kwargs):
        """Initialize DuplicationConfig object from raw settings dictionary."""
        source = helper.camel_to_snake(source)
        export_sets = source.get('export', {})
        import_sets = source.get('import', {})
        obj = DuplicationConfig(
            schema_objects_only=export_sets.get('project_objects_preference', {}).get(
                'schema_objects_only', True
            ),
            skip_empty_profile_folders=export_sets.get(
                'project_objects_preference', {}
            ).get('skip_empty_profile_folders', True),
            include_user_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_user_subscriptions', True),
            include_contact_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_contact_subscriptions', True),
            import_description=import_sets.get('description', None),
            import_default_locale=import_sets.get('default_locale', 0),
            import_locales=import_sets.get('locales', [0]),
        )
        return obj


@dataclass
class ProjectInfo(helper.Dictable):
    """Dataclass to store project duplication record info. It stores
    environment, project, and creator info."""

    creator: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    project: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, source, **kwargs):
        """Initialize ProjectInfo from a dictionary."""
        return cls(
            creator=source.get('creator', {}),
            environment=source.get('environment', {}),
            project=source.get('project', {}),
        )


class ProjectDuplicationStatus(AutoUpperName):
    """Enum representing the status of a project duplication."""

    UNKNOWN = auto()
    CREATED = auto()
    CREATE_FAILED = auto()
    EXPORTING = auto()
    EXPORTED = auto()
    EXPORT_FAILED = auto()
    IMPORTING = auto()
    IMPORT_FAILED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    CANCELLING = auto()
    EXPORT_SYNCING = auto()
    IMPORT_SYNCING = auto()


@method_version_handler('11.5.0700')
def list_projects_duplications(
    connection: Connection, limit: int | None = None, to_dictionary: bool = False
) -> list['ProjectDuplication | dict']:
    """Get project duplications.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
        limit (int, optional): Limit the number of elements returned. If `None`
            (default), all objects are returned.
        to_dictionary (bool, optional): If `True` returns dict, by default
            (False) returns ProjectDuplication objects.

    Returns:
        List of ProjectDuplication objects or list od dicts.
    """
    duplications = projects_processors.get_project_duplications(
        connection=connection, limit=limit
    )

    duplications = helper.camel_to_snake(duplications)
    if to_dictionary:
        return duplications
    return [
        ProjectDuplication.from_dict(
            source=duplication, connection=connection, with_missing_value=False
        )
        for duplication in duplications
    ]


class ProjectDuplication(EntityBase):
    """Object representation of a project duplication request.

    Attributes:
        id (str): Duplication job ID.
        source (ProjectInfo): Source environment, project, and creator info.
        target (ProjectInfo): Target environment, project, and creator info.
        created_date (datetime): Duplication creation date.
        last_updated_date (datetime): Duplication last update date.
        status (ProjectDuplicationStatus): Duplication status.
        progress (int): Duplication progress percentage.
        message (str): Status or error message.
        settings (DuplicationConfig): Duplication settings.
    """

    _API_GETTERS = {
        (
            'id',
            'source',
            'target',
            'created_date',
            'last_updated_date',
            'status',
            'progress',
            'message',
            'settings',
        ): projects.get_project_duplication
    }

    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'created_date': DatetimeFormats.FULLDATETIME,
        'last_updated_date': DatetimeFormats.FULLDATETIME,
        'settings': DuplicationConfig.from_dict,
        'source': ProjectInfo.from_dict,
        'status': ProjectDuplicationStatus,
        'target': ProjectInfo.from_dict,
    }

    def __init__(
        self,
        connection: "Connection",
        id: str,
    ) -> None:
        """Initialize ProjectDuplication object.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            id: ID of the ProjectDuplication
        """

        super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.source = (
            ProjectInfo.from_dict(kwargs.get('source', {}))
            if kwargs.get('source')
            else {}
        )
        self.target = (
            ProjectInfo.from_dict(kwargs.get('target', {}))
            if kwargs.get('target')
            else {}
        )
        self.created_date = time_helper.map_str_to_datetime(
            "created_date", kwargs.get("created_date"), self._FROM_DICT_MAP
        )
        self.last_updated_date = time_helper.map_str_to_datetime(
            "last_updated_date", kwargs.get("last_updated_date"), self._FROM_DICT_MAP
        )
        self.status = (
            ProjectDuplicationStatus(kwargs.get('status'))
            if kwargs.get('status')
            else None
        )
        self.progress = kwargs.get('progress', 0)
        self.message = kwargs.get('message', '')
        self.settings = (
            DuplicationConfig.from_dict(kwargs.get('settings'))
            if kwargs.get('settings')
            else None
        )

    @classmethod
    def from_dict(
        cls,
        source: dict,
        connection: 'Connection | None' = None,
        with_missing_value: bool = False,
    ):
        return super().from_dict(
            source=source,
            connection=connection,
            with_missing_value=with_missing_value,
        )

    def cancel(self) -> bool:
        """Cancel the project duplication job.

        Returns:
            bool: True if the cancellation was successful, False otherwise.
        """
        body = {"status": "cancelled"}
        response = projects.cancel_project_duplication(self.connection, self.id, body)
        if response.status_code == 204:
            if config.verbose:
                logger.info(
                    f"Project duplication with ID '{self.id}' cancelled successfully."
                )
            return True
        else:
            if config.verbose:
                logger.error(
                    f"Failed to cancel project duplication with ID '{self.id}'."
                )
            return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"progress={self.progress}, "
            f"source_project='{self.source.project.get('name')}', "
            f"target_project='{self.target.project.get('name')}')"
        )

    def wait_for_stable_status(
        self, timeout: int = 240, interval: int = 2
    ) -> 'ProjectDuplication':
        """Wait for the project duplication to reach a stable status.

        Args:
            timeout (int, optional): Maximum time to wait in seconds.
            interval (int, optional): Time between status checks in seconds.

        Returns:
            ProjectDuplication: The project duplication object with updated
                status.
        """
        not_stable_statuses = [
            ProjectDuplicationStatus.CANCELLING,
            ProjectDuplicationStatus.EXPORTING,
            ProjectDuplicationStatus.EXPORT_SYNCING,
            ProjectDuplicationStatus.IMPORTING,
            ProjectDuplicationStatus.IMPORT_SYNCING,
        ]
        return helper.wait_for_stable_status(
            self, 'status', not_stable_statuses, timeout=timeout, interval=interval
        )
