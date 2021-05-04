from mstrio.users_and_groups.user_group import UserGroup, list_usergroups  # noqa: F401
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.usergroup", "mstrio.users_and_groups.user_group", "11.3.2.101")
