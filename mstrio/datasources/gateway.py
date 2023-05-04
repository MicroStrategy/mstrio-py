from typing import Optional, Type

from mstrio.connection import Connection
from mstrio.datasources.helpers import DBType, GatewayType
from mstrio.utils.entity import EntityBase
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import _prepare_objects as filter_objects
from mstrio.utils.response_processors import gateways
from mstrio.utils.version_helper import class_version_handler


def list_gateways(
    connection: Connection, to_dictionary: bool = False, **filters
) -> list['Gateway'] | list[dict]:
    """Get all gateways as list of Gateway objects or dictionaries.

    Optionally filter the gateways by specifying filters.

    Args:
        connection (Connection): MicroStrategy connection object
        to_dictionary (bool): If True returns a list of Gateway dicts,
           otherwise returns a list of Gateway objects
       **filters: Available filter parameters:
           ['id', 'name', 'gateway_type', 'db_type', 'is_certified']
    """
    return Gateway.list(connection, to_dictionary, **filters)


@class_version_handler('11.3.0960')
class Gateway(EntityBase):
    """Object representation of Microstrategy Gateway

    Attributes:
        id: Gateway's ID
        name: Gateway's name
        gateway_type: Gateway's type
        db_type: Database type
        is_certified: Specifies if a gateway is certified
    """

    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'db_type': DBType,
        'gateway_type': GatewayType,
    }
    _API_GETTERS = {
        (
            'id',
            'name',
            'gateway_type',
            'db_type',
            'is_certified',
        ): gateways.get
    }

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Initialize Driver object by passing ID or name.
        When `id` is provided, `name` is omitted.

        Args:
            connection (Connection): MicroStrategy connection object
            id (str): ID of Driver
            name (str): name of Driver
        """

        if id is None and name is None:
            raise ValueError(
                "Please specify either 'id' or 'name' parameter in the constructor."
            )

        if id is None:
            result: list[dict] = self.list(connection, name=name, to_dictionary=True)

            if result:
                object_data = result[0]
                self._init_variables(**object_data, connection=connection)
            else:
                raise ValueError(f"There is no Gateway named: '{name}'.")
        elif id == '':
            raise ValueError("Gateway's ID cannot be an empty string.")
        else:
            super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self.gateway_type = (
            GatewayType(kwargs.get('gateway_type'))
            if kwargs.get('gateway_type')
            else None
        )
        self.db_type = DBType(kwargs.get('db_type')) if kwargs.get('db_type') else None
        self.is_certified = kwargs.get('is_certified')

    @classmethod
    def list(
        cls, connection: Connection, to_dictionary: bool = False, **filters
    ) -> list[Type['Gateway']] | list[dict]:
        """Get all gateways as list of Gateway objects or dictionaries.

        Optionally filter the gateways by specifying filters.

        Args:
            connection (Connection): MicroStrategy connection object
            to_dictionary (bool): If True returns a list of Gateway dicts,
               otherwise returns a list of Gateway objects
           **filters: Available filter parameters:
               ['id', 'name', 'gateway_type', 'db_type', 'is_certified']
        """

        if gateway_type := filters.get('gateway_type'):
            filters['gateway_type'] = get_enum_val(gateway_type, GatewayType)

        if db_type := filters.get('db_type'):
            filters['db_type'] = get_enum_val(db_type, DBType)

        objects = filter_objects(gateways.get_all(connection), filters)

        if to_dictionary:
            return objects

        return cls.bulk_from_dict(source_list=objects, connection=connection)
