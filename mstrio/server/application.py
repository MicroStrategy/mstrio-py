from enum import Enum
import time
from typing import List, Optional, TYPE_CHECKING, Union

from pandas import DataFrame, Series
from tqdm import tqdm

from mstrio.api import monitors, projects
import mstrio.config as config
from mstrio.utils.entity import Entity, ObjectTypes
import mstrio.utils.helper as helper
from mstrio.utils.settings import BaseSettings

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ProjectStatus(Enum):
    ACTIVE = 0
    ERRORSTATE = -3
    EXECIDLE = 1
    FULLIDLE = 7
    OFFLINE = -1
    OFFLINEPENDING = -2
    ONLINEPENDING = -4
    REQUESTIDLE = 2
    WHEXECIDLE = 4


def compare_application_settings(applications: List["Application"],
                                 show_diff_only: bool = False) -> DataFrame:
    """Compares settings of application objects.

    Args:
        applications (List[Application]): List of application objects
            to compare.
        show_diff_only (bool, optional): Whether to display all settings
            or only different from first application in list.
    """
    to_be_compared = {}
    df = DataFrame({}, columns=['initial'])

    for app in applications:
        to_be_compared[app.name] = app.settings.to_dataframe().reset_index()
        if df.empty:
            df.columns = ['setting']
            df['setting'] = to_be_compared[app.name]['setting']
        df[app.name] = to_be_compared[app.name]['value']

    if show_diff_only:
        index = Series([True] * len(df['setting']))
        base = applications[0].name
        for app_name in to_be_compared.keys():
            compare = df[base].eq(df[app_name])
            index = compare & index
        df = df[~index]
        if df.empty and config.verbose:
            app_names = list(to_be_compared.keys())
            app_names.remove(base)
            print((f"There is no difference in settings between application '{base}' and "
                   f"remaining applications: '{app_names}'"))
    return df


