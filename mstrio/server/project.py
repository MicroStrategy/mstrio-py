from enum import Enum, IntEnum
import logging
import time
from typing import List, Optional, Union

from pandas import DataFrame, Series
from tqdm import tqdm

from mstrio import config
from mstrio.api import monitors, projects
from mstrio.connection import Connection
from mstrio.utils.entity import Entity, ObjectTypes
import mstrio.utils.helper as helper
from mstrio.utils.settings.base_settings import BaseSettings


logger = logging.getLogger(__name__)


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


class IdleMode(Enum):
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


def compare_project_settings(projects: List["Project"], show_diff_only: bool = False) -> DataFrame:
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
            msg = (f"There is no difference in settings between project '{base}' and "
                   f"remaining projects: '{project_names}'")
            logger.info(msg)
    return df


class Project(Entity):
    """Object representation of MicroStrategy Project (Project) object.

    Attributes:
        connection: A MicroStrategy connection object
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
    """
    _OBJECT_TYPE = ObjectTypes.PROJECT
    _API_GETTERS = {
        **Entity._API_GETTERS, ('status', 'alias'): projects.get_project,
        'nodes': monitors.get_node_info
    }
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'status': ProjectStatus}
    _STATUS_PATH = "/status"
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, name: Optional[str] = None,
                 id: Optional[str] = None) -> None:
        """Initialize Project object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: Project name
            id: Project ID
        """

        # initialize either by ID or Project Name
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.")

        if id is None:
            project_list = Project._list_project_ids(connection, name=name)
            if project_list:
                id = project_list[0]
            elif project_list == []:
                project_loaded_list = Project._list_loaded_projects(connection, to_dictionary=True,
                                                                    name=name)
                try:
                    id = project_loaded_list[0]['id']
                except IndexError:
                    helper.exception_handler(
                        f"There is no project with the given name: '{name}'",
                        exception_type=ValueError)

        super().__init__(connection=connection, object_id=id, name=name)

        if not self.is_loaded():
            helper.exception_handler(("Some projects are either unloaded or idled. Change "
                                      "status using the 'load()' or 'resume()' method to use "
                                      "all functionality."), exception_type=UserWarning)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._status = kwargs.get("status")
        self._alias = kwargs.get("alias")
        self._nodes = kwargs.get("nodes")

    @classmethod
    def _create(cls, connection: Connection, name: str, description: Optional[str] = None,
                force: bool = False) -> Optional["Project"]:
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to create new project '{name}'? [Y/N]: ")

        if force or user_input == 'Y':
            # Create new project
            with tqdm(desc=f"Please wait while Project '{name}' is being created.",
                      bar_format='{desc}', leave=False, disable=config.verbose):
                projects.create_project(connection, {"name": name, "description": description})
                http_status, i_server_status = 500, 'ERR001'
                while http_status == 500 and i_server_status == 'ERR001':
                    time.sleep(1)
                    response = projects.get_project(connection, name, whitelist=[('ERR001', 500)])
                    http_status = response.status_code
                    i_server_status = response.json().get('code')
                    id_ = response.json().get('id')
            if config.verbose:
                logger.info(f"Project '{name}' successfully created.")
            return cls(connection, name=name, id=id_)
        else:
            return None

    @classmethod
    def _list_projects(cls, connection: Connection, to_dictionary: bool = False,
                       limit: Optional[int] = None,
                       **filters) -> Union[List["Project"], List[dict]]:
        msg = "Error getting information for a set of Projects."
        objects = helper.fetch_objects_async(connection, monitors.get_projects,
                                             monitors.get_projects_async,
                                             dict_unpack_value='projects', limit=limit,
                                             chunk_size=50, error_msg=msg, filters=filters)
        if to_dictionary:
            return objects
        else:
            projects = [cls.from_dict(source=obj, connection=connection) for obj in objects]
            projects_loaded = Project._list_loaded_projects(connection, to_dictionary=True)
            projects_loaded_ids = [project['id'] for project in projects_loaded]
            unloaded = [project for project in projects if project.id not in projects_loaded_ids]

            if unloaded:
                msg = (f"Projects {[project.name for project in unloaded]} are either unloaded or "
                       "idled. Change status using the 'load()' or 'resume()' method to use all "
                       "functionality.")
                helper.exception_handler(msg, exception_type=UserWarning)
            return projects

    @classmethod
    def _list_project_ids(cls, connection: Connection, limit: Optional[int] = None,
                          **filters) -> List[str]:
        project_dicts = Project._list_projects(
            connection=connection,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [project['id'] for project in project_dicts]

    @classmethod
    def _list_loaded_projects(cls, connection: Connection, to_dictionary: bool = False,
                              **filters) -> Union[List["Project"], List[dict]]:
        response = projects.get_projects(connection, whitelist=[('ERR014', 403)])
        list_of_dicts = response.json() if response.ok else []
        list_of_dicts = helper.camel_to_snake(list_of_dicts)  # Convert keys
        raw_project = helper.filter_list_of_dicts(list_of_dicts, **filters)

        if to_dictionary:
            # return list of project names
            return raw_project
        else:
            # return list of Project objects
            return [cls.from_dict(source=obj, connection=connection) for obj in raw_project]

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter project name or/and description.

        Args:
            name: new name of the project.
            description: new description of the project.
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        self._alter_properties(**properties)

    def __change_project_state(self, func, on_nodes: Union[str, List[str]] = None, **mode):
        if type(on_nodes) is list:
            for node in on_nodes:
                func(node, **mode)
        elif type(on_nodes) is str:
            func(on_nodes, **mode)
        elif on_nodes is None:
            for node in self.nodes:
                func(node.get('name'), **mode)  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list[str], str, NoneType]",
                exception_type=TypeError)

    def idle(self, on_nodes: Optional[Union[str, List[str]]] = None,
             mode: Union[IdleMode, str] = IdleMode.REQUEST) -> None:
        """Request to idle a specific cluster node. Idle project with mode
        options.

        Args:
            on_nodes: Name of node, if not passed, project will be idled on
                all of the nodes.
            mode: One of: `IdleMode` values.
        """

        def idle_project(node: str, mode: IdleMode):
            body = {
                "operationList": [{
                    "op": "replace",
                    "path": self._STATUS_PATH,
                    "value": mode.value
                }]
            }
            response = monitors.update_node_properties(self.connection, node, self.id, body)
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != mode.value:
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(
                        f"Project '{self.id}' changed status to '{mode}' on node '{node}'."
                    )

        if not isinstance(mode, IdleMode):
            # Previously `mode` was just a string with possible values
            # corresponding to the member names of the current IdleMode enum.
            # This attempts to convert it to avoid breaking backwards compat.
            if mode in IdleMode.__members__.values():
                mode = IdleMode(mode)
            elif mode in IdleMode.__members__.keys():
                mode = IdleMode[mode]
            else:
                helper.exception_handler(
                    "Unsupported mode, please provide a valid `IdleMode` value.", KeyError)

        self.__change_project_state(func=idle_project, on_nodes=on_nodes, mode=mode)

    def resume(self, on_nodes: Optional[Union[str, List[str]]] = None) -> None:
        """Request to resume the project on the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, project will be resumed
                on all of the nodes.
        """

        def resume_project(node):
            body = {
                "operationList": [{
                    "op": "replace",
                    "path": self._STATUS_PATH,
                    "value": "loaded"
                }]
            }
            response = monitors.update_node_properties(self.connection, node, self.id, body)
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'loaded':
                    self.fetch('nodes')
                if config.verbose:
                    logger.info(f"Project '{self.id}' resumed on node '{node}'.")

        self.__change_project_state(func=resume_project, on_nodes=on_nodes)

    def load(self, on_nodes: Optional[Union[str, List[str]]] = None) -> None:
        """Request to load the project onto the chosen cluster nodes. If
        nodes are not specified, the project will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, project will be loaded
                on all of the nodes.
        """

        def load_project(node):
            body = {
                "operationList": [{
                    "op": "replace",
                    "path": self._STATUS_PATH,
                    "value": "loaded"
                }]
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

        self.__change_project_state(func=load_project, on_nodes=on_nodes)

    def unload(self, on_nodes: Optional[Union[str, List[str]]] = None) -> None:
        """Request to unload the project from the chosen cluster nodes. If
        nodes are not specified, the project will be unloaded on all nodes.
        The unload action cannot be performed until all jobs and connections
        for project are completed. Once these processes have finished,
        pending project will be automatically unloaded.

        Args:
            on_nodes: Name of node, if not passed, project will be unloaded
                on all of the nodes.
        """

        def unload_project(node):
            body = {
                "operationList": [{
                    "op": "replace",
                    "path": self._STATUS_PATH,
                    "value": "unloaded"
                }]
            }
            response = monitors.update_node_properties(self.connection, node, self.id, body,
                                                       whitelist=[('ERR001', 500)])
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

        self.__change_project_state(func=unload_project, on_nodes=on_nodes)

    def register(self, on_nodes: Optional[Union[str, list]] = None) -> None:
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

    def unregister(self, on_nodes: Optional[Union[str, list]] = None) -> None:
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

    def fetch_settings(self) -> None:
        """Fetch the current project settings from the I-Server."""
        self.settings.fetch(self.id)

    def is_loaded(self) -> bool:
        """Check if the project is loaded on any node (server)."""
        loaded = False
        self.fetch('nodes')
        if not isinstance(self.nodes, list):
            helper.exception_handler("Could not retrieve current project status.",
                                     exception_type=ConnectionError)
        for node in self.nodes:
            projects = node.get('projects')
            if projects:
                status = projects[0].get('status')
                loaded = True if status == 'loaded' else False
                if loaded:
                    break
        return loaded

    def _register(self, on_nodes: Union[list]) -> None:
        path = f"/projects/{self.id}/nodes"
        body = {"operationList": [{"op": "replace", "path": path, "value": on_nodes}]}
        projects.update_projects_on_startup(self.connection, body)
        if config.verbose:
            if on_nodes:
                logger.info(f'Project will load on startup of: {on_nodes}')
            else:
                logger.warning('Project will not load on startup.')

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
            super(Entity, self).__setattr__("_settings", ProjectSettings(self.connection, self.id))
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


class ProjectSettings(BaseSettings):
    """Object representation of MicroStrategy Project (Project) Settings.

    Used to fetch, view, modify, update, export to file, import from file and
    validate Project settings.

    The object can be optionally initialized with `connection` and
    `project_id`, which will automatically fetch the current settings for
    the specified project. If not specified, settings can be loaded from
    file using `import_from()` method. Object attributes (representing settings)
    can be modified manually. Lastly, the object can be applied to any
    project using the `update()` method.

    Attributes:
        connection: A MicroStrategy connection object
    """

    _TYPE = "allProjectSettings"
    _CONVERSION_MAP = {
        'maxCubeSizeForDownload': 'B',
        'maxDataUploadSize': 'B',
        'maxMstrFileSize': 'B',
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
        'cubeIndexGrowthUpperBound': '%'
    }

    def __init__(self, connection: Connection, project_id: Optional[str] = None):
        """Initialize `ProjectSettings` object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            project_id: Project ID
        """
        super(BaseSettings, self).__setattr__('_connection', connection)
        super(BaseSettings, self).__setattr__('_project_id', project_id)
        self._configure_settings()

        if project_id:
            self.fetch()

    def fetch(self, project_id: Optional[str] = None) -> None:
        """Fetch current project settings from I-Server and update this
        `ProjectSettings` object.

        Args:
            project_id: Project ID
        """
        self._check_params(project_id)
        super().fetch()

    def update(self, project_id: Optional[str] = None) -> None:
        """Update the current project settings on I-Server using this
        Settings object.

        Args:
            project_id: Project ID
        """
        self._check_params(project_id)
        set_dict = self._prepare_settings_push()
        response = projects.update_project_settings(self._connection, self._project_id, set_dict)
        if config.verbose:
            if response.status_code == 200:
                logger.info('Project settings updated.')
            elif response.status_code == 207:
                partial_succ = response.json()
                logging.info(f'Project settings partially successful.\n{partial_succ}')

    def _fetch(self) -> dict:
        response = projects.get_project_settings(self._connection, self._project_id,
                                                 whitelist=[('ERR001', 404)])
        settings = response.json() if response.ok else {}
        if not response.ok:
            msg = ("Settings could not be fetched. It may be because the project is not "
                   "loaded in the Intelligence Server or the project is idle.")
            helper.exception_handler(msg, Warning)
        return self._prepare_settings_fetch(settings)

    def _get_config(self):
        if not ProjectSettings._CONFIG:
            project_id = self._project_id
            if not project_id:
                project_id = Project._list_loaded_projects(self._connection,
                                                           to_dictionary=True)['id'][0]
            response = projects.get_project_settings_config(self._connection, project_id)
            ProjectSettings._CONFIG = response.json()
            super()._get_config()

    def _check_params(self, project_id: Optional[str] = None):
        if project_id:
            super(BaseSettings, self).__setattr__('_project_id', project_id)
        if not self._connection or not self._project_id:
            raise AttributeError("Please provide `connection` and `project_id` parameter")
