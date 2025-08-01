import logging
from functools import partial
from typing import TYPE_CHECKING

from pandas import DataFrame, concat

from mstrio import config
from mstrio.api import documents, library
from mstrio.connection import Connection
from mstrio.object_management import Folder, SearchPattern, search_operations
from mstrio.project_objects import OlapCube, SuperCube
from mstrio.project_objects.helpers import answer_prompts_helper
from mstrio.project_objects.palette import Palette
from mstrio.server.environment import Environment
from mstrio.types import ObjectSubTypes
from mstrio.users_and_groups import User
from mstrio.utils import helper
from mstrio.utils.cache import CacheSource, ContentCacheMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import (
    CopyMixin,
    DeleteMixin,
    Entity,
    MoveMixin,
    ObjectTypes,
    VldbMixin,
)
from mstrio.utils.helper import (
    filter_params_for_func,
    find_object_with_name,
    get_valid_project_id,
    is_document,
)
from mstrio.utils.library import LibraryMixin
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.project_objects.prompt import Prompt

logger = logging.getLogger(__name__)


def list_documents(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    name: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    **filters,
) -> list["Document"] | list[dict] | DataFrame:
    """Get all Documents available in the project specified within the
    `connection` object.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Documents as
            list of dicts
        to_dataframe (bool, optional): if True, return Documents as
            pandas DataFrame
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        name (str, optional): characters that the document name must contain
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of documents or list of dictionaries or DataFrame object
    """

    return Document._list_all(
        connection,
        to_dictionary=to_dictionary,
        name=name,
        limit=limit,
        to_dataframe=to_dataframe,
        project_id=project_id,
        project_name=project_name,
        **filters,
    )


