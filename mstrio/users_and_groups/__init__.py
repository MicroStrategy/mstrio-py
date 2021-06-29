# flake8: noqa
from typing import Union

from .user import User, create_users_from_csv, list_users
from .user_group import UserGroup, list_user_groups
from .user_connections import UserConnections

UserOrGroup = Union[str, User, UserGroup]
