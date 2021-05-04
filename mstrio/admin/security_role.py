from mstrio.access_and_security.security_role import (  # noqa: F401
    list_security_roles, SecurityRole)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.security_role", "mstrio.access_and_security.security_role",
                    "11.3.2.101")
