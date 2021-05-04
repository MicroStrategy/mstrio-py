from mstrio.server.application import (  # noqa: F401
    Application, ApplicationSettings, compare_application_settings, ProjectStatus)
from mstrio.server.environment import Environment  # noqa: F401
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.application",
                    "mstrio.server.application and mstrio.server.environment", "11.3.2.101")
