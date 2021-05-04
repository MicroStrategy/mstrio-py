from mstrio.application_objects.datasets.cube import _Cube, CubeStates  # noqa: F401
from mstrio.utils.helper import deprecation_warning

Cube = _Cube

deprecation_warning(
    "mstrio.cube",
    ("mstrio.application_objects.datasets.super_cube "
     "and mstrio.application_objects.datasets.olap_cube"),
    "11.3.2.101",
)
