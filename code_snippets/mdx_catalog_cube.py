"""This is the demo script to show how to manage MDX catalog cubes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling.mdx_catalog_cube import (
    MDXCatalogCube,
    list_mdx_catalog_cubes,
)


PROJECT_NAME = $project_name  # Insert project name here
MDX_DATASOURCE = $mdx_datasource  # Insert MDX datasource ID or name here
MDX_CATALOG_CUBE_ID = $mdx_catalog_cube_id
MDX_CATALOG_CUBE_NAME = $mdx_catalog_cube_name

conn = get_connection(connectionData, project_name=PROJECT_NAME)

# List imported MDX catalog cubes from the selected datasource
mdx_catalog_cubes = list_mdx_catalog_cubes(
    connection=conn,
    mdx_datasource=MDX_DATASOURCE,
)
mdx_catalog_cubes_as_dicts = list_mdx_catalog_cubes(
    connection=conn,
    mdx_datasource=MDX_DATASOURCE,
    to_dictionary=True,
)

# Initialize an MDX catalog cube by ID or name
mdx_catalog_cube = MDXCatalogCube(
    connection=conn,
    id=MDX_CATALOG_CUBE_ID,
)
mdx_catalog_cube_by_name = MDXCatalogCube(
    connection=conn,
    name=MDX_CATALOG_CUBE_NAME,
    mdx_datasource=MDX_DATASOURCE,
)

# Retarget an imported MDX catalog cube
NEW_MDX_CATALOG_NAME = $new_mdx_catalog_name
NEW_MDX_CUBE_NAME = $new_mdx_cube_name

mdx_catalog_cube.alter(
    mdx_catalog_name=NEW_MDX_CATALOG_NAME,
    mdx_cube_name=NEW_MDX_CUBE_NAME,
)
