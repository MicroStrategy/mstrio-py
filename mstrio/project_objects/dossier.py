from dataclasses import dataclass
import logging
from typing import Optional

from pandas import concat, DataFrame

from mstrio import config
from mstrio.api import documents
from mstrio.connection import Connection
from mstrio.object_management import Folder, search_operations, SearchPattern
from mstrio.project_objects.document import Document
from mstrio.server.environment import Environment
from mstrio.types import ObjectSubTypes
from mstrio.users_and_groups import UserOrGroup
from mstrio.utils import helper
from mstrio.utils.cache import CacheSource
from mstrio.utils.helper import Dictable, get_valid_project_id
from mstrio.utils.helper import is_dossier

logger = logging.getLogger(__name__)


def list_dossiers(
    connection: Connection,
    name: Optional[str] = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    **filters
) -> list["Dossier"] | list[dict] | DataFrame:
    """Get all Dossiers stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: characters that the dossier name must contain
        to_dictionary(bool, optional): if True, return Dossiers as
            list of dicts
        to_dataframe(bool, optional): if True, return Dossiers as
            pandas DataFrame
        limit(int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of dossiers or list of dictionaries or DataFrame object
    """

    return Dossier._list_all(
        connection,
        to_dictionary=to_dictionary,
        name=name,
        limit=limit,
        to_dataframe=to_dataframe,
        project_id=project_id,
        project_name=project_name,
        **filters
    )


def list_dossiers_across_projects(
    connection: Connection,
    name: Optional[str] = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: Optional[int] = None,
    **filters
) -> list["Dossier"] | list[dict] | DataFrame:
    """Get all Dossiers stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: characters that the dossier name must contain
        to_dictionary(bool, optional): if True, return Dossiers as
            list of dicts
        to_dataframe(bool, optional): if True, return Dossiers as
            pandas DataFrame
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
        List of dossiers or list of dictionaries or DataFrame object
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
        dossiers = Dossier._list_all(
            connection,
            to_dictionary=to_dictionary,
            name=name,
            limit=limit,
            to_dataframe=to_dataframe,
            **filters
        )

        if to_dataframe:
            output = concat([output, dossiers], ignore_index=True)
        else:
            output.extend(dossiers)

    connection.select_project(project_id=project_id_before)
    return output[:limit]


class Dossier(Document):
    _CACHE_TYPE = CacheSource.Type.DOSSIER

    _API_GETTERS = {
        **Document._API_GETTERS, ('chapters', 'current_chapter'): documents.get_dossier_hierarchy
    }
    _FROM_DICT_MAP = {
        **Document._FROM_DICT_MAP,
        'chapters': (
            lambda source,
            connection: [DossierChapter.from_dict(content, connection) for content in source]
        )
    }

    def __init__(
        self, connection: Connection, name: Optional[str] = None, id: Optional[str] = None
    ):
        """Initialize Dossier object by passing name or id.

        Args:
            connection (object): MicroStrategy connection object returned
                by `connection.Connection()`
            name (string, optional): name of Dossier
            id (string, optional): ID of Dossier
        """
        super().__init__(connection=connection, name=name, id=id)

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        self._current_chapter = kwargs.get('current_chapter')
        self._chapters = kwargs.get('chapters')

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
        name: Optional[str] = None,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: Optional[int] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        **filters
    ) -> list["Dossier"] | list[dict] | DataFrame:

        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either to_dictionary=True or to_dataframe=True, but not both.",
                ValueError
            )
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )

        objects = search_operations.full_search(
            connection,
            object_types=ObjectSubTypes.REPORT_WRITING_DOCUMENT,
            project=project_id,
            name=name,
            pattern=search_pattern,
            **filters,
        )
        dossiers = [
            obj for obj in objects if is_dossier(obj['view_media'])
        ]
        dossiers = dossiers[:limit]

        if to_dictionary:
            return dossiers
        elif to_dataframe:
            return DataFrame(dossiers)
        else:
            return [cls.from_dict(source=dossier, connection=connection) for dossier in dossiers]

    def list_properties(self) -> dict:
        """List properties for the dossier."""
        properties = super().list_properties()
        additional_values = {'chapters': self.chapters, 'current_chapter': self.current_chapter}
        properties.update(additional_values)
        return properties

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        folder_id: Optional[Folder | str] = None
    ):
        """Alter Dossier name, description and/or folder id.

        Args:
            name (string, optional): new name of the Dossier
            description (string, optional): new description of the Dossier
            folder_id (string | Folder, optional): A globally unique identifier
                used to distinguish between metadata objects within the same
                project. It is possible for two metadata objects in different
                projects to have the same Object Id.
        """
        super().alter(name, description, folder_id)

    def publish(self, recipients: Optional[UserOrGroup | list[UserOrGroup]] = None):
        """Publish the dossier for authenticated user. If `recipients`
        parameter is specified publishes the dossier for the given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the dossier to (can be a list of IDs
                or a list of User and UserGroup elements)
        """
        super().publish(recipients)

    def unpublish(self, recipients: Optional[UserOrGroup | list[UserOrGroup]] = None):
        """Unpublish the dossier for all users it was previously published to.
        If `recipients` parameter is specified unpublishes the dossier for the
        given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the dossier to (can be a list of IDs
                or a list of User and UserGroup elements)
        """
        super().unpublish(recipients)

    def share_to(self, users: UserOrGroup | list[UserOrGroup]):
        """Shares the dossier to the listed users' libraries.

        Args:
            users(UserOrGroup | list[UserOrGroup]): list of users or user
                groups to publish the dossier to (can be a list of IDs or a
                list of User and UserGroup elements).
        """
        self.publish(users)

    @property
    def chapters(self) -> list["DossierChapter"]:
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
    targets: Optional[list[dict]] = None

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
    source: Optional[dict] = None
    multi_selection_allowed: bool = False
    has_all_option: bool = False
    display_style: Optional[str] = None
    available_object_items: Optional[list[dict]] = None
    targets: Optional[list[dict]] = None
    name: Optional[str] = None
    summary: Optional[str] = None

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
    visualization_type: Optional[str] = None
    name: Optional[str] = None
    selector: Optional[VisualizationSelector] = None

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
        'visualizations': [PageVisualization.from_dict], 'selectors': [PageSelector.from_dict]
    }

    key: str
    visualizations: list[PageVisualization]
    name: Optional[str] = None
    selectors: Optional[list[PageSelector]] = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of dossier chapter page."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class DossierChapter(Dictable):
    """Object that describes a Dossier Chapter

    Attributes:
        key (string): key/id of the chapter
        pages (list[ChapterPage]): list of the chapter pages
        name (string, optional): name of the chapter
        filters: (dict, optional): filters for the chapter"""

    _FROM_DICT_MAP = {'pages': [ChapterPage.from_dict]}

    key: str
    pages: list[ChapterPage]
    name: Optional[str] = None
    filters: Optional[list[dict]] = None

    def list_properties(self, camel_case=True) -> dict:
        """Lists properties of dossier chapter."""
        return self.to_dict(camel_case=camel_case)
