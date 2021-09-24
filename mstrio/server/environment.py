from typing import List, Optional, Union
from mstrio.server.project import Project, compare_project_settings

from pandas import DataFrame

from mstrio.server.server import ServerSettings
from mstrio.api import monitors
import mstrio.utils.helper as helper


class Environment:
    """Browse and manage Projects on the environment. List loaded
    projects, nodes (servers) and compare project settings on the
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

    def create_project(self, name: str, description: Optional[str] = None,
                       force: bool = False) -> Optional["Project"]:
        """Create a new project on the envrionment.

        Args:
            name: Name of Project.
            description: Description of Aplication.
            force: If `True`, overrides the prompt.
        """
        return Project._create(self.connection, name, description, force)

    def create_application(self, name: str, description: Optional[str] = None,
                           force: bool = False) -> Optional["Project"]:

        helper.deprecation_warning(
            'create_application function',
            'create_project function',
            '11.3.4.101',  # NOSONAR
            False)
        return self.create_project(name, description, force)

    def list_projects(self, to_dictionary: bool = False, limit: Optional[int] = None,
                      **filters) -> Union[List["Project"], List[dict]]:
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

    def list_applications(self, to_dictionary: bool = False, limit: Optional[int] = None,
                          **filters) -> Union[List["Project"], List[dict]]:
        # Support for deprecation period, to be removed with version 11.3.4.101

        helper.deprecation_warning(
            'list_applications function',
            'list_projects function',
            '11.3.4.101',  # NOSONAR
            False)
        return self.list_projects(to_dictionary, limit, **filters)

    def list_loaded_projects(self, to_dictionary: bool = False,
                             **filters) -> Union[List["Project"], List[dict]]:
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

    def list_loaded_applications(self, to_dictionary: bool = False,
                                 **filters) -> Union[List["Project"], List[dict]]:

        helper.deprecation_warning(
            'list_loaded_applications function',
            'list_loaded_projects function',
            '11.3.4.101',  # NOSONAR
            False)
        return self.list_loaded_projects(to_dictionary, **filters)

    def list_nodes(self, project: Optional[Union[str, "Project"]] = None,
                   node_name: Optional[str] = None,
                   application: Optional[Union[str, "Project"]] = None) -> List[dict]:
        """Return a list of I-Server nodes and their properties. Optionally
        filter by `project` or `node_name`.

        Args:
            project: ID of project or Project object
            application: deprecated. Use project instead.
            node_name: Name of node
        """
        if application:
            helper.deprecation_warning(
                '`application`',
                '`project`',
                '11.3.4.101',  # NOSONAR
                False)
            project = project or application
        project_id = project.id if isinstance(project, Project) else project
        response = monitors.get_node_info(self.connection, project_id, node_name).json()
        return response['nodes']

    def is_loaded(self, project_id: Optional[str] = None, project_name: Optional[str] = None,
                  application_id: Optional[str] = None,
                  application_name: Optional[str] = None) -> bool:
        """Check if project is loaded, by passing project ID or name,
        returns True or False.

        Args:
            project_id: Project ID
            project_name: Project name
            application_id: deprecated. Use project_id instead.
            application_name: deprecated. Use project_name instead.
        """
        if (application_id or application_name):
            helper.deprecation_warning(
                '`application_id` and `application_name`',
                '`project_id` and `project_name`',
                '11.3.4.101',  # NOSONAR
                False)
            project_id = project_id or application_id
            project_name = project_name or application_name

        if project_id is None and project_name is None:
            helper.exception_handler(
                "Please specify either 'project_name' or 'project_id' argument.")
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
            loaded = True if status == 'loaded' else False
            if loaded:
                break
        return loaded

    def compare_settings(self, projects: Union[List[str], List["Project"]] = None,
                         show_diff_only: bool = False,
                         applications: Union[List[str], List["Project"]] = None) -> DataFrame:
        """Compare project' settings to the first project in the
        provided list.

        Args:
            projects (list of names or project objects, optional): List
                of project objects or names to be compared. First element of
                list is the one to which the rest is compared. If None, all
                projects on the environment will be compared.
            applications: deprecated. Use projects instead.
            show_diff_only(bool, optional): Whether to display all settings or
                only different from first project in list.

        Returns:
            Dataframe with values of selected project' settings.
        """
        if applications:
            helper.deprecation_warning(
                '`applications`',
                '`projects`',
                '11.3.4.101',  # NOSONAR
                False)
            projects = projects or applications

        def not_exist_warning(wrong_name):
            helper.exception_handler(
                "Project '{}' does not exist and will be skipped.".format(wrong_name),
                exception_type=Warning)

        if projects:
            just_objects = [project for project in projects if isinstance(project, Project)]
        else:
            just_objects = []
        if (len(just_objects) == len(projects)):
            return compare_project_settings(projects, show_diff_only)

        all_projects = self.list_projects()
        if type(projects) == list:
            if len(projects) < 2:
                helper.exception_handler("Provide more than one project object or name in list",
                                         exception_type=TypeError)

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

            projects = list(filter(lambda project: project.name in project_names, all_projects))
            projects = sorted(projects, key=lambda x: project_names.index(x.name))

        elif projects is None:
            projects = all_projects
        else:
            helper.exception_handler(
                "The 'projects' parameter needs to be a list of len > 1 or None.",
                exception_type=TypeError)

        return compare_project_settings(projects, show_diff_only)