def list_documents_across_projects(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
) -> list["Document"] | list[dict] | DataFrame:
    """Get all Documents stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        name (string, optional): characters that the document name must contain
        to_dictionary (bool, optional): if True, return Documents as
            list of dicts
        to_dataframe (bool, optional): if True, return Documents as
            pandas DataFrame
        limit (int, optional): limit the number of elements returned. If `None`
            (default), all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of documents or list of dictionaries or DataFrame object
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

        docs = Document._list_all(
            connection,
            to_dictionary=to_dictionary,
            name=name,
            limit=limit,
            to_dataframe=to_dataframe,
            **filters,
        )
        if to_dataframe:
            output = concat([output, docs], ignore_index=True)
        else:
            output.extend(docs)

    connection.select_project(project_id=project_id_before)
    return output[:limit]


class Document(
    Entity,
    VldbMixin,
    CopyMixin,
    MoveMixin,
    DeleteMixin,
    ContentCacheMixin,
    LibraryMixin,
):
    """Python representation of Strategy One Document object

    _CACHE_TYPE is a variable used by ContentCache class for cache filtering
    purposes.
    """

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION
    _CACHE_TYPE = CacheSource.Type.DOCUMENT
    _API_GETTERS = {**Entity._API_GETTERS, 'recipients': library.get_document}
    _API_PATCH = {
        ('name', 'description', 'folder_id', 'hidden', 'owner'): (
            objects_processors.update,
            'partial_put',
        )
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict,
        'recipients': [User.from_dict],
    }

    def __init__(
        self, connection: Connection, name: str | None = None, id: str | None = None
    ):
        """Initialize Document object by passing name or id.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Document
            id (string, optional): ID of Document
        """
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            document = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=self._list_all,
                search_pattern=SearchPattern.EXACTLY,
            )
            id = document['id']
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._instance_id = ""
        self._recipients = kwargs.get('recipients', default_value)
        self._template_info = kwargs.get('templateInfo', default_value)
        self._folder_id = None

    def list_properties(self, excluded_properties: list[str] | None = None) -> dict:
        """List properties for the document.

        Returns:
            A list of all document properties."""
        properties = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'subtype': self.subtype,
            'ext_type': self.ext_type,
            'ancestors': self.ancestors,
            'certified_info': self.certified_info,
            'comments': self.comments,
            'date_created': self.date_created,
            'date_modified': self.date_modified,
            'instance_id': self.instance_id,
            'owner': self.owner,
            'recipients': self.recipients,
            'version': self.version,
            'template_info': self.template_info,
            'acg': self.acg,
            'acl': self.acl,
        }

        if excluded_properties:
            for prop in excluded_properties:
                properties.pop(prop, None)

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
        """Alter Document's basic properties.

        Args:
            name (string, optional): new name of the Document
            description (string, optional): new description of the Document
            folder_id (string | Folder, optional): A globally unique identifier
                used to distinguish between metadata objects within the same
                project. It is possible for two metadata objects in different
                projects to have the same Object ID.
            hidden: Specifies whether the document is hidden
            comments (str, optional): long description of the Document
            owner: (str | User, optional): owner of the Document
        """
        if isinstance(owner, User):
            owner = owner.id
        description = description or self.description
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)
        if folder_id:
            self._folder_id = folder_id

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
        name: str | None = None,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        project_id: str | None = None,
        project_name: str | None = None,
        **filters,
    ) -> list["Document"] | list[dict] | DataFrame:
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either `to_dictionary=True` or `to_dataframe=True`, but "
                "not both.",
                ValueError,
            )
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=not project_name,
        )

        objects = search_operations.full_search(
            connection,
            object_types=ObjectSubTypes.REPORT_WRITING_DOCUMENT,
            project=project_id,
            name=name,
            pattern=search_pattern,
            **filters,
        )
        documents = [obj for obj in objects if is_document(obj['view_media'])]

        documents = documents[:limit] if limit else documents

        if to_dictionary:
            return documents
        elif to_dataframe:
            return DataFrame(documents)
        else:
            return [
                cls.from_dict(
                    source=document, connection=connection, with_missing_value=True
                )
                for document in documents
            ]

    def get_connected_cubes(self) -> list[SuperCube | OlapCube]:
        """Lists cubes used by this document.

        Returns:
            A list of cubes used by the document."""
        cubes = documents.get_cubes_used_by_document(self.connection, self.id).json()
        ret_cubes = [helper.choose_cube(self.connection, cube) for cube in cubes]
        return [tmp for tmp in ret_cubes if tmp]  # remove `None` values

    @method_version_handler('11.3.0600')
    def list_palettes(self, to_dictionary: bool = False) -> list[Palette] | list[dict]:
        """List all palettes used by this document.

        Returns:
            A list of color palettes used by the document."""
        return self.list_dependencies(
            object_types=ObjectTypes.PALETTE, to_dictionary=to_dictionary
        )

    def answer_prompts(
        self, prompt_answers: list['Prompt'], force: bool = False
    ) -> bool:
        """Answer prompts of the report.

        Args:
            prompt_answers (list[Prompt]): List of Prompt class objects
                answering the prompts of the report.
            force (bool): If True, then the document's existing prompt will be
                overwritten by ones from the prompt_answers list, and additional
                input from the user won't be asked. Otherwise, the user will be
                asked for input if the prompt is not answered, or if prompt was
                already answered.

        Returns:
            bool: True if prompts were answered successfully, False otherwise.
        """
        common_args = {
            'connection': self.connection,
            'document_id': self.id,
            'instance_id': self.instance_id,
            'project_id': self.project_id,
        }

        return answer_prompts_helper(
            instance_id=self.instance_id,
            prompt_answers=prompt_answers,
            get_status_func=partial(
                documents.get_document_status,
                **common_args,
            ),
            get_prompts_func=partial(
                documents.get_prompts_for_instance,
                **common_args,
                closed=False,
            ),
            answer_prompts_func=partial(
                documents.answer_prompts,
                **common_args,
            ),
            force=force,
        )

    @property
    def instance_id(self) -> str:
        if not self.get('_instance_id'):
            body = {"resolveOnly": True, "persistViewState": True}
            response = documents.create_new_document_instance(
                connection=self.connection, document_id=self.id, body=body
            ).json()
            self._instance_id = response.get('mid')
        return self._instance_id

    @property
    def folder_id(self):
        if not self._folder_id:
            self._folder_id = (
                next(folder['id'] for folder in self.ancestors if folder['level'] == 1)
                if self.ancestors
                else None
            )
        return self._folder_id

    @property
    def recipients(self):
        return self._recipients

    @property
    def template_info(self):
        return self._template_info
