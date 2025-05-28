from logging import getLogger

from requests import Response

from mstrio import config
from mstrio.api import timezones as tz_api
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = getLogger(__name__)


@method_version_handler(version='11.3.0500')
def list_timezones(
    connection: Connection,
    to_dictionary: bool = False,
    limit: int | None = None,
    only_system_timezones: bool | None = None,
    only_custom_timezones: bool | None = None,
    **filters,
):
    """Get list of all time zones.

    Args:
        connection: Strategy One connection object returned
            by `connection.Connection()`.
        to_dictionary (bool, optional): If True, returns list of time zones
            as dicts, otherwise list of TimeZone objects. Defaults to False.
        limit (int, optional): The maximum number of time zones to return.
        only_system_timezones (bool, optional): If True, returns only system
            time zones. Cannot be used with `only_custom_timezones`.
        only_custom_timezones (bool, optional): If True, returns only custom
            time zones. Cannot be used with `only_system_timezones`.

    Returns:
        List of time zones as `TimeZone` objects or dictionaries.
    """
    return TimeZone._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        only_system_timezones=only_system_timezones,
        only_custom_timezones=only_custom_timezones,
        **filters,
    )


@class_version_handler(version='11.3.0500')
class TimeZone(Entity, CopyMixin, DeleteMixin):
    _OBJECT_TYPE = ObjectTypes.TIMEZONE
    _API_GETTERS = {
        (
            'name',
            'description',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'acg',
            'acl',
            'comments',
            'hidden',
        ): objects_processors.get_info,
        (
            'id',
            'base_timezone',
            'current_offset',
        ): tz_api.get_tz,
    }
    _API_PATCH = {
        (
            'name',
            'description',
            'abbreviation',
            'hidden',
            'folder_id',
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
        ('base_timezone',): (tz_api.update_tz, 'partial_put'),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'base_timezone': lambda source, connection: source['object_id'],
    }

    def __init__(
        self,
        connection: Connection,
        id: str = None,
        name: str = None,
    ):
        """Initialize TimeZone object by passing ID or name.
        When `id` is provided, `name` is omitted.

        Args:
            connection: Strategy One connection object
            id (str, optional): ID of the time zone object
            name (str, optional): Name of the time zone object. Must be provided
                if `id` is not.
        """
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            tz_obj = helper.find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=self._list_all,
            )
            object_id = tz_obj['id']
        else:
            object_id = id
        super().__init__(connection=connection, object_id=object_id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.name = kwargs.get('name')
        self.current_offset = kwargs.get('current_offset')
        self.base_timezone = kwargs.get('base_timezone')

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        base_timezone: 'str | TimeZone',
        description: str | None = None,
    ) -> 'TimeZone':
        """Create a new time zone object with the specified properties.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`.
            name (str): Name of the new time zone.
            base_timezone (str | TimeZone): Existing time zone object to base
                the new time zone on.
            description (str, optional): Description of the new time zone.
        """
        if isinstance(base_timezone, cls):
            base_timezone = base_timezone.id
        body = {
            "name": name,
            "description": description,
            "baseTimezone": {
                "objectId": base_timezone,
            },
        }
        body = helper.delete_none_values(source=body, recursion=True)
        res: Response = tz_api.create_tz(connection=connection, body=body)
        new_tz = cls.from_dict(
            source=res.json(),
            connection=connection,
        )
        if config.verbose:
            logger.info(
                f"Successfully created Time Zone named: '{name}' with ID:"
                f" '{new_tz.id}'"
            )
        return new_tz

    def alter(
        self,
        name: str = None,
        base_timezone: 'str | TimeZone | None' = None,
        description: str = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the time zone's properties.
        Args:
            name (str, optional): Name of the time zone object
            base_timezone (str or TimeZone, optional): Reference (ID or TimeZone
                object) to the base time zone
            description (str, optional): Description of the time zone object
            comments (str, optional): long description of the time zone object
            owner: (str or User, optional): owner of the time zone object
        """
        if isinstance(base_timezone, self.__class__):
            base_timezone = base_timezone.id
        if base_timezone is not None:
            base_timezone = {"objectId": base_timezone}
        properties = helper.filter_params_for_func(
            self.alter, locals(), exclude=['self']
        )
        self._alter_properties(**properties)

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        limit: int | None = None,
        only_system_timezones: bool | None = None,
        only_custom_timezones: bool | None = None,
        **filters,
    ) -> list['TimeZone'] | list[dict]:

        if only_system_timezones and only_custom_timezones:
            raise ValueError(
                "You can use only one of "
                "'only_system_timezones' and 'only_custom_timezones' arguments."
            )

        subtype = None
        if only_system_timezones:
            subtype = "timezone_system"
        elif only_custom_timezones:
            subtype = "timezone_custom"

        objects = helper.fetch_objects(
            connection=connection,
            api=tz_api.list_all_tzs,
            limit=limit,
            filters=filters,
            dict_unpack_value='timezones',
            subtype=subtype,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]
