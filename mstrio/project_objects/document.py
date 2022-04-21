from typing import List, Optional, Union

from pandas import DataFrame

from mstrio.api import documents, library
from mstrio.connection import Connection
from mstrio.server.environment import Environment
from mstrio.users_and_groups import list_users, User, UserGroup, UserOrGroup
from mstrio.utils import helper
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import DeleteMixin, Entity, ObjectTypes, VldbMixin


def list_documents(connection: Connection, name: Optional[str] = None, to_dictionary: bool = False,
                   to_dataframe: bool = False, limit: Optional[int] = None, **filters):
    """Get all Documents available in the project specified within the
    `connection` object.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact name of the document to list
        to_dictionary(bool, optional): if True, return Documents as
            list of dicts
        to_dataframe(bool, optional): if True, return Documents as
            pandas DataFrame
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of documents.
    """
    # TODO: consider adding Connection.project_selected attr/method
    if connection.project_id is None:
        raise ValueError("Please log into a specific project to load documents within it. "
                         "To load all documents across the whole environment use "
                         f"{list_documents_across_projects.__name__} function.")
    return Document._list_all(connection, to_dictionary=to_dictionary, name=name, limit=limit,
                              to_dataframe=to_dataframe, **filters)


def list_documents_across_projects(connection: Connection, name: Optional[str] = None,
                                   to_dictionary: bool = False, to_dataframe: bool = False,
                                   limit: Optional[int] = None, **filters):
    """Get all Documents stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact names of the documents to list
        to_dictionary(bool, optional): if True, return Documents as
            list of dicts
        to_dataframe(bool, optional): if True, return Documents as
            pandas DataFrame
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of documents.
    """
    project_id_before = connection.project_id
    env = Environment(connection)
    projects = env.list_projects()
    output = []
    for project in projects:
        connection.select_project(project_id=project.id)
        output.extend(
            Document._list_all(connection, to_dictionary=to_dictionary, name=name, limit=limit,
                               to_dataframe=to_dataframe, **filters))
        output = list(set(output))
    connection.select_project(project_id=project_id_before)
    return output


class Document(Entity, VldbMixin, DeleteMixin):
    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP, 'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict
    }
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, name: Optional[str] = None,
                 id: Optional[str] = None):
        """Initialize Document object by passing name or id.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: name of Document
            id: ID of Document
        """
        if id is None and name is None:
            raise ValueError("Please specify either 'name' or 'id' parameter in the constructor.")
        if id is None:
            documents = self._list_all(connection=connection, to_dictionary=True, name=name)
            if documents:
                id = documents[0]['id']
            else:
                msg = (f"There is no {self.__class__.__name__} associated with the given "
                       f"name: '{name}'")
                raise ValueError(msg)

        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._instance_id = ""
        self._recipients = []

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter Document name or/and description.

        Args:
            name: new name of the Document
            description: new description of the Document
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

    def publish(self, recipients: Optional[Union[UserOrGroup, List[UserOrGroup]]] = None):
        """Publish the document for authenticated user. If `recipients`
        parameter is specified publishes the document for the given users.

        Args:
            recipients(list): list of users or user groups to publish the
                document to (can be a list of IDs or a list of User and
                UserGroup elements)
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
        body = {'id': self.id, 'recipients': recipients}
        self._instance_id = ''
        library.publish_document(self.connection, body)

    def unpublish(self, recipients: Optional[Union[UserOrGroup, List[UserOrGroup]]] = None):
        """Unpublish the document for all users it was previously published to.
        If `recipients` parameter is specified unpublishes the document for the
        given users.

        Args:
            recipients(list): list of users or user groups to publish the
                document to (can be a list of IDs or a list of User and
                UserGroup elements).
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
                    'Please provide either list User and UserGroup elements or str elements.')
            for user_id in recipients:
                library.unpublish_document_for_user(self.connection, document_id=self.id,
                                                    user_id=user_id)

    def share_to(self, users: Union[UserOrGroup, List[UserOrGroup]]):
        """Shares the document to the listed users' libraries.

        Args:
            users(list): list of users or user groups to publish the
                document to (can be a list of IDs or a list of User and
                UserGroup elements).
        """
        self.publish(users)

    @classmethod
    def _list_all(cls, connection: Connection, name: Optional[str] = None,
                  to_dictionary: bool = False, to_dataframe: bool = False,
                  limit: Optional[int] = None,
                  **filters) -> Union[List["Document"], List[dict], DataFrame]:
        msg = "Error retrieving documents from the environment."
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either `to_dictionary=True` or `to_dataframe=True`, but not both.",
                ValueError)
        objects = helper.fetch_objects_async(connection, api=documents.get_documents,
                                             async_api=documents.get_documents_async,
                                             dict_unpack_value='result', limit=limit,
                                             chunk_size=1000, error_msg=msg, filters=filters,
                                             search_term=name)
        if to_dictionary:
            return objects
        elif to_dataframe:
            return DataFrame(objects)
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    def get_connected_cubes(self):
        """Lists cubes used by this document."""
        cubes = documents.get_cubes_used_by_document(self.connection, self.id).json()
        ret_cubes = [helper.choose_cube(self.connection, cube) for cube in cubes]
        return [tmp for tmp in ret_cubes if tmp]  # remove `None` values

    @property
    def instance_id(self):
        if self._instance_id == '':
            body = {"resolveOnly": True, "persistViewState": True}
            response = documents.create_new_document_instance(connection=self.connection,
                                                              document_id=self.id, body=body)
            self._instance_id = response.json()['mid']
        return self._instance_id

    @property
    def recipients(self):
        response = library.get_document(connection=self.connection,
                                        id=self.id).json()['recipients']
        if response:
            self._recipients = list_users(connection=self.connection,
                                          id=[r['id'] for r in response])
        else:
            self._recipients = []
        return self._recipients
