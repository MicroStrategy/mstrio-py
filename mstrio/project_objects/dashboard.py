import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pandas import DataFrame, concat

from mstrio import config
from mstrio.api import documents
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.object_management import Folder, SearchPattern, search_operations
from mstrio.project_objects.document import Document
from mstrio.server.environment import Environment
from mstrio.types import ObjectSubTypes
from mstrio.users_and_groups import UserOrGroup
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.cache import CacheSource
from mstrio.utils.helper import Dictable, is_dashboard
from mstrio.utils.related_subscription_mixin import RelatedSubscriptionMixin
from mstrio.utils.resolvers import (
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)

if TYPE_CHECKING:
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


def list_dashboards(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> list["Dashboard"] | list[dict] | DataFrame:
    """Get all Dashboards stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): Strategy One connection object returned
            by 'connection.Connection()'
        name: characters that the dashboard name must contain
        to_dictionary(bool, optional): if True, return Dashboards as
            list of dicts
        to_dataframe(bool, optional): if True, return Dashboards as
            pandas DataFrame
        limit(int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of dashboards or list of dictionaries or DataFrame object
    """

    return Dashboard._list_all(
        connection,
        to_dictionary=to_dictionary,
        name=name,
        limit=limit,
        to_dataframe=to_dataframe,
        project=project,
        project_id=project_id,
        project_name=project_name,
        folder=folder,
        folder_id=folder_id,
        folder_name=folder_name,
        folder_path=folder_path,
        **filters,
    )


def list_dashboards_across_projects(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
) -> list["Dashboard"] | list[dict] | DataFrame:
    """Get all Dashboards stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): Strategy One connection object returned
            by 'connection.Connection()'
        name: characters that the dashboard name must contain
        to_dictionary(bool, optional): if True, return Dashboards as
            list of dicts
        to_dataframe(bool, optional): if True, return Dashboards as
            pandas DataFrame
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
        List of dashboards or list of dictionaries or DataFrame object
    """
    project_id_before = connection.project_id
    env = Environment(connection)
    projects = env.list_projects()
    output = DataFrame() if to_dataframe else []
    for project in projects:
        try:
            connection.select_project(project_id=project.id)
        except ValueError:
            if config.verbose:
                logger.info(
                    f'Project {project.name} ({project.id}) is skipped '
                    f'because it does not exist or user has no access '
                    f'to it'
                )
            continue
        try:
            dashboards = Dashboard._list_all(
                connection,
                to_dictionary=to_dictionary,
                name=name,
                limit=limit,
                to_dataframe=to_dataframe,
                **filters,
            )

            if to_dataframe:
                output = concat([output, dashboards], ignore_index=True)
            else:
                output.extend(dashboards)
        except IServerError as e:
            if config.verbose:
                logger.info(f'Project {project.name} ({project.id}) is skipped - {e}')
            continue

    connection.select_project(project_id=project_id_before)
    return output[:limit]


class Dashboard(Document, RelatedSubscriptionMixin):
    _CACHE_TYPE = CacheSource.Type.DASHBOARD

    _API_GETTERS = {
        **Document._API_GETTERS,
        ('chapters', 'current_chapter'): documents.get_dashboard_hierarchy,
    }
    _FROM_DICT_MAP = {
        **Document._FROM_DICT_MAP,
        'chapters': (
            lambda source, connection: [
                DashboardChapter.from_dict(content, connection) for content in source
            ]
        ),
    }

    def __init__(
        self,
        connection: Connection,
        name: str | None = None,
        id: str | None = None,
    ):
        """Initialize Dashboard object by passing name or id.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Dashboard
            id (string, optional): ID of Dashboard
        """
        super().__init__(connection=connection, name=name, id=id)

    def _init_variables(self, default_value, **kwargs):
        super()._init_variables(default_value=default_value, **kwargs)
        self._current_chapter = kwargs.get('current_chapter', default_value)
        self._chapters = kwargs.get('chapters', default_value)

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
        name: str | None = None,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        folder: 'Folder | tuple[str] | list[str] | str | None' = None,
        folder_id: str | None = None,
        folder_name: str | None = None,
        folder_path: tuple[str] | list[str] | str | None = None,
        **filters,
    ) -> list["Dashboard"] | list[dict] | DataFrame:
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either to_dictionary=True or to_dataframe=True, but not "
                "both.",
                ValueError,
            )

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )

        validate_owner_key_in_filters(filters)

        objects = search_operations.full_search(
            connection,
            object_types=ObjectSubTypes.REPORT_WRITING_DOCUMENT,
            project=proj_id,
            name=name,
            pattern=search_pattern,
            root=folder,
            root_id=folder_id,
            root_name=folder_name,
            root_path=folder_path,
            **filters,
        )
        dashboards = [obj for obj in objects if is_dashboard(obj['view_media'])]
        dashboards = dashboards[:limit]

        if to_dictionary:
            return dashboards
        elif to_dataframe:
            return DataFrame(dashboards)
        else:
            return [
                cls.from_dict(
                    source=dashboard, connection=connection, with_missing_value=True
                )
                for dashboard in dashboards
            ]

    def list_properties(self) -> dict:
        """List properties for the dashboard."""
        properties = super().list_properties()
        additional_values = {
            'chapters': self.chapters,
            'current_chapter': self.current_chapter,
        }
        properties.update(additional_values)
        return properties

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        folder_id: Folder | str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ):
        """Alter Dashboard's basic properties.

        Args:
            name (string, optional): new name of the Dashboard
            description (string, optional): new description of the Dashboard
            folder_id (string | Folder, optional): A globally unique identifier
                used to distinguish between metadata objects within the same
                project. It is possible for two metadata objects in different
                projects to have the same Object Id.
            hidden (bool, optional): specifies whether the dashboard is hidden
            comments (str, optional): long description of the dashboard
            owner: (str | User, optional): owner of the dashboard
        """
        super().alter(name, description, folder_id, hidden, comments, owner)

    def publish(self, recipients: UserOrGroup | list[UserOrGroup] | None = None):
        """Publish the dashboard for authenticated user. If `recipients`
        parameter is specified publishes the dashboard for the given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the dashboard to (can be a list of IDs
                or a list of User and UserGroup elements)
        """
        super().publish(recipients)

    def unpublish(self, recipients: UserOrGroup | list[UserOrGroup] | None = None):
        """Unpublish the dashboard for all users it was previously published to.
        If `recipients` parameter is specified unpublishes the dashboard for the
        given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the dashboard to (can be a list of IDs
                or a list of User and UserGroup elements)
        """
        super().unpublish(recipients)

    def share_to(self, users: UserOrGroup | list[UserOrGroup]):
        """Shares the dashboard to the listed users' libraries.

        Args:
            users(UserOrGroup | list[UserOrGroup]): list of users or user
                groups to publish the dashboard to (can be a list of IDs or a
                list of User and UserGroup elements).
        """
        self.publish(users)

    @property
    def chapters(self) -> list["DashboardChapter"]:
        return self._chapters

    @property
    def current_chapter(self) -> str:
        return self._current_chapter


