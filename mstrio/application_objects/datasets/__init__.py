# flake8: noqa
from mstrio.project_objects.datasets.cube import list_all_cubes, load_cube
from mstrio.project_objects.datasets.cube_cache import (CubeCache, delete_cube_cache,
                                                        delete_cube_caches, list_cube_caches)
from mstrio.project_objects.datasets.olap_cube import list_olap_cubes, OlapCube
from mstrio.project_objects.datasets.super_cube import list_super_cubes, SuperCube
from mstrio.utils.helper import deprecation_warning

deprecation_warning(
    'mstrio.application_objects.datasets',
    'mstrio.project_objects.datasets',
    '11.3.4.101',  # NOSONAR
    False)
