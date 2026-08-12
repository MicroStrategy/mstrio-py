import logging
from typing import TYPE_CHECKING, Any

from mstrio.api import mdx_data_sources
from mstrio.connection import Connection
from mstrio.datasources.datasource_instance import DatasourceInstance
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import Entity
from mstrio.utils.helper import delete_none_values
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import mdx_catalog_cube as mdx_processor
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.project import Project

MDX_DATABASE_TYPES = mdx_processor.MDX_DATABASE_TYPES

logger = logging.getLogger(__name__)

_MDX_CATALOG_CUBE_MIN_SERVER_VERSION = '11.6.0800'


@method_version_handler(_MDX_CATALOG_CUBE_MIN_SERVER_VERSION)
def list_mdx_catalog_cubes(
    connection: Connection,
    mdx_datasource: DatasourceInstance | str | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
) -> list['MDXCatalogCube'] | list[dict[str, Any]]:
    """List MDX catalog cubes for the given datasource(s) and project.

    Note:
        The current API response contains imported cubes only.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        mdx_datasource (DatasourceInstance | str, optional): MDX datasource
            object, ID, or name. If not provided, cubes from all MDX
            datasources are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID.
        project_name (str, optional): Project name.
        to_dictionary (bool, optional): If True, return dictionaries instead
            of objects.
        limit (int, optional): Maximum number of rows returned.

    Returns:
        list[MDXCatalogCube] | list[dict[str, Any]]: MDX catalog cube objects
            or dictionaries.
    """
    resolved_project_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )
    datasource_ids = (
        [mdx_processor.resolve_mdx_datasource_id(connection, mdx_datasource)]
        if mdx_datasource is not None
        else [
            datasource['id']
            for datasource in mdx_processor.list_mdx_datasources(connection)
        ]
    )

    rows = []
    for datasource_id in datasource_ids:
        payload = mdx_processor.get_mdx_catalog_payload(
            connection,
            datasource_id,
            resolved_project_id,
        )
        rows.extend(
            {
                **row,
                'mdx_datasource': {'id': datasource_id},
            }
            for row in mdx_processor.get_catalog_rows(payload)
        )

    if limit is not None:
        rows = rows[:limit]

    return (
        rows
        if to_dictionary
        else MDXCatalogCube.bulk_from_dict(source_list=rows, connection=connection)
    )


@class_version_handler(_MDX_CATALOG_CUBE_MIN_SERVER_VERSION)
class MDXCatalogCube(Entity):
    """Representation of an imported or available MDX catalog cube."""

    _OBJECT_TYPE = ObjectTypes.TABLE
    _OBJECT_SUBTYPES = [ObjectSubTypes.TABLE]
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'type': ObjectTypes,
        'mdx_datasource': DatasourceInstance.from_dict,
    }
    _API_GETTERS = {
        (
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
            'project_id',
            'hidden',
            'target_info',
        ): objects_processors.get_info,
        (
            'id',
            'name',
            'mdx_datasource',
        ): mdx_processor.get_mdx_catalog_cube,
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
        mdx_datasource: DatasourceInstance | str | None = None,
    ) -> None:
        """Initialize an MDX catalog cube.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            id (str, optional): ID of the MDX catalog cube
                from MDX cube catalog.
            name (str, optional): Name of the MDX catalog cube
                from MDX cube catalog.
            mdx_datasource (DatasourceInstance | str, optional): MDX
                datasource object, name, or ID used to limit lookup. This is
                useful when `name` is provided and multiple datasources
                contain mdx catalog cubes with the same name.

        Raises:
            ValueError: If neither `id` nor `name` is provided, if no project
                is selected, or if the object cannot be found.
        """

        cube_data = mdx_processor.get_mdx_catalog_cube(
            connection=connection,
            id=id,
            name=name,
            mdx_datasource=mdx_datasource,
        )
        if not cube_data:
            identifier = id or name
            raise ValueError(f"MDXCatalogCube '{identifier}' was not found.")

        id = cube_data.pop('id')

        super().__init__(connection=connection, object_id=id, **cube_data)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._imported: bool = kwargs.get('imported', True)
        self._mdx_datasource: DatasourceInstance | None = (
            DatasourceInstance.from_dict(
                kwargs.get('mdx_datasource'),
                self.connection,
            )
            if isinstance(kwargs.get('mdx_datasource'), dict)
            else kwargs.get('mdx_datasource', default_value)
        )

    def alter(
        self,
        mdx_catalog_name: str | None = None,
        mdx_cube_name: str | None = None,
    ) -> None:
        """Retarget the imported MDX catalog cube
        to a different external catalog and/or cube.

        Args:
            mdx_catalog_name (str, optional): New external MDX catalog name.
            mdx_cube_name (str, optional): New external MDX cube name.

        Raises:
            ValueError: If the cube is not imported or both parameters are not
                provided.
        """
        if not self.imported or not self.id:
            raise ValueError('Only imported MDX catalog cubes can be altered.')

        body = delete_none_values(
            {
                'mdxCatalogName': mdx_catalog_name,
                'mdxCubeName': mdx_cube_name,
            },
            recursion=False,
        )
        if not body:
            raise ValueError(
                'At least one of `mdx_catalog_name` or `mdx_cube_name` must be '
                'provided.'
            )
        datasource_id = self._mdx_datasource.id if self._mdx_datasource else None
        if not datasource_id:
            raise ValueError(
                'Cannot alter MDX catalog cube because MDX datasource ID is '
                'missing. Reinitialize MDXCatalogCube with the '
                '`mdx_datasource` parameter (ID, name, or DatasourceInstance) '
                'and try again.'
            )

        mdx_data_sources.alter_mdx_cube(
            connection=self.connection,
            datasource_id=datasource_id,
            id=self.id,
            body=body,
        )

    @property
    def imported(self) -> bool:
        return self._imported

    @property
    def mdx_datasource(self) -> DatasourceInstance | None:
        return self._mdx_datasource
