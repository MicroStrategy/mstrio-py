from typing import List, Optional, Union
from mstrio.server.application import Application
from mstrio.server.application import compare_application_settings

from pandas import DataFrame

from mstrio.server.server import ServerSettings
from mstrio.api import monitors
import mstrio.utils.helper as helper


class Environment:
    """Browse and manage Applications on the environment. List loaded
    applications, nodes (servers) and compare application settings on the
    environment. Browse and modify I-Server settings.

    Attributes:
        connection: A MicroStrategy connection object.
        server_settings: Intelligence Server settings object.
    """

    def __init__(self, connection):
        """Initialize Environment object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
        """
        self.connection = connection

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

    def create_application(self, name: str, description: Optional[str] = None,
                           force: bool = False) -> Optional["Application"]:
        """Create a new application on the envrionment.

        Args:
            name: Name of Application.
            description: Description of Aplication.
            force: If `True`, overrides the prompt.
        """
        return Application._create(self.connection, name, description, force)

    def list_applications(self, to_dictionary: bool = False, limit: Optional[int] = None,
                          **filters) -> Union[List["Application"], List[dict]]:
        """Return list of application objects or application dicts if
        `to_dictionary=True`. Optionally filter the Applications by specifying
        the `filters` keyword arguments.

        Args:
            to_dictionary: If True returns list of application dicts.
            limit: limit the number of elements returned. If `None`, all objects
                are returned.
            **filters: Available filter parameters: ['name', 'id',
                'description', 'date_created', 'date_modified', 'owner'].
        """
        return Application._list_applications(
            connection=self.connection,
            to_dictionary=to_dictionary,
            limit=limit,
            **filters,
        )

    def list_loaded_applications(self, to_dictionary: bool = False,
                                 **filters) -> Union[List["Application"], List[dict]]:
        """Return list of all loaded application objects or application dicts
        if `to_dictionary=True` that the user has access to. Optionally filter
        the Applications by specifying the `filters` keyword arguments.

        Args:
            to_dictionary: If True, returns list of application dicts
            **filters: Available filter parameters: ['acg', 'id', 'name',
                'status', 'alias', 'description', 'date_created',
                'date_modified', 'owner']
        """
        return Application._list_loaded_applications(
            connection=self.connection,
            to_dictionary=to_dictionary,
            **filters,
        )

    def list_nodes(self, application_id: Optional[str] = None,
                   node_name: Optional[str] = None) -> List[dict]:
        """Return a list of I-Server nodes and their properties. Optionally
        filter by `application_id` or `node_name`.

        Args:
            application_id: ID of application
            node_name: Name of node
        """
        response = monitors.get_node_info(self.connection, application_id, node_name).json()
        return response['nodes']

    def is_loaded(self, application_id: Optional[str] = None,
                  application_name: Optional[str] = None) -> bool:
        """Check if application is loaded, by passing application ID or name,
        returns True or False.

        Args:
            application_id: Application ID
            application_name: Application name
        """
        if application_id is None and application_name is None:
            helper.exception_handler(
                "Please specify either 'application_name' or 'application_id' argument.")
        if application_id is None:
            app_list = Application._list_application_ids(self.connection, name=application_name)
            if app_list:
                application_id = app_list[0]
            else:
                msg = f"There is no application with the given name: '{application_name}'"
                raise ValueError(msg)

        nodes = self.list_nodes(application_id=application_id)
        loaded = False
        for node in nodes:
            status = node['projects'][0]['status']
            loaded = True if status == 'loaded' else False
            if loaded:
                break
        return loaded

    def compare_settings(self, applications: Union[List[str], List["Application"]] = None,
                         show_diff_only: bool = False) -> DataFrame:
        """Compare application' settings to the first application in the
        provided list.

        Args:
            applications (list of names or application objects, optional): List
                of application objects or names to be compared. First element of
                list is the one to which the rest is compared. If None, all
                applications on the environment will be compared.
            show_diff_only(bool, optional): Whether to display all settings or
                only different from first application in list.

        Returns:
            Dataframe with values of selected application' settings.
        """

        def not_exist_warning(wrong_name):
            helper.exception_handler(
                "Application '{}' does not exist and will be skipped.".format(
                    wrong_name), exception_type=Warning)

        if applications:
            just_objects = [app for app in applications if isinstance(app, Application)]
        else:
            just_objects = []
        if (len(just_objects) == len(applications)):
            return compare_application_settings(applications, show_diff_only)

        all_applications = self.list_applications()
        if type(applications) == list:
            if len(applications) < 2:
                helper.exception_handler(
                    "Provide more than one application object or name in list",
                    exception_type=TypeError)

            # extract app names from either application object or strings
            app_names = [
                app.name if isinstance(app, Application) else str(app) for app in applications
            ]
            # filter only valid applications
            all_app_names = [app.name for app in all_applications]
            [not_exist_warning(a_name) for a_name in app_names if a_name not in all_app_names]

            applications = list(filter(lambda app: app.name in app_names, all_applications))
            applications = sorted(applications, key=lambda x: app_names.index(x.name))

        elif applications is None:
            applications = all_applications
        else:
            helper.exception_handler(
                "The 'applications' parameter needs to be a list of len > 1 or None.",
                exception_type=TypeError)

        return compare_application_settings(applications, show_diff_only)
