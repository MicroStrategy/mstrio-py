import logging
from typing import Optional

from pandas import concat, DataFrame

from mstrio import config
from mstrio.api import documents, library, objects
from mstrio.api.schedules import get_contents_schedule
from mstrio.connection import Connection
from mstrio.distribution_services.schedule import Schedule
from mstrio.object_management import Folder, search_operations, SearchPattern
from mstrio.project_objects import OlapCube, SuperCube
from mstrio.server.environment import Environment
from mstrio.types import ObjectSubTypes
from mstrio.users_and_groups import User, UserGroup, UserOrGroup
from mstrio.utils import helper
from mstrio.utils.cache import CacheSource, ContentCacheMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin, ObjectTypes, VldbMixin
from mstrio.utils.helper import filter_params_for_func, get_valid_project_id, IServerError
from mstrio.utils.helper import is_document
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


def list_documents(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: Optional[int] = None,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    **filters
) -> list["Document"] | list[dict] | DataFrame:
    """Get all Documents available in the project specified within the
    `connection` object.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): MicroStrategy connection object returned
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
        **filters
    )


def list_documents_across_projects(
    connection: Connection,
    name: Optional[str] = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: Optional[int] = None,
    **filters
) -> list["Document"] | list[dict] | DataFrame:
    """Get all Documents stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): MicroStrategy connection object returned
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
            **filters
        )
        if to_dataframe:
            output = concat([output, docs], ignore_index=True)
        else:
            output.extend(docs)

    connection.select_project(project_id=project_id_before)
    return output[:limit]