@dataclass
class VisualizationSelector(Dictable):
    """Object that describes a Visualization Selector

    Attributes:
        visualization_key (string): key/id of the selector
        selector_type (string): type of the selector
        current_selection (dict): current selection of the selector
        targets (list[dict], optional): list of the selector's targets"""

    visualization_key: str
    selector_type: str
    current_selection: dict
    targets: list[dict] | None = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of visualization selector."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class PageSelector(Dictable):
    """Object that describes a Page Selector

    Attributes:
        key (string): key/id of the selector
        selector_type (string): type of the selector
        current_selection (dict): current selection of the selector
        source (dict, optional): source of the selector
        multi_selection_allowed (bool): whether multi selection is allowed,
            defaults to False
        has_all_option (bool): whether the selector has all options enabled,
            defaults to False
        display_style (string, optional): style of the selector display
        available_object_items (list[dict], optional): list of objects available
            for the selector
        targets (list[dict], optional): list of targets of the selector
        name (string, optional): name of the selector
        summary (string, optional): summary of the selector"""

    key: str
    selector_type: str
    current_selection: dict
    source: dict | None = None
    multi_selection_allowed: bool = False
    has_all_option: bool = False
    display_style: str | None = None
    available_object_items: list[dict] | None = None
    targets: list[dict] | None = None
    name: str | None = None
    summary: str | None = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of page selector."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class PageVisualization(Dictable):
    """Object that describes a Visualization on a Page

    Attributes:
        key (string): key/id of the visualization
        visualization_type (string, optional): type of the visualization
        name (string, optional): name of the visualization
        selector (VisualizationSelector, optional):
            selector for the visualization"""

    _FROM_DICT_MAP = {'selector': VisualizationSelector.from_dict}

    key: str
    visualization_type: str | None = None
    name: str | None = None
    selector: VisualizationSelector | None = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of page visualization."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class ChapterPage(Dictable):
    """Object that describes a Chapter Page

    Attributes:
        key (string): key/id of the page
        visualizations (list[PageVisualization]): list of visualizations on the
            page
        name (string, optional): name of the page
        selectors (list[PageSelector], optional): list of selectors on the
            page"""

    _FROM_DICT_MAP = {
        'visualizations': [PageVisualization.from_dict],
        'selectors': [PageSelector.from_dict],
    }

    key: str
    visualizations: list[PageVisualization]
    name: str | None = None
    selectors: list[PageSelector] | None = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of dashboard chapter page."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class DashboardChapter(Dictable):
    """Object that describes a Dashboard Chapter

    Attributes:
        key (string): key/id of the chapter
        pages (list[ChapterPage]): list of the chapter pages
        name (string, optional): name of the chapter
        filters: (dict, optional): filters for the chapter"""

    _FROM_DICT_MAP = {'pages': [ChapterPage.from_dict]}

    key: str
    pages: list[ChapterPage]
    name: str | None = None
    filters: list[dict] | None = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of dashboard chapter."""
        return self.to_dict(camel_case=camel_case)
