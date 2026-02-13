import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Literal

from pandas import DataFrame, Series
from tqdm import tqdm

from mstrio import config
from mstrio.api import administration
from mstrio.api import change_journal as change_journal_api
from mstrio.api import datasources as datasources_api
from mstrio.api import monitors, objects, projects
from mstrio.connection import Connection
from mstrio.helpers import IServerError, VersionException
from mstrio.server.change_journal import _format_timestamp_for_api_purge
from mstrio.server.project_languages import (
    DataLanguageSettings,
    MetadataLanguageSettings,
)
from mstrio.utils import helper, time_helper
from mstrio.utils.entity import (
    ChangeJournalMixin,
    DeleteMixin,
    Entity,
    EntityBase,
    ObjectTypes,
)
from mstrio.utils.enum_helper import AutoName, AutoUpperName, get_enum_val
from mstrio.utils.resolvers import validate_owner_key_in_filters
from mstrio.utils.response_processors import datasources as datasources_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.response_processors import projects as projects_processors
from mstrio.utils.settings.base_settings import BaseSettings
from mstrio.utils.time_helper import DatetimeFormats
from mstrio.utils.version_helper import (
    is_server_min_version,
    meets_minimal_version,
    method_version_handler,
)
from mstrio.utils.vldb_mixin import ModelVldbMixin
from mstrio.utils.wip import WipLevels, wip

if TYPE_CHECKING:
    from requests import Response

    from mstrio.datasources import DatasourceInstance
    from mstrio.object_management.object import Object
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