class Application(Entity):
    """Object representation of MicroStrategy Application (Project) object.

    Attributes:
        connection: A MicroStrategy connection object
        settings: Application settings object
        id: Application ID
        name: Application name
        description: Application description
        alias: Application alias
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        nodes: List of nodes on which application is loaded
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd
        version: Version ID
        owner: owner ID and name
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        status: Application
        ancestors: List of ancestor folders
    """
    _PATCH_PATH_TYPES = {'name': str, 'description': str}
    _IDLE_MODE_DICT = {
        'REQUEST': 'request_idle',
        'EXECUTION': 'exec_idle',
        'WAREHOUSEEXEC': 'wh_exec_idle',
        'PARTIAL': 'partial_idle',
        'FULL': 'full_idle',
    }
    _OBJECT_TYPE = ObjectTypes.APPLICATION
    _API_GETTERS = {
        **Entity._API_GETTERS, ('status', 'alias'): projects.get_project,
        'nodes': monitors.get_node_info
    }
    _FROM_DICT_MAP = {'type': ObjectTypes, 'status': ProjectStatus}

    def __init__(self, connection: "Connection", name: str = None, id: str = None) -> None:
        """Initialize Application object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: Application name
            id: Application ID
        """

        # initialize either by ID or Application Name
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.")

        if id is None:
            app_list = Application._list_application_ids(connection, name=name)
            if app_list:
                id = app_list[0]
            elif app_list == []:
                app_loaded_list = Application._list_loaded_applications(
                    connection, to_dictionary=True, name=name)
                try:
                    id = app_loaded_list[0]['id']
                except IndexError:
                    helper.exception_handler(
                        "There is no application with the given name: '{}'".format(name),
                        exception_type=ValueError)

        super().__init__(connection=connection, object_id=id, name=name)

        if not self.is_loaded():
            helper.exception_handler(("Some applications are either unloaded or idled. Change "
                                      "status using the 'load()' or 'resume()' method to use "
                                      "all functionality."), exception_type=UserWarning)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._status = kwargs.get("status")
        self._alias = kwargs.get("alias")
        self._nodes = kwargs.get("nodes")

    @classmethod
    def _create(cls, connection: "Connection", name: str, description: str = None,
                force: bool = False) -> Optional["Application"]:
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to create new application '{}'? [Y/N]: ".format(name))

        if force or user_input == 'Y':
            # Create new application
            with tqdm(desc="Please wait while Application '{}' is being created.".format(name),
                      bar_format='{desc}', leave=False, disable=config.verbose):
                response = projects.create_project(connection, {
                    "name": name,
                    "description": description
                })
                http_status, i_server_status = 500, 'ERR001'
                while http_status == 500 and i_server_status == 'ERR001':
                    time.sleep(1)
                    response = projects.get_project(connection, name, whitelist=[('ERR001', 500)])
                    http_status = response.status_code
                    i_server_status = response.json().get('code')
                    id = response.json().get('id')
            if config.verbose:
                print("Application '{}' successfully created.".format(name))
            return cls(connection, name=name, id=id)
        else:
            return None

    @classmethod
    def _list_applications(cls, connection: "Connection", to_dictionary: bool = False,
                           limit: int = None, **filters) -> Union[List["Application"], List[dict]]:
        msg = "Error getting information for a set of Applications."
        objects = helper.fetch_objects_async(
            connection,
            monitors.get_projects,
            monitors.get_projects_async,
            dict_unpack_value='projects',
            limit=limit,
            chunk_size=50,
            error_msg=msg,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            apps = [cls.from_dict(source=obj, connection=connection) for obj in objects]
            apps_loaded = Application._list_loaded_applications(connection, to_dictionary=True)
            apps_loaded_ids = [app['id'] for app in apps_loaded]
            unloaded = [app for app in apps if app.id not in apps_loaded_ids]

            if unloaded:
                msg = (f"Applications {[app.name for app in unloaded]} are either unloaded or "
                       "idled. Change status using the 'load()' or 'resume()' method to use all "
                       "functionality.")
                helper.exception_handler(msg, exception_type=UserWarning)
            return apps

    @classmethod
    def _list_application_ids(cls, connection: "Connection", limit: int = None,
                              **filters) -> List[str]:
        application_dicts = Application._list_applications(
            connection=connection,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [app['id'] for app in application_dicts]

    @classmethod
    def _list_loaded_applications(cls, connection: "Connection", to_dictionary: bool = False,
                                  **filters) -> Union[List["Application"], List[dict]]:
        response = projects.get_projects(connection, whitelist=[('ERR014', 403)])
        list_of_dicts = response.json() if response.ok else []
        list_of_dicts = helper.camel_to_snake(list_of_dicts)  # Convert keys
        raw_applications = helper.filter_list_of_dicts(list_of_dicts, **filters)

        if to_dictionary:
            # return list of application names
            return raw_applications
        else:
            # return list of Application objects
            return [cls.from_dict(source=obj, connection=connection) for obj in raw_applications]

    def alter(self, name: str = None, description: str = None):
        """Alter application name or/and description.

        Args:
            name: new name of the application.
            description: new description of the application.
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

    def idle(self, on_nodes: Union[str, List[str]] = None, mode: str = "REQUEST") -> None:
        """Request to idle a specific cluster node. Idle application with mode
        options for `REQUEST`, `EXECUTION`, `WAREHOUSEEXEC`, `PARTIAL`, `FULL`.

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

        Args:
            on_nodes: Name of node, if not passed, application will be idled on
                all of the nodes.
            mode: One of: `REQUEST`, `EXECUTION`,`WAREHOUSEEXEC`, `PARTIAL`,
                `FULL`.
        """
        msg = ("Unsupported mode, choose one of: 'REQUEST', 'EXECUTION', 'WAREHOUSEEXEC', "
               "'PARTIAL', 'FULL'")
        if mode not in Application._IDLE_MODE_DICT.keys():
            helper.exception_handler(msg, KeyError)

        def idle_app(node, mode):
            formatted_mode = Application._IDLE_MODE_DICT.get(mode)
            body = {
                "operationList": [{
                    "op": "replace",
                    "path": "/status",
                    "value": formatted_mode
                }]
            }
            response = monitors.update_node_properties(self.connection, node, self.id, body)
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != formatted_mode:
                    self.fetch('nodes')
                if config.verbose:
                    print("Application '{}' changed status to '{}' on node '{}'.".format(
                        self.id, mode, node))

        if type(on_nodes) is list:
            for node in on_nodes:
                idle_app(node, mode)
        elif type(on_nodes) is str:
            idle_app(on_nodes, mode)
        elif on_nodes is None:
            for node in self.nodes:
                idle_app(node.get('name'), mode)  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list, str, NoneType]",
                exception_type=TypeError)

    def resume(self, on_nodes: Union[str, List[str]] = None) -> None:
        """Request to resume the application on the chosen cluster nodes. If
        nodes are not specified, the application will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, application will be resumed
                on all of the nodes.
        """

        def resume_app(node):
            body = {"operationList": [{"op": "replace", "path": "/status", "value": "loaded"}]}
            response = monitors.update_node_properties(self.connection, node, self.id, body)
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'loaded':
                    self.fetch('nodes')
                if config.verbose:
                    print("Application '{}' resumed on node '{}'.".format(self.id, node))

        if type(on_nodes) is list:
            for node in on_nodes:
                resume_app(node)
        elif type(on_nodes) is str:
            resume_app(on_nodes)
        elif on_nodes is None:
            for node in self.nodes:
                resume_app(node.get('name'))  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list, str, NoneType]",
                exception_type=TypeError)

    def load(self, on_nodes: Union[str, List[str]] = None) -> None:
        """Request to load the application onto the chosen cluster nodes. If
        nodes are not specified, the application will be loaded on all nodes.

        Args:
            on_nodes: Name of node, if not passed, application will be loaded
                on all of the nodes.
        """

        def load_app(node):
            body = {"operationList": [{"op": "replace", "path": "/status", "value": "loaded"}]}
            response = monitors.update_node_properties(self.connection, node, self.id, body)
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'loaded':
                    self.fetch('nodes')
                if config.verbose:
                    print("Application '{}' loaded on node '{}'.".format(self.id, node))

        if type(on_nodes) is list:
            for node in on_nodes:
                load_app(node)
        elif type(on_nodes) is str:
            load_app(on_nodes)
        elif on_nodes is None:
            for node in self.nodes:
                load_app(node.get('name'))  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list, str, NoneType]",
                exception_type=TypeError)

    def unload(self, on_nodes: Union[str, List[str]] = None) -> None:
        """Request to unload the application from the chosen cluster nodes. If
        nodes are not specified, the application will be unloaded on all nodes.
        The unload action cannot be performed until all jobs and connections
        for application are completed. Once these processes have finished,
        pending application will be automatically unloaded.

        Args:
            on_nodes: Name of node, if not passed, application will be unloaded
                on all of the nodes.
        """

        def unload_app(node):
            body = {"operationList": [{"op": "replace", "path": "/status", "value": "unloaded"}]}
            response = monitors.update_node_properties(self.connection, node, self.id, body,
                                                       whitelist=[('ERR001', 500)])
            if response.status_code == 202:
                tmp = helper.filter_list_of_dicts(self.nodes, name=node)
                tmp[0]['projects'] = [response.json()['project']]
                self._nodes = tmp
                if tmp[0]['projects'][0]['status'] != 'unloaded':
                    self.fetch('nodes')
                if config.verbose:
                    print("Application '{}' unloaded on node '{}'.".format(self.id, node))
            if response.status_code == 500 and config.verbose:  # handle whitelisted
                print("Application '{}' already unloaded on node '{}'.".format(self.id, node))

        if type(on_nodes) is list:
            for node in on_nodes:
                unload_app(node)
        elif type(on_nodes) is str:
            unload_app(on_nodes)
        elif on_nodes is None:
            for node in self.nodes:
                unload_app(node.get('name'))  # type: ignore
        else:
            helper.exception_handler(
                "'on_nodes' argument needs to be of type: [list, str, NoneType]",
                exception_type=TypeError)

    def register(self, on_nodes: Union[str, list] = None) -> None:
        """Register application on nodes.

        A registered project will load on node (server) startup.

        Args:
            on_nodes: Name of node, if not passed, application will be loaded
                on all available nodes on startup.
        """
        if on_nodes is None:
            value = [node['name'] for node in self.nodes]
        else:
            on_nodes = on_nodes if isinstance(on_nodes, list) else [on_nodes]
            value = list(set(self.load_on_startup) | set(on_nodes))
        self._register(on_nodes=value)

    def unregister(self, on_nodes: Union[str, list] = None) -> None:
        """Unregister application on nodes.

        An unregistered application will not load on node (server) startup.

        Args:
            on_nodes (str or list, optional): Name of node, if not passed,
                application will not be loaded on any nodes on startup.
        """
        if on_nodes is None:
            value = []
        else:
            on_nodes = on_nodes if isinstance(on_nodes, list) else [on_nodes]
            value = list(set(self.load_on_startup) - set(on_nodes))
        self._register(on_nodes=value)

    def update_settings(self) -> None:
        """Update the current application settings on the I-Server."""
        self.settings.update(self.id)

    def fetch_settings(self) -> None:
        """Fetch the current application settings from the I-Server."""
        self.settings.fetch(self.id)

    def is_loaded(self) -> bool:
        """Check if the application is loaded on any node (server)."""
        loaded = False
        self.fetch('nodes')
        if not isinstance(self.nodes, list):
            helper.exception_handler("Could not retrieve current application status.",
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
        path = "/projects/{}/nodes".format(self.id)
        body = {"operationList": [{"op": "replace", "path": path, "value": on_nodes}]}
        projects.update_projects_on_startup(self.connection, body)
        if config.verbose:
            if on_nodes:
                print("Application will load on startup of: {}".format(on_nodes))
            else:
                print("Application will not load on startup")

    @property
    def load_on_startup(self):
        """View nodes (servers) to load application on startup."""
        response = projects.get_projects_on_startup(self.connection).json()
        return response['projects'][self.id]['nodes']

    @property
    def settings(self) -> "ApplicationSettings":
        """`Settings` object storing Application settings.

        Settings can be listed by using `list_properties()` method.
        Settings can be modified directly by setting the values in the
        object.
        """

        if not hasattr(self, "_settings"):
            super(Entity, self).__setattr__("_settings",
                                            ApplicationSettings(self.connection, self.id))
        return self._settings

    @settings.setter
    def settings(self, settings: "ApplicationSettings") -> None:
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


class ApplicationSettings(BaseSettings):
    """Object representation of MicroStrategy Application (Project) Settings.

    Used to fetch, view, modify, update, export to file, import from file and
    validate Application settings.

    The object can be optionally initialized with `connection` and
    `application_id`, which will automatically fetch the current settings for
    the specified application. If not specified, settings can be loaded from
    file using `import_from()` method. Object attributes (representing settings)
    can be modified manually. Lastly, the object can be applied to any
    application using the `update()` method.

    Attributes:
        connection: A MicroStrategy connection object
    """

    _TYPE = "allProjectSettings"
    _CONVERTION_DICT = {
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

    def __init__(self, connection: "Connection", application_id: str = None):
        """Initialize `ApplicationSettings` object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            application_id: Application ID
        """
        super(BaseSettings, self).__setattr__('_connection', connection)
        super(BaseSettings, self).__setattr__('_application_id', application_id)
        self._configure_settings()

        if application_id:
            self.fetch()

    def fetch(self, application_id: str = None) -> None:
        """Fetch current application settings from I-Server and update this
        `ApplicationSettings` object.

        Args:
            application_id: Application ID
        """
        self._check_params(application_id)
        super(ApplicationSettings, self).fetch()

    def update(self, application_id: str = None) -> None:
        """Update the current application settings on I-Server using this
        Settings object.

        Args:
            application_id: Application ID
        """
        self._check_params(application_id)
        set_dict = self._prepare_settings_push()
        response = projects.update_project_settings(self._connection, self._application_id,
                                                    set_dict)
        if response.status_code == 204 and config.verbose:
            print("Application settings updated.")

    def _fetch(self) -> dict:
        response = projects.get_project_settings(self._connection, self._application_id,
                                                 whitelist=[('ERR001', 404)])
        settings = response.json() if response.ok else {}
        if not response.ok:
            msg = ("Settings could not be fetched. It may be because the application is not "
                   "loaded in the Intelligence Server or the application is idle.")
            helper.exception_handler(msg, Warning)
        return self._prepare_settings_fetch(settings)

    def _get_config(self):
        if not ApplicationSettings._CONFIG:
            app_id = self._application_id
            if not app_id:
                app_id = Application._list_loaded_applications(self._connection,
                                                               to_dictionary=True)['id'][0]
            response = projects.get_project_settings_config(self._connection, app_id)
            ApplicationSettings._CONFIG = response.json()

    def _check_params(self, application_id=None):
        if application_id:
            super(BaseSettings, self).__setattr__('_application_id', application_id)
        if not self._connection or not self._application_id:
            raise AttributeError("Please provide `connection` and `application_id` parameter")