class Document(Entity, VldbMixin, CopyMixin, MoveMixin, DeleteMixin, ContentCacheMixin):
    """ Python representation of MicroStrategy Document object

    _CACHE_TYPE is a variable used by ContentCache class for cache filtering
    purposes.
    """

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION
    _CACHE_TYPE = CacheSource.Type.DOCUMENT
    _API_GETTERS = {**Entity._API_GETTERS, 'recipients': library.get_document}
    _API_PATCH = {('name', 'description', 'folder_id'): (objects.update_object, 'partial_put')}
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict,
        'recipients': [User.from_dict]
    }

    def __init__(
        self, connection: Connection, name: Optional[str] = None, id: Optional[str] = None
    ):
        """Initialize Document object by passing name or id.

        Args:
            connection (object): MicroStrategy connection object returned
                by `connection.Connection()`
            name (string, optional): name of Document
            id (string, optional): ID of Document
        """
        if id is None:
            document = super()._find_object_with_name(
                connection=connection, name=name, listing_function=self._list_all
            )
            id = document['id']
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._instance_id = ""
        self._recipients = kwargs.get('recipients')
        self._project_id = self.connection.project_id
        self._template_info = kwargs.get('templateInfo')
        self._folder_id = None

    def list_properties(self):
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
            'acl': self.acl
        }
        return properties

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        folder_id: Optional[Folder | str] = None
    ):
        """Alter Document name, description and/or folder id.

        Args:
            name (string, optional): new name of the Document
            description (string, optional): new description of the Document
            folder_id (string | Folder, optional): A globally unique identifier
                used to distinguish between metadata objects within the same
                project. It is possible for two metadata objects in different
                projects to have the same Object Id.
        """
        description = description or self.description
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)
        if folder_id:
            self._folder_id = folder_id

    def __validate_user(self, recipient_id: str) -> str | None:
        try:
            User(self.connection, id=recipient_id)
        except IServerError:
            if config.verbose:
                logger.info(f'{recipient_id} is not a valid value for User ID')
            return None
        return recipient_id

    def publish(self, recipients: Optional[UserOrGroup | list[UserOrGroup]] = None):
        """Publish the document for authenticated user. If `recipients`
        parameter is specified publishes the document for the given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the document to (can be a list of IDs
                or a list of User and UserGroup elements)
        """
        if not isinstance(recipients, list) and recipients is not None:
            recipients = [recipients]

        if recipients is None:
            recipients = [self.connection.user_id]
        elif all([isinstance(el, User) for el in recipients]):
            recipients = [recipient.id for recipient in recipients]
        elif all([isinstance(el, UserGroup) for el in recipients]):
            users = [user for group in recipients for user in group.members]
            recipients = [user["id"] for user in users]
        elif any([not isinstance(el, str) for el in recipients]):
            raise ValueError('Please provide either list of User, UserGroup or str elements.')
        for recipient in recipients:
            if not self.__validate_user(recipient):
                recipients.remove(recipient)
        body = {'id': self.id, 'recipients': recipients}
        library.publish_document(self.connection, body)
        self.fetch(attr='recipients')

    def unpublish(self, recipients: Optional[UserOrGroup | list[UserOrGroup]] = None):
        """Unpublish the document for all users it was previously published to.
        If `recipients` parameter is specified unpublishes the document for the
        given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup], optional): list of users
                or user groups to publish the document to (can be a list of IDs
                or a list of User and UserGroup elements)
        """

        if recipients is None:
            library.unpublish_document(self.connection, id=self.id)
        else:
            if not isinstance(recipients, list):
                recipients = [recipients]
            if all([isinstance(el, User) for el in recipients]):
                recipients = [recipient.id for recipient in recipients]
            elif all([isinstance(el, UserGroup) for el in recipients]):
                users = [user for group in recipients for user in group.members]
                recipients = [user["id"] for user in users]
            elif any([not isinstance(el, str) for el in recipients]):
                raise ValueError(
                    'Please provide either list User and UserGroup elements or str elements.'
                )
            for user_id in recipients:
                if self.__validate_user(user_id):
                    library.unpublish_document_for_user(
                        self.connection, document_id=self.id, user_id=user_id
                    )
        self.fetch(attr='recipients')

    @method_version_handler('11.3.0600')
    def list_available_schedules(self,
                                 to_dictionary: bool = False) -> list["Schedule"] | list[dict]:
        """Get a list of schedules available for the object instance.

        Args:
            to_dictionary (bool, optional): If True returns a list of
                dictionaries, otherwise returns a list of Schedules.
                False by default.

        Returns:
            List of Schedule objects or list of dictionaries.
        """
        schedules_list_response = (
            get_contents_schedule(
                connection=self.connection,
                project_id=self.connection.project_id,
                body={
                    'id': self.id, 'type': 'document'
                }
            ).json()
        ).get('schedules')
        if to_dictionary:
            return schedules_list_response
        else:
            return [
                Schedule.from_dict(connection=self.connection, source=schedule_id)
                for schedule_id in schedules_list_response
            ]

    def share_to(self, users: UserOrGroup | list[UserOrGroup]):
        """Shares the document to the listed users' libraries.

        Args:
            users(UserOrGroup | list[UserOrGroup]): list of users or user
                groups to publish the document to (can be a list of IDs or a
                list of User and UserGroup elements).
        """
        self.publish(users)

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
    ) -> list["Document"] | list[dict] | DataFrame:

        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either `to_dictionary=True` or `to_dataframe=True`, but not both.",
                ValueError
            )
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True,
        )

        objects = search_operations.full_search(
            connection,
            object_types=ObjectSubTypes.REPORT_WRITING_DOCUMENT,
            project=project_id,
            name=name,
            pattern=search_pattern,
            **filters,
        )
        documents = [
            obj for obj in objects if is_document(obj['view_media'])
        ]

        documents = documents[:limit] if limit else documents

        if to_dictionary:
            return documents
        elif to_dataframe:
            return DataFrame(documents)
        else:
            return [
                cls.from_dict(source=document, connection=connection)
                for document in documents
            ]

    def get_connected_cubes(self) -> list[SuperCube | OlapCube]:
        """Lists cubes used by this document.

        Returns:
            A list of cubes used by the document."""
        cubes = documents.get_cubes_used_by_document(self.connection, self.id).json()
        ret_cubes = [helper.choose_cube(self.connection, cube) for cube in cubes]
        return [tmp for tmp in ret_cubes if tmp]  # remove `None` values

    @property
    def instance_id(self):
        if self._instance_id == '':
            body = {"resolveOnly": True, "persistViewState": True}
            response = documents.create_new_document_instance(
                connection=self.connection, document_id=self.id, body=body
            )
            self._instance_id = response.json()['mid']
        return self._instance_id

    @property
    def folder_id(self):
        if not self._folder_id:
            self._folder_id = next(
                folder['id'] for folder in self.ancestors if folder['level'] == 1
            ) if self.ancestors else None
        return self._folder_id

    @property
    def recipients(self):
        return self._recipients

    @property
    def template_info(self):
        return self._template_info