class Project(Entity, DeleteMixin, ModelVldbMixin):
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
    _API_DEL_JOURNAL_MIN_VER = None
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

        Note:
            You can initialize Project selected in `Connection` object by making
            sure `connection` has project selected and providing connection
            param as the only one: `Project(connection=conn)`.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            name: Project name
            id: Project ID
        """

        if id is None:
            if name is not None:
                project_list = Project._list_project_ids(connection, name=name)
                if project_list:
                    id = project_list[0]
                else:
                    helper.exception_handler(
                        f"There is no project with the given name: '{name}'",
                        exception_type=ValueError,
                    )
            else:
                if connection.project_id:
                    if config.verbose:
                        logger.info(
                            "Initializing Project selected in `Connection` object."
                        )
                    id = connection.project_id
                else:
                    helper.exception_handler(
                        (
                            "Please specify either 'name' or 'id' parameter in "
                            "the constructor or select a project in `Connection`."
                        ),
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
        async_request: bool = False,
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
                disable=not config.verbose or not config.progress_bar,
                delay=3,
            ):
                res = projects.create_project(
                    connection, name, description, async_request
                )

                if async_request:
                    if not res.ok or res.status_code != 202:
                        helper.response_handler(res)
                        raise IServerError(  # for if helper above did not raise
                            "Async Project creation request was not accepted.",
                            res.status_code,
                        )

                    return None

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
        validate_owner_key_in_filters(filters)

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
        validate_owner_key_in_filters(filters)

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
        self,
        func: Callable[[list[str], dict], None],
        on_nodes: 'str | Node | list[str | Node] | None' = None,
        **mode,
    ):
        on_nodes: list[str] = self._normalize_nodes(on_nodes)
        func(on_nodes, **mode)

    def _change_project_state_all_nodes(
        self, status: str, delete_sessions: bool | None = None
    ):
        body = {"status": status}
        response = monitors.update_project_status(
            self.connection,
            body,
            project_id=self.id,
            delete_sessions=delete_sessions,
        )
        if response.status_code == 202 and config.verbose:
            logger.info(
                f"Project '{self.id}' changed status to '{status}' on all nodes."
            )

    @method_version_handler('11.2.0000')
    def idle(
        self,
        on_nodes: 'str | Node | list[str | Node] | None' = None,
        mode: IdleMode | str = IdleMode.REQUEST,
    ) -> None:
        """Request to idle a specific cluster node. Idle project with mode
        options.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be idled on all of the nodes.
            mode: One of: `IdleMode` values.
        """

        def idle_project(nodes: list[str], mode: IdleMode):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": mode.value}
                ]
            }
            for node in nodes:
                try:
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
                                f"Project '{self.id}' changed status to '{mode}' on "
                                f"node '{node}'."
                            )
                except Exception as err:
                    logger.error(err)
                    continue

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
    def resume(self, on_nodes: 'str | Node | list[str | Node] | None' = None) -> None:
        """Request to resume the project on the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be resumed on all of the nodes.
        """

        def resume_project(nodes: list[str]):
            body = {
                "operationList": [
                    {"op": "replace", "path": self._STATUS_PATH, "value": "loaded"}
                ]
            }
            for node in nodes:
                try:
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
                            logger.info(
                                f"Project '{self.id}' resumed on node '{node}'."
                            )
                except Exception as err:
                    logger.error(err)
                    continue

        self.__change_project_state(func=resume_project, on_nodes=on_nodes)

    def _normalize_nodes(
        self, on_nodes: 'str | list[str] | Node | list[Node] | None'
    ) -> list[str]:
        """Normalize `on_nodes` parameter to a list of node names. Select all
            nodes as a default if `on_nodes` is None.
        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes or None.
        Returns:
            (list[str]): List of node names.
        """
        if on_nodes is None:
            return self._node_names

        if not isinstance(on_nodes, list):
            on_nodes = [on_nodes]

        from mstrio.server.node import Node

        return [node.name if isinstance(node, Node) else node for node in on_nodes]

    def _load_project(self, node):
        body = {
            "operationList": [
                {"op": "replace", "path": self._STATUS_PATH, "value": "loaded"}
            ]
        }
        response = monitors.update_node_properties(self.connection, node, self.id, body)
        if response.status_code == 202:
            tmp = helper.filter_list_of_dicts(self.nodes, name=node)
            tmp[0]['projects'] = [response.json()['project']]
            self._nodes = tmp
            if tmp[0]['projects'][0]['status'] != 'loaded':
                self.fetch('nodes')
            if config.verbose:
                logger.info(f"Project '{self.id}' loaded on node '{node}'.")

    @method_version_handler('11.2.0000')
    def load(
        self, on_nodes: 'str | list[str] | Node | list[Node] | None' = None
    ) -> None:
        """Request to load the project onto the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be loaded on all of the nodes.
        """
        on_nodes: list[str] = self._normalize_nodes(on_nodes)
        all_nodes_are_selected = set(self._node_names) == set(on_nodes)

        if all_nodes_are_selected and meets_minimal_version(
            self.connection.iserver_version, '11.5.0500'
        ):
            self._change_project_state_all_nodes(status="loaded")
        else:
            self.__change_project_state(func=self._load_project, on_nodes=on_nodes)

    def _unload_project(self, node):
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
            logger.warning(f"Project '{self.id}' already unloaded on node '{node}'.")

    @method_version_handler('11.2.0000')
    def unload(
        self,
        on_nodes: 'str | list[str] | Node | list[Node] | None' = None,
        delete_sessions: bool | None = None,
    ) -> None:
        """Request to unload the project from the chosen cluster nodes. If
        nodes are not specified, the project will be unloaded on all nodes.
        The unload action cannot be performed until all jobs and connections
        for project are completed. Once these processes have finished,
        pending project will be automatically unloaded.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be unloaded on all of the nodes.
            delete_sessions: If True, will delete all project sessions
                immediately before unloading.
        """
        on_nodes: list[str] = self._normalize_nodes(on_nodes)
        all_nodes_are_selected = set(self._node_names) == set(on_nodes)

        supports_server_wide_endpoint = meets_minimal_version(
            self.connection.iserver_version, '11.5.0500'
        )
        if delete_sessions is not None and not supports_server_wide_endpoint:
            logger.warning(
                "The `delete_sessions` argument requires iServer version 11.5.0500 or "
                f"later. Since your server version: {self.connection.iserver_version} "
                "is not compatible, this parameter will be omitted."
            )

        if all_nodes_are_selected and supports_server_wide_endpoint:
            self._change_project_state_all_nodes(
                status="unloaded", delete_sessions=delete_sessions
            )
        else:
            self.__change_project_state(func=self._unload_project, on_nodes=on_nodes)

    @method_version_handler('11.3.0800')
    def delete(
        self,
        force: bool = False,
        unload_beforehand: bool = True,
        delete_immediately: bool = False,
        journal_comment: str | None = None,
    ) -> bool:
        """Delete project.

        Note:
            All objects within a Project will be permanently deleted.
            This cannot be undone.

        Args:
            force (bool, optional): If True, will not prompt for confirmation.
                Default is False.
            unload_beforehand (bool, optional): If True, will unload the project
                from all nodes before deletion. Default is True.
            delete_immediately (bool, optional): If True, will delete all
                connection sessions from the Project before deletion and will
                not require the project to be unloaded beforehand. Default is
                False.
            journal_comment (str, optional): Comment to be added to the change
                journal for this deletion. If None, no comment is added.

        Returns:
            True if project was deleted, False otherwise.
        """

        if unload_beforehand and self.is_loaded():
            self.unload(delete_sessions=delete_immediately)

        supports_session_delete = meets_minimal_version(
            self.connection.iserver_version, '11.5.0500'
        )
        will_delete_immediately = (
            not unload_beforehand
            and delete_immediately
            and supports_session_delete
            and self.is_loaded()
        )

        msg_part = (
            "delete project"
            if not will_delete_immediately
            else "delete (immediately, without unloading) project"
        )

        self._DELETE_CONFIRM_MSG = (
            f"Are you sure you want to {msg_part} "
            f"'{self.name}' with ID: {self._id}?\n"
            "All objects will be permanently deleted. This cannot be undone.\n"
            "Please type the project name to confirm: "
        )
        self._DELETE_SUCCESS_MSG = (
            f"Project '{self.name}' has been successfully deleted."
        )
        self._DELETE_PROMPT_ANSWER = self.name

        return super().delete(
            force=force,
            journal_comment=journal_comment,
            delete_sessions=will_delete_immediately,
        )

    @method_version_handler('11.3.0000')
    def register(
        self,
        on_nodes: 'str | Node | list[str | Node] | None' = None,
    ) -> None:
        """Register project on nodes.

        A registered project will load on node (server) startup.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be set to load on all available nodes on startup.
        """
        # a call to `_register` will overwrite with new list of nodes
        register_all_nodes = on_nodes is None
        if register_all_nodes:
            value = self._node_names
        else:
            on_nodes: list[str] = self._normalize_nodes(on_nodes)
            value = list(set(self.load_on_startup) | set(on_nodes))
        self._register(on_nodes=value)

    @method_version_handler('11.3.0000')
    def unregister(
        self,
        on_nodes: 'str | Node | list[str | Node] | None' = None,
    ) -> None:
        """Unregister project on nodes.

        An unregistered project will not load on node (server) startup.

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, project will
                be set to not load on any nodes on startup.
        """
        # a call to `_register` will overwrite with new list of nodes
        unregister_all_nodes = on_nodes is None
        if unregister_all_nodes:
            value = []
        else:
            on_nodes: list[str] = self._normalize_nodes(on_nodes)
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

    def is_loaded(
        self,
        on_nodes: 'str | Node | list[str | Node] | None' = None,
        check_all_selected_nodes: bool = False,
        strict: bool = False,
    ) -> bool:
        """Check if the project is loaded on any node (server).

        Args:
            on_nodes (str | Node | list[str | Node], optional):
                One or more references to nodes. If not provided, all nodes
                in the cluster will be checked.
            check_all_selected_nodes (bool, optional): If True, checks if the
                project is loaded on all given nodes. If False, checks if the
                project is loaded on at least one of the selected nodes.
                Default is False.
            strict (bool, optional): If True, performs additional checks that
                the project is not only loaded on the server, but also reliably
                accessible by Strategy One services that might not be
                immediately synced after the project is loaded.
                Default is False.
        """

        self.fetch('nodes')
        if not isinstance(self.nodes, list):
            helper.exception_handler(
                "Could not retrieve current project status.",
                exception_type=ConnectionError,
            )

        # Filter nodes list by whether project is loaded on the node.
        nodes_loaded = {
            node['name']
            for node in self.nodes
            if any(
                prj['id'] == self.id and prj['status'] == 'loaded'
                for prj in node.get('projects', [])
            )
        }
        if strict:
            libapi_nodes_res = administration.get_cluster_membership(
                self.connection
            ).json()
            nodes_loaded_from_libapi = {
                node['name']
                for node in libapi_nodes_res
                if any(
                    prj['id'] == self.id and prj['status'] == 0
                    for prj in node.get('projects', [])
                )
            }
            nodes_loaded &= nodes_loaded_from_libapi

        nodes_to_check = set(self._normalize_nodes(on_nodes))

        if check_all_selected_nodes:
            return nodes_to_check.issubset(nodes_loaded)
        else:
            return bool(nodes_to_check.intersection(nodes_loaded))

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

    def _register(self, on_nodes: list[str]) -> None:
        """Overwrite list of nodes on which project will load on startup.
        Args:
            on_nodes (list[str]): List of node names. Must be normalized to a
                list of node names with _normalize_nodes.
        """
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

    @method_version_handler('11.4.1200')
    def delete_unused_managed_objects(
        self,
        try_force_delete: bool = False,
        return_failed_items: bool = False,
    ) -> bool | list[dict]:
        """Delete all unused managed objects in the project.

        Managed Objects in scope of this method are objects of type:
        - ObjectTypes.ATTRIBUTE,
        - ObjectTypes.METRIC,
        - ObjectTypes.CONSOLIDATION,
        - ObjectTypes.CONSOLIDATION_ELEMENT,

        Note:
            This method is known to be resource and time intensive. Use only
            if necessary.

        Args:
            try_force_delete (bool, optional): If `True`, will attempt to delete
                items that could not be confirmed whether they are unused, for
                any reason. Server should not allow deleting of those and throw
                error which will be caught by this method. Defaults to `False`.
            return_failed_items (bool, optional): If `True`, will return a list
                of dicts of data of objects that could not be deleted. If
                `False`, will return a boolean indicating whether all unused
                objects were deleted successfully. Defaults to `False`.

        Returns:
            If `return_failed_items` is `False`, returns `True` if all unused
            managed objects were deleted successfully, `False` otherwise.
            If `return_failed_items` is `True`, returns a list of dicts of
            objects that could not be deleted. If all objects were deleted
            successfully, returns an empty list.
        """
        from mstrio.object_management.object import Object
        from mstrio.object_management.search_enums import SearchDomain, SearchScope
        from mstrio.object_management.search_operations import full_search

        items = full_search(
            self.connection,
            scope=SearchScope.MANAGED_ONLY,
            domain=SearchDomain.PROJECT,
            object_types=[
                ObjectTypes.ATTRIBUTE,
                ObjectTypes.METRIC,
                ObjectTypes.CONSOLIDATION,
                ObjectTypes.CONSOLIDATION_ELEMENT,
            ],
            project=self,
            include_hidden=True,
            to_dictionary=True,
        )

        if config.verbose:
            logger.info(f"Found {len(items)} managed objects to check if unused.")

        problematic_items: list[dict] = []
        final_items: list["Object"] = []
        final_len = 0  # cumulative final items length

        def bulk_delete(objs: list["Object"]) -> bool:
            FAIL_MSG = "Deleting some of the unused managed objects failed."

            try:
                res: Response = objects.bulk_delete_objects(
                    self.connection,
                    [obj.id for obj in objs],
                    [obj.type.value for obj in objs],
                    project_id=self.id,
                    error_msg=FAIL_MSG,
                )

                if config.verbose and res.ok:
                    logger.info(
                        "Successfully deleted a batch of unused managed "
                        f"objects in project '{self.id}'."
                    )

                return res.ok
            except Exception:
                logger.warning(FAIL_MSG)
                return False

        def perform_bulk_delete(checked: int, unused: int) -> None:
            nonlocal final_items

            if config.verbose:
                logger.info(
                    f"Checked {checked} items so far. Found {unused} are "
                    "confirmed unused."
                    + (" Deleting this new batch now." if final_items else "")
                )

            if final_items:
                if not bulk_delete(final_items):
                    # bulk delete may have failed due to only some of items,
                    # not all. Retry one by one to find problematic ones.
                    for obj in final_items:
                        try:
                            obj.delete(force=True)
                        except Exception:
                            problematic_items.append(obj.to_dict())

                final_items = []

        for i, itm in enumerate(items):
            if i % 100 == 0 and i > 0:
                perform_bulk_delete(i, final_len)

            try:
                obj = Object.from_dict(
                    itm,
                    self.connection,
                    with_missing_value=True,
                )

                if not obj.has_dependents():
                    final_len += 1
                    final_items.append(obj)
            except Exception:
                problematic_items.append(itm)

        perform_bulk_delete(len(items), final_len)

        if problematic_items and try_force_delete:
            # At this point we were either not able to delete the item, not
            # able to check if there are dependents, or something happened
            # during the bulk delete. As a last resort, we will try the most
            # raw delete method just to see.
            #
            # This will fail if there are dependents and this is what we want.
            if config.verbose:
                logger.info(
                    "Some items could not be confirmed whether they are unused. "
                    "Will try to delete them (this will fail if they are used)."
                )

            for prob_dict in problematic_items.copy():
                try:
                    with config.temp_verbose_disable():
                        objects.delete_object(
                            self.connection,
                            prob_dict['id'],
                            prob_dict['type'],
                            project_id=self.id,
                        )
                    problematic_items.remove(prob_dict)
                except Exception:
                    continue

        if problematic_items:
            logger.warning(
                "For the following items, could not check if they are unused "
                "or could not delete them: "
                f"{[p.get('id') for p in problematic_items]}. They were skipped."
            )

        if return_failed_items:
            return problematic_items
        return len(problematic_items) == 0

    def _build_duplication_body(
        self,
        target_name: str,
        target_env: 'Connection | Environment | None' = None,
        duplication_config: (
            'dict | DuplicationConfig | CrossDuplicationConfig | None'
        ) = None,
    ) -> dict:
        """Build common body part for project duplication methods.

        Args:
            target_name (str): New name for the duplicated project.
            target_env (Connection, Environment, optional):
                Target environment or connection to the target environment.
                If not provided, current environment will be used.
            duplication_config (dict, DuplicationConfig, CrossDuplicationConfig,
                optional): Configuration for the duplication process. If not
                provided `DuplicationConfig()` with default values will be used.

        Returns:
            dict: Body for duplication request.
        """
        from mstrio.server.environment import Environment

        if not duplication_config:
            duplication_config = DuplicationConfig()
        if isinstance(duplication_config, DuplicationConfig):
            duplication_config = duplication_config.to_dict(connection=self.connection)

        if target_env is None:
            target_env = self.connection
        elif isinstance(target_env, Environment):
            target_env = target_env.connection

        body = {
            'source': {
                'environment': {
                    'id': self.connection.base_url,
                    'name': self.connection.base_url,
                },
                'project': {
                    'id': self.id,
                    'name': self.name,
                },
            },
            'target': {
                'environment': {
                    'id': target_env.base_url,
                    'name': target_env.base_url,
                },
                'project': {'name': target_name},
            },
            'settings': duplication_config,
        }
        return body

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

        body = self._build_duplication_body(
            target_name=target_name,
            duplication_config=duplication_config,
        )
        resp = projects.trigger_project_duplication(self.connection, self.id, body)
        return ProjectDuplication.from_dict(
            helper.get_response_json(resp), connection=self.connection
        )

    @wip(level=WipLevels.PREVIEW)
    @method_version_handler('11.5.1200')
    def duplicate_to_other_environment(
        self,
        target_name: str,
        target_env: 'Connection | Environment',
        cross_duplication_config: 'dict | CrossDuplicationConfig | None' = None,
        sync_with_target_env: bool | None = True,
    ) -> 'ProjectDuplication':
        """Duplicate the project with a new name to another environment. It can
        work in two modes:
        1) duplication by StorageService (default, when `sync_with_target_env`
            is True) - in this mode, after triggering duplication on source
            environment, the method will also trigger duplication on target
            environment. This requires StorageService to be configured between
            the two environments.
        2) manual duplication (when `sync_with_target_env` is False) - in this
            mode, the method will only trigger duplication on source
            environment. Then the duplication file needs to be manually
            transferred to the target environment and imported there.

        Note:
            Some duplication configuration properties require specific server
            versions. See `DuplicationConfig` documentation for details.

        Args:
            target_name (str): New name for the duplicated project.
            target_env (Connection, Environment): Target environment
                or connection to the target environment.
            cross_duplication_config (dict, CrossDuplicationConfig, optional):
                Configuration for the cross-environment duplication process. If
                not provided `CrossDuplicationConfig()` with default values will
                be used.
            sync_with_target_env (bool, optional): Whether to synchronize the
                duplication with the target environment. If True, the method
                will work in mode 1) described above. If False, the method will
                work in mode 2). Default is True.

        Returns:
            ProjectDuplication object.

        """

        from mstrio.server.environment import Environment

        if isinstance(target_env, Environment):
            target_env = target_env.connection

        if cross_duplication_config is None:
            cross_duplication_config = CrossDuplicationConfig()

        body = self._build_duplication_body(
            target_name=target_name,
            target_env=target_env,
            duplication_config=cross_duplication_config,
        )
        resp = projects.trigger_project_duplication(self.connection, self.id, body)

        if resp.ok:
            logger.info(
                f"Project '{self.name}' | {self.id} duplication from environment "
                f"'{self.connection.base_url}' to '{target_env.base_url}' "
                f"initiated successfully."
            )

        if sync_with_target_env and resp.ok:
            res = projects.trigger_project_duplication_on_target_env(
                target_env, resp.json()['id'], body
            )
            if res.ok:
                logger.info(
                    f"Project '{self.name}' | {self.id} duplication synchronized "
                    f"successfully on target environment '{target_env.base_url}'."
                )
        return ProjectDuplication.from_dict(resp.json(), connection=self.connection)

    @method_version_handler('11.4.0900')
    def purge_change_journals(
        self, comment: str | None = None, timestamp: str | datetime | None = None
    ) -> None:
        """Purge change journal entries for the project.

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
            projects_ids=self.id,
        )

        if config.verbose and res.ok:
            logger.info(
                f"Request to purge change journal entries was successfully sent for "
                f"{self.name} | {self.id} project."
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
    def _node_names(self):
        return [node['name'] for node in self._nodes]

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
    """Object representation of Strategy One Project Settings.

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

    def enable_caching(self) -> None:
        """
        Enable caching settings for the current project on I-Server
        using this Settings object
        """
        for setting in self._CACHING_SETTINGS_TO_ENABLE:
            if hasattr(self, setting):
                self.__setattr__(setting, True)

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


class ProjectDuplicationRule(Enum):
    """Enum representing rules for handling conflicts for configuration
    objects during cross-environment project duplication.

    There are three possible rules:
    - USE_EXISTING (1): Ignore the object in the source MD and retain the
        object with the same ID in the target MD.
    - REPLACE (2): Overwrite the object in the target MD with the object from
        the source MD.
    - MERGE (6): Merge the object in the source MD with the object in the
        target MD. Applicable only to USER and SECURITY_ROLE objects. If the
        merge rule is set for other types of objects, it will fall back to
        USE_EXISTING.
    """

    USE_EXISTING = 1
    REPLACE = 2
    MERGE = 6


@dataclass
class AdminObjectRule(helper.Dictable):
    """Rule for handling conflicts for a specific configuration object during
    cross-environment project duplication.

    Attributes:
        type (ObjectTypes | int): Type of the configuration object.
        rule (ProjectDuplicationRule | int): Rule for handling conflicts for
            the configuration object.
    """

    type: ObjectTypes | int
    rule: ProjectDuplicationRule | int


@dataclass
class DuplicationConfig(helper.Dictable):
    """Configuration for project duplication.

    Attributes:
        schema_objects_only (bool, optional): If True, only schema objects will
            be duplicated.
        skip_empty_profile_folders (bool, optional): Whether to skip empty
            profile folders during duplication.
        skip_all_profile_folders (bool, optional): Whether to skip all profile
            folders during duplication. Available in Strategy One 11.5.0900+.
        include_user_subscriptions (bool, optional): Whether to include user
            subscriptions in the duplication.
        include_contact_subscriptions (bool, optional): Whether to include
            contact subscriptions in the duplication.
        include_contacts_and_contact_groups (bool, optional): Whether to
            include contacts and contact groups in the duplication. Available
            in Strategy One 11.5.0900+.
        import_description (str, optional): Description for the import operation
            to be stored in ProjectDuplication class object.
        import_default_locale (int, optional): Locale used for
            internationalization in imported project. Please provide Language
            object 'lcid' attribute.
        import_locales (list[int], optional): List of locale ids for imported
            project. Please provide Language object 'lcid' attribute.

    Note:
        The properties `skip_all_profile_folders` and
        `include_contacts_and_contact_groups` are only available in Strategy
        One version 11.5.0900 or higher. Using these properties with older
        server versions may result in unexpected behavior.
    """

    schema_objects_only: bool = True
    skip_empty_profile_folders: bool = True
    skip_all_profile_folders: bool = False
    include_user_subscriptions: bool = True
    include_contact_subscriptions: bool = True
    include_contacts_and_contact_groups: bool = False
    import_description: str | None = 'Project Duplication'
    import_default_locale: int | None = 0
    import_locales: list[int] | None = field(default_factory=lambda: [0])

    def __post_init__(self):
        if self.import_default_locale not in self.import_locales:
            raise ValueError("Default locale must be included in the import locales.")

    def _validate_version_specific_properties(self, connection: Connection) -> None:
        """Validate that version-specific properties are not used with
        incompatible server versions.

        Args:
            connection: Strategy One connection object.

        Raises:
            VersionException: If version-specific properties are used with
                incompatible server version.
        """
        incompatible_properties = []
        if self.skip_all_profile_folders:
            incompatible_properties.append('skip_all_profile_folders')
        if self.include_contacts_and_contact_groups:
            incompatible_properties.append('include_contacts_and_contact_groups')

        if incompatible_properties and not is_server_min_version(
            connection, '11.5.0900'
        ):
            if len(incompatible_properties) == 1:
                msg = (
                    f"The property '{incompatible_properties[0]}' requires "
                    "Strategy One version 11.5.0900 or higher. Your environment "
                    f"is running version {connection.iserver_version}. Please "
                    "update your environment to version 11.5.0900 or higher, "
                    "or omit this property from the duplication configuration."
                )
            else:
                properties_str = "', '".join(incompatible_properties)
                msg = (
                    f"The properties '{properties_str}' require Strategy One "
                    "version 11.5.0900 or higher. Your environment is running "
                    f"version {connection.iserver_version}. Please update your "
                    "environment to version 11.5.0900 or higher, or omit these "
                    "properties from the duplication configuration."
                )
            raise VersionException(msg)

    def to_dict(self, connection: Connection | None = None) -> dict:
        """Convert the duplication configuration to a dictionary accepted by
        the API.

        Args:
            connection (Connection, optional): Strategy One connection object
                to validate version-specific properties.

        Returns:
            dict: Dictionary representation of the duplication configuration.
        """
        if connection:
            self._validate_version_specific_properties(connection)

        settings = {
            "export": {
                "projectObjectsPreference": {
                    "schemaObjectsOnly": self.schema_objects_only,
                    "skipEmptyProfileFolders": self.skip_empty_profile_folders,
                    "skipAllProfileFolders": self.skip_all_profile_folders,
                },
                "subscriptionPreferences": {
                    "includeUserSubscriptions": self.include_user_subscriptions,
                    "includeContactSubscriptions": self.include_contact_subscriptions,
                    "includeContactsAndContactGroups": (
                        self.include_contacts_and_contact_groups
                    ),
                },
            },
            "import": {
                "description": self.import_description,
                "defaultLocale": self.import_default_locale,
                "locales": self.import_locales,
            },
        }

        if connection and not is_server_min_version(connection, '11.5.0900'):
            settings["export"]["projectObjectsPreference"].pop(
                "skipAllProfileFolders", None
            )
            settings["export"]["subscriptionPreferences"].pop(
                "includeContactsAndContactGroups", None
            )

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
            skip_all_profile_folders=export_sets.get(
                'project_objects_preference', {}
            ).get('skip_all_profile_folders', False),
            include_user_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_user_subscriptions', True),
            include_contact_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_contact_subscriptions', True),
            include_contacts_and_contact_groups=export_sets.get(
                'subscription_preferences', {}
            ).get('include_contacts_and_contact_groups', False),
            import_description=import_sets.get('description'),
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


@dataclass
class CrossDuplicationConfig(DuplicationConfig):
    """Configuration for cross-environment project duplication.

    Extends `DuplicationConfig` with additional settings for handling
    configuration objects (users, user groups, security roles, etc.)
    during cross-environment duplication.

    Attributes:
        admin_objects_rules (list[AdminObjectRule | dict], optional):
            List of rules for handling conflicts for configuration objects
            during duplication.
        admin_objects (list[Object | str], optional): List of admin objects
            or admin object IDs to be included in the duplication.
        include_all_user_groups (bool, optional): Whether to include all
            user groups in the duplication. Default is False.
        match_by_name (list[ObjectTypes | int], optional): List of object
            types to match by name during import. Currently supported:
            DBLOGIN (30), DBCONNECTION (31), and SECURITY_ROLE (44).
        match_users_by_login (bool, optional): Whether to match users by
            login during import. Default is False.

    Note:
        This class inherits all attributes from `DuplicationConfig`.
    """

    admin_objects_rules: list['AdminObjectRule | dict'] | None = field(default=None)
    admin_objects: list['Object | str'] | None = field(default=None)
    include_all_user_groups: bool = False
    match_by_name: list[ObjectTypes | int] | None = field(default=None)
    match_users_by_login: bool = False

    def to_dict(self, connection: Connection | None = None) -> dict:
        """Convert the cross-duplication configuration to a dictionary
        accepted by the API.

        Args:
            connection (Connection, optional): Strategy One connection object
                to validate version-specific properties.

        Returns:
            dict: Dictionary representation of the duplication configuration.
        """
        body = super().to_dict(connection=connection)

        body['export']['configurationObjects'] = {
            'includeAllUserGroups': self.include_all_user_groups
        }
        body['import']['configurationObjects'] = {
            'matchUsersByLogin': self.match_users_by_login
        }

        if self.match_by_name is not None:
            body['import']['typesMatchByName'] = [
                get_enum_val(item, ObjectTypes) for item in self.match_by_name
            ]

        if self.admin_objects_rules is not None:
            admin_objects_rules = [
                rule.to_dict() if isinstance(rule, AdminObjectRule) else rule
                for rule in self.admin_objects_rules
            ]
            body['export']['configurationObjects'][
                'conflictRules'
            ] = admin_objects_rules
            body['import']['configurationObjects'][
                'conflictRules'
            ] = admin_objects_rules

        if self.admin_objects is not None:
            admin_object_ids = [
                obj.id if isinstance(obj, Object) else obj for obj in self.admin_objects
            ]
            body['export']['configurationObjects']['objects'] = admin_object_ids

        return body

    @classmethod
    def from_dict(cls, source, **kwargs):
        """Create CrossDuplicationConfig from a dictionary.

        Args:
            source (dict): Dictionary with duplication configuration settings.

        Returns:
            CrossDuplicationConfig: Initialized configuration object.
        """
        source = helper.camel_to_snake(source)

        export_sets = source.get('export', {})
        import_sets = source.get('import', {})

        export_config_objs = export_sets.get('configuration_objects', {})
        import_config_objs = import_sets.get('configuration_objects', {})

        admin_objects_rules = None
        raw_rules = export_config_objs.get('conflict_rules')
        if raw_rules is not None:
            admin_objects_rules = [
                AdminObjectRule.from_dict(rule) if isinstance(rule, dict) else rule
                for rule in raw_rules
            ]

        admin_objects = export_config_objs.get('objects')

        return cls(
            schema_objects_only=export_sets.get('project_objects_preference', {}).get(
                'schema_objects_only', True
            ),
            skip_empty_profile_folders=export_sets.get(
                'project_objects_preference', {}
            ).get('skip_empty_profile_folders', True),
            skip_all_profile_folders=export_sets.get(
                'project_objects_preference', {}
            ).get('skip_all_profile_folders', False),
            include_user_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_user_subscriptions', True),
            include_contact_subscriptions=export_sets.get(
                'subscription_preferences', {}
            ).get('include_contact_subscriptions', True),
            include_contacts_and_contact_groups=export_sets.get(
                'subscription_preferences', {}
            ).get('include_contacts_and_contact_groups', False),
            import_description=import_sets.get('description', 'Project Duplication'),
            import_default_locale=import_sets.get('default_locale', 0),
            import_locales=import_sets.get('locales', [0]),
            admin_objects_rules=admin_objects_rules,
            admin_objects=admin_objects,
            include_all_user_groups=export_config_objs.get(
                'include_all_user_groups', False
            ),
            match_by_name=import_sets.get('types_match_by_name'),
            match_users_by_login=import_config_objs.get('match_users_by_login', False),
        )


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


class ProjectDuplication(EntityBase, ChangeJournalMixin, DeleteMixin):
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
        settings (DuplicationConfig | CrossDuplicationConfig): Duplication
            settings. Returns `CrossDuplicationConfig` for cross-environment
            duplications, otherwise `DuplicationConfig`.
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
        'source': ProjectInfo.from_dict,
        'status': ProjectDuplicationStatus,
        'target': ProjectInfo.from_dict,
    }
    _API_DELETE = staticmethod(projects.delete_project_duplication)
    _API_DEL_JOURNAL_MIN_VER = None

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
        source_dict = kwargs.get('source', {})
        target_dict = kwargs.get('target', {})
        self.source = (
            ProjectInfo.from_dict(source_dict) if source_dict else ProjectInfo()
        )
        self.target = (
            ProjectInfo.from_dict(target_dict) if target_dict else ProjectInfo()
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
        self.settings = self._parse_settings(kwargs)

    def _set_object_attributes(self, **kwargs) -> None:
        """Override to convert settings dict to config object."""
        super()._set_object_attributes(**kwargs)
        if isinstance(self.settings, dict):
            self.settings = self._parse_settings(kwargs)

    @staticmethod
    def _parse_settings(
        source: dict,
    ) -> 'DuplicationConfig | CrossDuplicationConfig':
        """Parse settings dictionary into appropriate config object.

        Args:
            source: Full API response dictionary containing source, target,
                and settings keys.

        Returns:
            DuplicationConfig or CrossDuplicationConfig object.
        """
        settings = source.get('settings', {})
        if not settings:
            return DuplicationConfig()

        source_env_id = source.get('source', {}).get('environment', {}).get('id')
        target_env_id = source.get('target', {}).get('environment', {}).get('id')
        is_cross_environment = source_env_id != target_env_id

        if is_cross_environment:
            return CrossDuplicationConfig.from_dict(settings)
        return DuplicationConfig.from_dict(settings)

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

    @method_version_handler('11.5.1200')
    def delete(
        self,
        force: bool = False,
    ) -> bool:
        """Deletes the project duplication record.

        Args:
            force (bool, optional): If True, no additional prompt will be shown
                before deleting the project duplication record.

        Returns:
            True for success. False otherwise.
        """
        return super().delete(force=force)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.id}', "
            f"progress={self.progress}, "
            f"source_project='{self.source.project.get('name')}', "
            f"target_project='{self.target.project.get('name')}')"
        )

    def wait_for_stable_status(
        self, timeout: int = 240, interval: int | None = None
    ) -> 'ProjectDuplication':
        """Wait for the project duplication to reach a stable status.

        Args:
            timeout (int, optional): Maximum time to wait in seconds.
            interval (int, optional): Time between status checks in seconds.
                If not provided, the value is taken from mstrio-py's `config`.

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

    @wip(level=WipLevels.PREVIEW)
    @method_version_handler('11.5.1200')
    def get_backup_package(
        self, save_to_file: bool = True, save_path: str | None = None
    ) -> dict[Literal['filepath', 'file_binary'], str | bytes] | bytes:
        """Download the duplication package binary and optionally save it
        to a file.

        Note:
            Backup package is available only for cross-environment
            duplications on source environment after package is created.

        Args:
            save_to_file: If True, saves the package to a file. If False,
                only returns the binary content. Defaults to True.
            save_path: A directory path where the package binary will be saved.
                If not provided, package will be saved to the current working
                directory. Only used when save_to_file is True.

        Returns:
            If save_to_file is True: Dictionary with 'filepath' and
            'file_binary' keys containing the path to saved file and
            the binary content respectively.
            If save_to_file is False: Binary content of the package.
        """
        response = projects.get_project_duplication_package(self.connection, id=self.id)

        if not save_to_file:
            return response.content

        if not save_path:
            save_path = os.getcwd()

        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            filename = f"duplication_package_{self.id}.projdup"
        filepath = os.path.join(save_path, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        if config.verbose:
            logger.info(f"Duplication package saved to: {filepath}")

        return {"filepath": filepath, "file_binary": response.content}

    @wip(level=WipLevels.PREVIEW)
    @method_version_handler('11.5.1200')
    def restore_package_on_target_environment(
        self,
        target_env: 'Connection | Environment',
    ) -> 'ProjectDuplication':
        """Restore the backup package on the target environment.

        Note:
            This method should be called after the duplication package has been
            created and exported on the source environment. The package will be
            retrieved from the source environment and restored on the target
            environment.

        Args:
            target_env (Connection | Environment): Target environment or
                connection to the target environment.

        Returns:
            ProjectDuplication: Updated project duplication object from the
                target environment.
        """
        from mstrio.server.environment import Environment

        if isinstance(target_env, Environment):
            target_env = target_env.connection

        package = self.get_backup_package(save_to_file=False)

        full_dict = self.to_dict()
        settings = full_dict.get('settings', {})
        target = full_dict.get('target', {})
        target.pop('creator', None)

        metadata_body = {
            'settings': {'import': settings.get('import', {})},
            'target': target,
        }
        resp = projects.trigger_project_restoration_on_target_env(
            target_env, package, metadata_body
        )

        if resp.ok:
            logger.info(
                f"Project duplication package '{self.id}' restoration initiated "
                f"successfully on target environment '{target_env.base_url}'."
            )

        return ProjectDuplication.from_dict(resp.json(), connection=target_env)
