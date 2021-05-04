from mstrio.users_and_groups.user_connections import UserConnections  # noqa: F401
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.user_connections", "mstrio.users_and_groups.user_connections",
                    "11.3.2.101")
