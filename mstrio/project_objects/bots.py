from typing import TYPE_CHECKING

from mstrio.types import ObjectSubTypes
from mstrio.utils.helper import deprecation_warning, find_object_with_name

from .agents import Agent, _list_implementation

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server.project import Project


DEPRECATION_VERSION = "11.6.1.101"  # NOSONAR


def list_bots(
    connection: 'Connection',
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    **filters,
) -> list['Bot'] | list[dict]:
    """Get a list of Bots.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        name (str, optional): characters that the dashboard name must contain
        to_dictionary (bool, optional): if True, return Bots as a
            list of dicts
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version',
            'owner', 'ext_type', 'view_media', 'certified_info']

    Returns:
        A list of Bots objects or dictionaries.
    """
    deprecation_warning('list_bots', None, DEPRECATION_VERSION, module=False)

    return _list_implementation(
        Bot,
        connection=connection,
        name=name,
        to_dictionary=to_dictionary,
        limit=limit,
        project=project,
        project_id=project_id,
        project_name=project_name,
        **filters,
    )


class Bot(Agent):
    _OBJECT_SUBTYPES = [ObjectSubTypes.DOCUMENT_BOT] + Agent._OBJECT_SUBTYPES

    def __init__(
        self, connection: 'Connection', name: str | None = None, id: str | None = None
    ) -> None:
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")

            bot = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_bots,
            )
            id = bot['id']
        super().__init__(
            connection=connection,
            id=id,
            name=name,
        )

        deprecation_warning(
            'mstrio.project_objects.bots',
            (
                'mstrio.project_objects.agents'
                if self._subtype in Agent._get_subtypes_as_raw_values()
                else None
            ),
            DEPRECATION_VERSION,
        )
