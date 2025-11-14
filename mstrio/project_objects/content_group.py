import logging

from mstrio import config
from mstrio.api import content_groups
from mstrio.connection import Connection
from mstrio.modeling.metric.metric_format import FormatProperty
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User, UserGroup, UserOrGroup
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.helper import (
    delete_none_values,
    find_object_with_name,
    get_temp_connection,
    is_dashboard,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler('11.3.1200')
def list_content_groups(
    connection: Connection,
    to_dictionary: bool = False,
    limit: int | None = None,
    name: str | None = None,
) -> list['ContentGroup'] | list[dict]:
    """Get a list of content groups.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Content Groups as a
            list of dicts
        limit (int, optional): limit the number of elements returned
        name (str, optional): filter for content groups with names containing
            this value

    Returns:
        A list of content group objects or dictionaries representing them.
    """
    response = (
        content_groups.list_content_groups(connection=connection)
        .json()
        .get('contentGroups')
    )
    if name:
        response = [cg for cg in response if name in cg.get('name')]
    if limit:
        response = response[:limit]
    if to_dictionary:
        return response
    return [
        ContentGroup.from_dict(source=obj, connection=connection) for obj in response
    ]


@class_version_handler('11.3.1200')
class ContentGroup(Entity, CopyMixin, DeleteMixin):
    """Python representation of a Strategy One Content Group object"""

    _OBJECT_TYPE = ObjectTypes.CONTENT_BUNDLE
    _API_GETTERS = {
        **Entity._API_GETTERS,
        (
            'color',
            'opacity',
            'email_enabled',
            'recipients',
        ): content_groups.get_content_group,
    }
    _API_PATCH: dict = {
        (
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }

    def __init__(
        self, connection: Connection, name: str | None = None, id: str | None = None
    ) -> None:
        """Initialize Content Group object by passing name or id.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Content Group
            id (string, optional): ID of Content Group
        """
        if id is None or id == '':
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")
            content_group = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_content_groups,
            )
            id = content_group.get('id')
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
        )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._color = kwargs.get('color')
        self.opacity = kwargs.get('opacity')
        self.email_enabled = kwargs.get('email_enabled')
        self._recipients = kwargs.get('recipients')

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        color: str,
        opacity: int = 100,
        email_enabled: bool = False,
        recipients: list[UserOrGroup] | None = None,
    ) -> 'ContentGroup':
        """Create a new content group.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            name (str): name of the content group
            color (str, optional): color of the content group, in hex format
                example '#ffe4e1' for misty rose pink
            opacity (int, optional): opacity percentage of the content group
                expressed in an int, ranges from 0-100, default is 100
            email_enabled (bool, optional): if True recipients will be notified
                about new content in this group via email, defaults to False
            recipients (list, optional): list of recipients of the content group
                represented as str containing ID or the User and UserGroup class
                objects

        Returns:
            ContentGroup object
        """
        recipients = [
            (
                {'id': recipient.id}
                if isinstance(recipient, (User, UserGroup))
                else {'id': recipient}
            )
            for recipient in (recipients or [])
        ]
        color = FormatProperty.Color(hex_value=color).server_value
        body = {
            'name': name,
            'color': color,
            'opacity': opacity,
            'emailEnabled': email_enabled,
            'recipients': recipients,
        }
        response = content_groups.create_content_group(
            connection=connection,
            body=body,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created Content Group named: '{name}' with ID: '"
                f"{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
        color: str | None = None,
        opacity: int | None = None,
        email_enabled: bool | None = None,
        recipients: list[UserOrGroup] | None = None,
    ) -> None:
        """Alter the content group.

        Args:
            name (str, optional): name of the content group
            color (str, optional): color of the content group, in hex format
                example '#ffe4e1' for misty rose pink
            opacity (int, optional): opacity percentage of the content group
                expressed in an int, ranges from 0-100, default is 100
            email_enabled (bool, optional): if True recipients will be notified
                about new content in this group via email
            recipients (list, optional): list of recipients of the content group
                represented as str containing ID or the User and UserGroup class
                objects
            comments (str, optional): long description of the content group
            owner: (str, User, optional): owner of the content group
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = {
            'comments': comments,
            'owner': owner,
        }
        properties = delete_none_values(properties, recursion=False)
        self._alter_properties(**properties)
        operations = [
            ('/name', name),
            (
                '/color',
                (
                    int(FormatProperty.Color(hex_value=color).server_value)
                    if color
                    else None
                ),
            ),
            ('/opacity', opacity),
            ('/emailEnabled', email_enabled),
        ]
        operation_list = []
        index = 1
        for path, value in operations:
            if value is not None:
                operation_list.append(
                    {'op': 'replace', 'path': path, 'value': value, 'id': index}
                )
                index += 1
        if recipients is not None:
            operation_list += self._prepare_recipients_for_alter(
                recipients=recipients, index_offset=len(operation_list) + 1
            )
        content_groups.update_content_group(
            connection=self.connection,
            id=self.id,
            body={'operationList': operation_list},
        )
        self.fetch()

    def _process_content(self, connection, content) -> Entity:
        """Process a single content item and return the corresponding object."""
        from mstrio.project_objects import Agent, Dashboard, Document, Report

        if content.get('type') == 3:
            return Report(connection=connection, id=content.get('id'))
        elif content.get('type') == 55:
            if content.get('subtype') == ObjectSubTypes.DOCUMENT_BOT.value:
                from mstrio.project_objects.bots import Bot

                return Bot(connection=connection, id=content.get('id'))
            elif content.get('subtype') in [
                ObjectSubTypes.DOCUMENT_AGENT.value,
                ObjectSubTypes.DOCUMENT_AGENT_UNIVERSAL.value,
            ]:
                return Agent(connection=connection, id=content.get('id'))
            elif is_dashboard(content.get('viewMedia')):
                return Dashboard(connection=connection, id=content.get('id'))
            else:
                return Document(connection=connection, id=content.get('id'))

    def get_contents(self, project_ids: list[str | Project]) -> list[Entity]:
        """Get contents of the content group.

        Args:
            project_ids (list): list of project IDs or Projects to search for
                contents

        Returns:
            A list of content objects.
        """

        project_ids = [
            proj.id if isinstance(proj, Project) else proj for proj in project_ids
        ]
        response = content_groups.get_content_group_contents(
            connection=self.connection,
            id=self.id,
            project_ids=project_ids,
        ).json()
        contents = []
        for project in response:
            project_change = project or self.connection.project_id
            temp_conn = get_temp_connection(self.connection, project_change)
            for content in response.get(project):
                contents.append(self._process_content(temp_conn, content))
        return contents

    def update_contents(
        self,
        content_to_add: list['Entity'] | None = None,
        content_to_remove: list['Entity'] | None = None,
    ) -> None:
        """Update contents of the content group.

        Args:
            content_to_add (list, optional): list of content objects to add to
                the content group. Provided as a list of Entity-based objects.
                Supported content types: Agent, Dashboard, Document, Report
            content_to_remove (list. optional): list of content objects to
                remove from the content group. Provided as a list of
                Entity-based objects.
        """
        if not content_to_add and not content_to_remove:
            raise ValueError(
                "Please provide at least one content object to add or remove."
            )
        content_to_add = content_to_add or []
        content_to_remove = content_to_remove or []
        operation_list = [
            {
                'op': 'add' if content in content_to_add else 'remove',
                'path': f'/{content.connection.project_id}',
                'value': [{'id': content.id, 'type': content._OBJECT_TYPE.value}],
                'id': index + 1,
            }
            for index, content in enumerate(content_to_add + content_to_remove)
        ]
        content_groups.update_content_group_contents(
            connection=self.connection,
            id=self.id,
            body={'operationList': operation_list},
        )

    def _prepare_recipients_for_alter(
        self, recipients: list[UserOrGroup], index_offset: int
    ) -> list[dict]:
        recipients = [
            (recipient.id if isinstance(recipient, (User, UserGroup)) else recipient)
            for recipient in recipients
        ]
        recipients_to_add = [
            r for r in recipients if r not in [r2.id for r2 in self.recipients]
        ]
        recipients_to_remove = [r.id for r in self.recipients if r.id not in recipients]
        operations = []
        for rec_id in recipients_to_add:
            operations.append(
                {
                    'op': 'add',
                    'path': '/recipients',
                    'value': [{'id': rec_id}],
                    'id': index_offset,
                }
            )
            index_offset += 1
        for rec_id in recipients_to_remove:
            operations.append(
                {
                    'op': 'remove',
                    'path': '/recipients',
                    'value': [{'id': rec_id}],
                    'id': index_offset,
                }
            )
            index_offset += 1

        return operations

    @property
    def color(self) -> str:
        """Color of the content group in hex format."""
        if self._color is None:
            self.fetch('color')
        if isinstance(self._color, int):
            self._color = FormatProperty.Color(server_value=str(self._color)).hex_value
        return self._color

    @property
    def recipients(self) -> list[UserOrGroup]:
        """Recipients of the content group."""
        if self._recipients is None:
            self.fetch('recipients')
        if self._recipients and isinstance(self._recipients[0], dict):
            self._recipients = [
                (
                    UserGroup.from_dict(source=recipient, connection=self.connection)
                    if recipient.get('group')
                    else User.from_dict(source=recipient, connection=self.connection)
                )
                for recipient in self._recipients
            ]
        return self._recipients
