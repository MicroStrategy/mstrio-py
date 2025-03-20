import logging

from mstrio import config
from mstrio.api import events
from mstrio.connection import Connection
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.helper import filter_params_for_func
from mstrio.utils.related_subscription_mixin import RelatedSubscriptionMixin
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import (
    class_version_handler,
    is_server_min_version,
    method_version_handler,
)

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0100')
def list_events(
    connection: Connection, to_dictionary: bool = False, limit: int = None, **filters
) -> list["Event"] | list[dict]:
    """List event objects or event dictionaries. Optionally filter list.

    Args:
        connection(object): Strategy One connection object returned
            by 'connection.Connection()'
        to_dictionary(bool, optional): if True, return event as
            list of dicts
        limit(int, optional): maximum number of Events returned.
        **filters: Available filter parameters:
            ['name', 'id', 'description', 'acg']
    """
    _objects = helper.fetch_objects(
        connection=connection,
        api=events.list_events,
        limit=limit,
        filters=filters,
        dict_unpack_value='events',
    )

    if to_dictionary:
        return _objects
    return [Event.from_dict(source=obj, connection=connection) for obj in _objects]


@class_version_handler('11.3.0100')
class Event(Entity, CopyMixin, DeleteMixin, RelatedSubscriptionMixin):
    """Class representation of Strategy One Event object.

    Attributes:
        connection: A Strategy One connection object
        name: Event name
        id: Event ID
        description: Event descriptions
    """

    _OBJECT_TYPE = ObjectTypes.SCHEDULE_EVENT
    _API_GETTERS = {
        (
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl',
            'comments',
            'owner',
        ): objects_processors.get_info,
    }
    _API_DELETE = staticmethod(events.delete_event)
    _API_PATCH = {
        ('name', 'description'): (events.update_event, 'put'),
        ('comments', 'owner'): (objects_processors.update, 'partial_put'),
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize the Event object, populates it with I-Server data.
        Specify either `id` or `name`. When `id` is provided (not `None`),
        `name` is omitted.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`.
            id: Event ID
            name: Event name
        """
        self._API_GETTERS[('id', 'name', 'description')] = (
            events.get_event
            if is_server_min_version(connection, '11.3.0200')
            else objects_processors.get_info
        )

        if id is None and name is None:
            raise AttributeError(
                "Please specify either 'name' or 'id' parameter in the constructor."
            )
        if id is None:
            objects_info = list_events(connection, name=name, to_dictionary=True)
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no event with the given name: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id, name=name)

    def trigger(self):
        """Trigger the Event"""
        response = events.trigger_event(self.connection, self.id)
        if response.ok and config.verbose:
            logger.info(
                f"Event '{self.name}' with ID : '{self.id}' has been triggered."
            )
        return response.ok

    @classmethod
    def create(
        cls, connection: Connection, name: str, description: str | None = None
    ) -> "Event":
        """Create an Event

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`.
            name: Name of the new Event
            description: Description of the new Event
        """
        body = helper.delete_none_values(
            {
                "name": name,
                "description": description,
            },
            recursion=True,
        )
        response = events.create_event(connection, body)
        return cls.from_dict(response.json(), connection)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the Event's properties

        Args:
            name (str, optional): New name for the Event
            description (str, optional): New description for the Event
            comments (str, optional): long description of the Event
            owner: (str, User, optional): owner of the Event object
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

        if config.verbose:
            logger.info(f"Updated event: '{self.name}' with ID: {self.id}.")
