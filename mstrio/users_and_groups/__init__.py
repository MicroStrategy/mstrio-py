# flake8: noqa
from typing import Union

from .user import create_users_from_csv, list_users, User
from .user_connections import UserConnections
from .user_group import list_user_groups, UserGroup

# those import has to be below import of `User` to avoid circular imports
from .contact import Contact, ContactAddress, ContactDeliveryType, list_contacts
from .contact_group import (
    ContactGroup, ContactGroupMember, ContactGroupMemberType, list_contact_groups
)

UserOrGroup = Union[str, User, UserGroup]
