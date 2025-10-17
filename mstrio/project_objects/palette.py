from logging import getLogger
from typing import TYPE_CHECKING

from requests import Response

from mstrio import config
from mstrio.api import palettes as palettes_api
from mstrio.connection import Connection
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.format import Color
from mstrio.utils.helper import delete_none_values
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.project import Project

logger = getLogger(__name__)


@method_version_handler('11.3.0600')
def list_palettes(
    connection: Connection,
    to_dictionary: bool = False,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
) -> list['Palette'] | list[dict]:
    """List all palettes in the environment.

    Note:
        If no project related parameter is provided, configuration-level
        palettes will be listed.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        to_dictionary: If True, returns a list of dictionaries, otherwise
            returns a list of Palette objects.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
    """
    return Palette._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        project=project,
        project_id=project_id,
        project_name=project_name,
    )


@class_version_handler('11.3.0600')
class Palette(Entity, CopyMixin, DeleteMixin):
    _OBJECT_TYPE = ObjectTypes.PALETTE
    _API_GETTERS = {
        (
            'id',
            'colors',
        ): palettes_api.get_palette,
        (
            'name',
            'description',
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
            'hidden',
        ): objects_processors.get_info,
    }

    @staticmethod
    def _parse_colors(source: list[str], *args, **kwargs) -> list[Color]:
        return [Color(server_value=color) for color in source]

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'colors': _parse_colors,
    }
    _API_PATCH: dict = {
        (
            # the endpoint must take name, while not changing it
            # hence 'name' in both entries
            'name',
            'colors',
        ): (palettes_api.update_palette, 'put'),
        (
            'name',
            'description',
            'abbreviation',
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Initialize a Palette object.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): ID of the palette.
            name (str, optional): Name of the palette.
            project (Project | str | None, optional): Project object or ID or
                name specifying the project. May be used instead of
                `project_id` or `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        if not id:
            if name:
                # not using find_object_with_name as api lacks search by name
                pals_with_name = [
                    c
                    for c in Palette._list_all(
                        connection=connection,
                        project_id=proj_id,
                        to_dictionary=True,
                    )
                    if c['name'] == name
                ]
                if not pals_with_name:
                    raise ValueError(f"Palette with name '{name}' not found.")
                if (num_of_pals := len(pals_with_name)) > 1:
                    raise ValueError(
                        f"Found {num_of_pals} palettes with name '{name}'. "
                        "Please provide 'id' argument."
                    )
                object_id = pals_with_name[0]['id']
            else:
                raise ValueError("Please provide either 'id' or 'name' argument.")
        else:
            object_id = id
        super().__init__(
            connection=connection,
            object_id=object_id,
            name=name,
            project_id=proj_id,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.colors = (
            Palette._parse_colors(cols)
            if (cols := kwargs.get('colors'))
            else default_value
        )

    @staticmethod
    def _color_to_server_value(color: Color | str) -> str:
        return color.server_value if isinstance(color, Color) else color

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        colors: list[Color] | list[str],
        abbreviation: str | None = None,
        description: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> 'Palette':
        """Create a new color palette.

        Note:
            If no project related parameter is provided, configuration-level
            palettes will be created.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            name (str): Name of the new palette.
            colors (list[Color] | list[str]): List of colors in the palette.
                In string format, colors should be in REST format, i.e. a
                single integer, e.g. "16737843" (16,737,843 = 0xff6633)
            abbreviation (str, optional): Abbreviation of the object name.
            description (str, optional): Description of the palette object.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            The newly created palette.
        """

        colors = [
            color.server_value if isinstance(color, Color) else color
            for color in colors
        ]
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )
        body = {
            'name': name,
            'colors': list(map(cls._color_to_server_value, colors)),
            'abbreviation': abbreviation,
            'description': description,
        }
        body = delete_none_values(source=body, recursion=True)
        res: Response = palettes_api.create_palette(
            connection=connection,
            body=body,
            project_id=proj_id,
        )
        new_id = res.json().get('id')
        new_pal = cls(
            connection=connection,
            id=new_id,
            project_id=proj_id,
        )
        if config.verbose:
            # duplicate name won't be accepted and won't create a changed name
            # so we can use the user-provided name
            logger.info(
                f"Successfully created Palette named: '{name}' with ID: '{new_id}'"
            )
        return new_pal

    def alter(
        self,
        name: str | None = None,
        colors: list[Color] | list[str] | None = None,
        abbreviation: str | None = None,
        description: str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the color palette's properties.
        Args:
            name (str, optional): New name of the palette.
            colors (list[Color] | list[str], optional): List of colors in the
                palette. In string format, colors should be in REST format,
                i.e. a single integer, e.g. "16737843" (16,737,843 = 0xff6633)
            abbreviation (str, optional): Abbreviation of the object name.
            description (str, optional): Description of the palette object.
            comments (str, optional): Long description of the palette.
            owner: (str | User, optional): Owner of the palette.
        """
        if isinstance(owner, User):
            owner = owner.id
        if name is None:
            name = self.name
        if colors:
            colors = [Palette._color_to_server_value(color) for color in colors]

        properties = {
            'name': name,
            'colors': colors,
            'abbreviation': abbreviation,
            'description': description,
            'comments': comments,
            'owner': owner,
        }
        properties = delete_none_values(properties, recursion=False)
        self._alter_properties(**properties)
        # update api does not return updated object data, only id;
        # need to fetch the object explicitly
        self.fetch()

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> list['Palette'] | list[dict]:
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        # not using fetch_objects as api lacks pagination
        res: Response = palettes_api.list_palettes(
            connection=connection,
            project_id=proj_id,
            fields='palettes',
        )
        objects = res.json().get('palettes', [])

        # listing api has 'paletteType': 0..1 instead of 'subtype': 17920..17921
        for obj in objects:
            obj['subtype'] = (
                obj.pop('paletteType') + ObjectSubTypes.SYSTEM_PALETTE.value
            )

        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]
