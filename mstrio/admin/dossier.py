from mstrio.application_objects.dossier import (  # noqa: F401
    Dossier, list_dossiers, list_dossiers_across_projects)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.dossier", "mstrio.application_objects.dossier", "11.3.2.101")
