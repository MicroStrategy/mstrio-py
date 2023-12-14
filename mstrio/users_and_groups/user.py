import json
import logging
from datetime import datetime
from enum import Enum, IntFlag
from typing import TYPE_CHECKING

import pandas as pd
from pandas import DataFrame, read_csv
from requests.exceptions import HTTPError

from mstrio import config
from mstrio.access_and_security.privilege_mode import PrivilegeMode
from mstrio.access_and_security.security_role import SecurityRole
from mstrio.connection import Connection
from mstrio.server.language import Language
from mstrio.users_and_groups.user_connections import UserConnections
from mstrio.utils import helper, time_helper
from mstrio.utils.acl import TrusteeACLMixin
from mstrio.utils.entity import DeleteMixin, Entity, ObjectTypes
from mstrio.utils.helper import Dictable, filter_params_for_func
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.response_processors import users
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.access_and_security.privilege import Privilege
    from mstrio.modeling.security_filter import SecurityFilter
    from mstrio.server.project import Project
    from mstrio.users_and_groups.user_group import UserGroup

logger = logging.getLogger(__name__)


def create_users_from_csv(connection: Connection, csv_file: str) -> list["User"]:
    """Create new user objects from csv file. Possible header values for the
    users are the same as in the `User.create()` method.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        csv_file: path to file containing at minimum 'username' and 'full_name'
            headers'.
    """
    return User._create_users_from_csv(connection=connection, csv_file=csv_file)


def list_users(
    connection: Connection,
    name_begins: str | None = None,
    abbreviation_begins: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list["User"] | list[dict]:
    """Get list of user objects or user dicts. Optionally filter the users by
    specifying 'name_begins', 'abbreviation_begins' or other filters.

    Wildcards available for name_begins and abbreviation_begins:
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins: characters that the user name must begin with.
        abbreviation_begins: characters that the abbreviation must begin with.
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'abbreviation',
            'description', 'type', 'subtype', 'date_created', 'date_modified',
            'version', 'acg', 'icon_path', 'owner', 'initials', 'enabled']

    Examples:
        >>> list_users(connection, name_begins='user', initials='UR')
    """
    return User._get_users(
        connection=connection,
        name_begins=name_begins,
        abbreviation_begins=abbreviation_begins,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class User(Entity, DeleteMixin, TrusteeACLMixin, TranslationMixin):
    """Object representation of MicroStrategy User object.

    Attributes:
        connection: A MicroStrategy connection object
        id: User ID
        name: User name
        username: User username
        full_name: full name of the User
        initials: User initials, derived from user's last name or username
        abbreviation: User login name
        description: User description
        memberships: IDs and names of direct parent groups for user
        security_roles: security roles that the user is a member of
        addresses: addresses for the user
        privileges: user privileges per project
        trust_id: Unique user ID provided by trusted authentication provider
        enabled: Specifies if user is allowed to log in
        owner: owner ID and name
        ancestors: List of ancestor folders
        password_modifiable: If user password can be modified
        require_new_password: If user is required to change new password
        standard_auth: If standard authentication is allowed for user
        ldapdn: information about user's LDAP distinguished name
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        version: Version ID
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        default_timezone:  Information about user default timezone
        language: Information about user language
    """

    _PATCH_PATH_TYPES = {
        "name": str,
        "username": str,
        "full_name": str,
        "description": str,
        "password": str,
        "enabled": bool,
        "password_modifiable": bool,
        "password_expiration_date": str,
        "standard_auth": bool,
        "require_new_password": bool,
        "ldapdn": str,
        "trust_id": str,
        "abbreviation": str,
        "owner": str,
    }
    _OBJECT_TYPE = ObjectTypes.USER
    _API_GETTERS = {
        (
            'id',
            'name',
            'type',
            'subtype',
            'ext_type',
            'abbreviation',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'username',
            'full_name',
            'enabled',
            'password_modifiable',
            'require_new_password',
            'standard_auth',
            'memberships',
            'acg',
            'acl',
            'trust_id',
            'initials',
            'default_timezone',
            'ldapdn',
        ): users.get,
        'addresses': users.get_addresses,
        'security_roles': users.get_security_roles,
        'privileges': users.get_privileges,
        ('default_timezone', 'language'): users.get_settings,
    }
    _API_PATCH: dict = {
        (
            'name',
            'abbreviation',
            'username',
            'full_name',
            'enabled',
            'password',
            'description',
            'password_modifiable',
            'require_new_password',
            'password_expiration_date',
            'standard_auth',
            'ldapdn',
            'trust_id',
            'initials',
            'privileges',
            'memberships',
            'addresses',
            'security_roles',
            'default_timezone',
        ): (users.update, 'patch'),
        ('owner'): (objects_processors.update, 'partial_put'),
        ('default_timezone', 'language'): (users.update_user_settings, 'partial_put'),
    }

    @staticmethod
    def _parse_owner(
        source: dict, connection: 'Connection', to_snake_case: bool = True
    ):
        """Parses owner from the API response."""
        from mstrio.users_and_groups import User

        return User.from_dict(source, connection, to_snake_case)

    @staticmethod
    def _parse_language(
        source: dict, connection: 'Connection', to_snake_case: bool = True
    ):
        """Parses language from the API response."""
        if not source['value']:
            return None
        source['id'] = source.pop('value')

        return Language.from_dict(source, connection, to_snake_case)

    @staticmethod
    def _parse_addresses(
        source: list[dict], connection: 'Connection', to_snake_case: bool = True
    ):
        """Parse Adresses from the API response."""
        from mstrio.users_and_groups.contact import ContactAddress

        return [
            ContactAddress.from_dict(contact, connection, to_snake_case)
            for contact in source
        ]

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'password_expiration_date': time_helper.DatetimeFormats.FULLDATETIME,
        'language': _parse_language,
        'owner': _parse_owner,
        'addresses': _parse_addresses,
    }

    def __init__(
        self,
        connection: Connection,
        username: str | None = None,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """Initialize User object by passing username, name, or id.
        When `id` is provided (not `None`), `username` and `name` are omitted.
        When `id` is not provided (`None`) and `username` is provided (not
        `None`), `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            id: ID of User
            username: username of User
            name: name of User
        """
        if id is None and name is None and username is None:
            helper.exception_handler(
                "Please specify either 'id', 'username' or 'name' parameter in the "
                "constructor."
            )

        if id is None:
            users = (
                User._get_user_ids(
                    connection=connection,
                    abbreviation_begins=username,
                    abbreviation=username,
                )
                if username is not None
                else User._get_user_ids(
                    connection=connection,
                    name_begins=name,
                    name=name,
                )
            )

            if users:
                [id] = users
            else:
                temp_name = name if name else username
                helper.exception_handler(
                    f"There is no user: '{temp_name}'", exception_type=ValueError
                )

        super().__init__(
            connection=connection, object_id=id, username=username, name=name
        )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.username = kwargs.get("username")
        self.full_name = kwargs.get("full_name")
        self.enabled = kwargs.get("enabled")
        self.password_modifiable = kwargs.get("password_modifiable")
        self.standard_auth = kwargs.get("standard_auth")
        self.require_new_password = kwargs.get("require_new_password")
        self.ldapdn = kwargs.get("ldapdn")
        self.trust_id = kwargs.get("trust_id")
        self._initials = kwargs.get("initials")
        self._addresses = kwargs.get("addresses")
        self._memberships = kwargs.get("memberships")
        self._security_roles = kwargs.get("security_roles")
        self._privileges = kwargs.get("privileges")
        self._security_filters = kwargs.get("security_filters")
        self._default_timezone = kwargs.get("default_timezone")
        self._language = kwargs.get("language")

    @classmethod
    def create(
        cls,
        connection: Connection,
        username: str,
        full_name: str,
        password: str | None = None,
        description: str | None = None,
        enabled: bool = True,
        password_modifiable: bool = True,
        password_expiration_date: str | datetime | None = None,
        require_new_password: bool = True,
        standard_auth: bool = True,
        ldapdn: str | None = None,
        trust_id: str | None = None,
        database_auth_login: str | None = None,
        memberships: list | None = None,
        language: 'str | Language | None' = None,
        default_timezone: 'str| dict | None' = None,
        owner: 'User | str | None' = None,
    ) -> "User":
        """Create a new user on the I-Server. Returns User object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            username: username of user
            full_name: user full name
            password: user password
            description: user description
            enabled: specifies if user is allowed to log in
            password_modifiable: Specifies if user password can be modified
            password_expiration_date: Expiration date of user password either
                as a datetime or string: "yyyy-MM-dd HH:mm:ss" in UTC
            require_new_password: Specifies if user is required to provide a new
                password.
            standard_auth: Specifies whether standard authentication is allowed
                for user.
            ldapdn: User's LDAP distinguished name
            trust_id: Unique user ID provided by trusted authentication provider
            database_auth_login: Database Authentication Login
            memberships: specify User Group IDs which User will be member off.
            owner: owner of user
            default_timezone: default timezone for user
            language: language for user
        """
        password_expiration_date = time_helper.map_datetime_to_str(
            name='password_expiration_date',
            date=password_expiration_date,
            string_to_date_map=cls._FROM_DICT_MAP,
        )
        body = {
            "username": username,
            "fullName": full_name,
            "description": description,
            "password": password,
            "enabled": enabled,
            "passwordModifiable": password_modifiable,
            "passwordExpirationDate": password_expiration_date,
            "requireNewPassword": require_new_password,
            "standardAuth": standard_auth,
            "ldapdn": ldapdn,
            "trustId": trust_id,
            "databaseAuthLogin": database_auth_login,
            "memberships": memberships,
        }
        body = helper.delete_none_values(body, recursion=True)
        response = users.create(connection, body, username)
        if config.verbose:
            logger.info(
                f"Successfully created user named: '{response.get('username')}' "
                f"with ID: '{response.get('id')}'"
            )
        # User objects are created with default language and timezone
        # in order to change them, you have to go through separate API calls
        user_created = cls.from_dict(source=response, connection=connection)
        user_created.alter(
            language=language, default_timezone=default_timezone, owner=owner
        )
        return user_created

    @classmethod
    def _create_users_from_csv(
        cls, connection: Connection, csv_file: str
    ) -> list["User"]:
        func = cls.create
        args = helper.get_args_from_func(func)
        df = read_csv(csv_file, na_filter=False, usecols=lambda x: x in args)
        user_list = []
        all_param_value_dict = df.to_dict('records')

        for param_value_dict in all_param_value_dict:
            param_value_dict['connection'] = connection
            try:
                temp_user = func(**param_value_dict)
            except HTTPError:
                pass
            else:
                user_list.append(temp_user)

        return user_list

    @classmethod
    def _get_users(
        cls,
        connection: Connection,
        name_begins: str | None = None,
        abbreviation_begins: str | None = None,
        to_dictionary: bool = False,
        limit: int | None = None,
        **filters,
    ) -> list["User"] | list[dict]:
        msg = "Error getting information for a set of users."
        objects = users.get_all(
            connection=connection,
            limit=limit,
            msg=msg,
            name_begins=name_begins,
            abbreviation_begins=abbreviation_begins,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @classmethod
    def _get_user_ids(
        cls,
        connection: Connection,
        name_begins: str | None = None,
        abbreviation_begins: str | None = None,
        limit: int | None = None,
        **filters,
    ) -> list[str]:
        user_dicts = User._get_users(
            connection=connection,
            name_begins=name_begins,
            abbreviation_begins=abbreviation_begins,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [user['id'] for user in user_dicts]

    def alter(
        self,
        username: str | None = None,
        full_name: str | None = None,
        description: str | None = None,
        password: str | None = None,
        enabled: bool | None = None,
        password_modifiable: bool | None = None,
        password_expiration_date: str | None = None,
        standard_auth: bool | None = None,
        require_new_password: bool | None = None,
        ldapdn: str | None = None,
        trust_id: str | None = None,
        database_auth_login: str | None = None,
        owner: 'User | str | None' = None,
        default_timezone: 'str| dict | None' = None,
        language: 'str | Language | None' = None,
    ) -> None:
        """Alter user properties.

        Args:
            username: username of user
            full_name: user full name
            description: user description
            password: user password
            enabled: specifies if user is allowed to log in
            password_modifiable: Specifies if user password can be modified
            password_expiration_date: Expiration date of user password,
                "yyyy-MM-dd HH:mm:ss" in UTC
            standard_auth: Specifies whether standard authentication is allowed
                for user.
            require_new_password: Specifies if user is required to provide a new
                password.
            ldapdn: User's LDAP distinguished name
            trust_id: Unique user ID provided by trusted authentication provider
            database_auth_login: Database Authentication Login
            owner: owner of user
            default_timezone: default timezone for user
            language: language for user
        """
        owner = owner.id if isinstance(owner, User) else owner
        if language:
            language = {
                'value': (language.id if isinstance(language, Language) else language)
            }
        if default_timezone:
            default_timezone = {
                'id': default_timezone['id']
                if isinstance(default_timezone, dict)
                else default_timezone
            }
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    def _create_address_v1(self, name, address, default):
        body = {
            "name": name,
            "deliveryMode": "EMAIL",
            "device": "GENERIC_EMAIL",
            "value": address,
            "default": default,
        }
        users.create_address(self.connection, self.id, body)
        response = users.get_addresses(self.connection, self.id)
        return response

    def _create_address_v2(self, name, address, default, delivery_type, device_id):
        if delivery_type and not device_id and config.verbose:
            msg = (
                f"Could not add address for user '{self.name}'. When you "
                "specify 'delivery_type', you need to add 'device_id' as "
                "well."
            )
            helper.exception_handler(msg, TypeError)
        if device_id and not delivery_type and config.verbose:
            msg = (
                f"Could not add address for user '{self.name}'. When you "
                "specify 'device_id', you need to add 'delivery_type' as "
                "well."
            )
            helper.exception_handler(msg, TypeError)

        body = {
            "name": name,
            "physicalAddress": address,
            "deliveryType": delivery_type,
            "deviceId": device_id,
            "idDefault": default,
        }
        response = users.create_address_v2(self.connection, self.id, body)
        return response

    def add_address(
        self,
        name: str | None = None,
        address: str | None = None,
        default: bool = True,
        delivery_type: str | None = None,
        device_id: str | None = None,
    ) -> None:
        """Add new address to the user object.

        Args:
            name (str): User-specified name for the address
            address (str): The actual value of the address i.e. email address
                associated with this address name/id
            default (bool, optional): Specifies whether this address is the
                default address (change isDefault parameter). Default value is
                set to True.
            delivery_type (str, optional): Delivery type
            device_id (str, optional): Device ID
        """
        if delivery_type or device_id:
            response = self._create_address_v2(
                name=name,
                address=address,
                default=default,
                delivery_type=delivery_type,
                device_id=device_id,
            )
        else:
            response = self._create_address_v1(
                name=name, address=address, default=default
            )
        if response:
            if config.verbose:
                logger.info(f"Added address '{address}' for user '{self.name}'")
            self._addresses = self._parse_addresses(
                response.get('addresses'), self.connection
            )

    def update_address(
        self,
        id: str,
        name: str | None = None,
        address: str | None = None,
        default: bool | None = None,
        delivery_type: str | None = None,
        device_id: str | None = None,
    ) -> None:
        """Update existing address. The address ID has to be specified
        as the name is not unique.

        Args:
            id (str): ID of the address
            name (str, optional): New user-specified name for the address
            address (str, optional): New address value
            default (bool, optional): Whether the address should be (un)marked
                as default
            delivery_type (str, optional): Delivery type
            device_id (str, optional): Device ID
        """
        if not id:
            helper.exception_handler("Please specify 'id' parameter in the method.")

        address_for_update = helper.filter_list_of_dicts(
            [address.to_dict() for address in self.addresses], id=id
        )[0]

        body = {
            'name': name if name else address_for_update['name'],
            'physicalAddress': address
            if address
            else address_for_update['physicalAddress'],
            'deliveryType': delivery_type
            if delivery_type
            else address_for_update['deliveryType'],
            'deviceId': device_id if device_id else address_for_update['deviceId'],
            'isDefault': default if default else address_for_update['isDefault'],
        }
        if users.update_address(self.connection, self.id, id, body):
            if config.verbose:
                logger.info(f"Updated address with ID '{id}' for user '{self.name}'")
            self.fetch("addresses")

    def remove_address(
        self,
        name: str | None = None,
        address: str | None = None,
        id: str | None = None,
    ) -> None:
        """Remove existing address from the user object. Specify either address
        ID or name. Warning, address names are not unique and can potentially
        remove multiple addresses.

        Args:
            name: User-specified name for the address
            address: The actual value of the address i.e. email address
                associated with this address name/id
            id: ID of the address.
        """
        initial_addresses = [address.to_dict() for address in self.addresses]
        if name is None and id is None and address is None or (name and id and address):
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the method."
            )
        if id is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, id=id)
            new_addresses = helper.filter_list_of_dicts(initial_addresses, id=f'!={id}')
        elif address is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, value=address)
            new_addresses = helper.filter_list_of_dicts(
                initial_addresses, value=f'!={address}'
            )
        elif name is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, name=name)
            new_addresses = helper.filter_list_of_dicts(
                initial_addresses, name=f'!={name}'
            )

        for addr in addresses:
            response = users.delete_address(
                self.connection, id=self.id, address_id=addr['id']
            )
            if response:
                if config.verbose:
                    logger.info(
                        f"Removed address '{addr['name']}' with id {addr['id']} "
                        f"from user '{self.name}'"
                    )
                self._addresses = self._parse_addresses(new_addresses, self.connection)

    def add_to_user_groups(
        self, user_groups: "str | UserGroup | list[str | UserGroup]"
    ) -> None:
        """Adds this User to user groups specified in user_groups.

        Args:
            user_groups: list of `UserGroup` objects or IDs
        """
        succeeded, failed = self._update_nested_properties(
            user_groups, "memberships", "add"
        )
        if succeeded and config.verbose:
            logger.info(f"Added user '{self.name}' to group(s): {succeeded}")
        elif failed and config.verbose:
            logger.info(f"User '{self.name}' is already a member of {failed}")

    def remove_from_user_groups(
        self, user_groups: "str | UserGroup | list[str | UserGroup]"
    ) -> None:
        """Removes this User from user groups specified in user_groups.

        Args:
            user_groups: list of `UserGroup` objects or IDs
        """
        succeeded, failed = self._update_nested_properties(
            user_groups, "memberships", "remove"
        )
        if succeeded and config.verbose:
            logger.info(f"Removed user '{self.name}' from group(s): {succeeded}")
        elif failed and config.verbose:
            logger.info(f"User '{self.name}' is not in {failed} group(s)")

    def remove_from_all_user_groups(self) -> None:
        """Removes this User from all user groups."""
        memberships = self.memberships
        existing_ids = [obj.get('id') for obj in memberships]
        self.remove_from_user_groups(user_groups=existing_ids)

    def assign_security_role(
        self, security_role: SecurityRole | str, project: 'Project | str'
    ) -> None:  # NOSONAR
        """Assigns a Security Role to the user for given project.

        Args:
            security_role: Security Role ID or object
            project: Project name or object
        """

        security_role = (
            security_role
            if isinstance(security_role, SecurityRole)
            else SecurityRole(self.connection, id=str(security_role))
        )

        security_role.grant_to([self.id], project)
        if config.verbose:
            logger.info(
                f"Assigned Security Role '{security_role.name}' to user: '{self.name}'"
            )
        self.fetch('security_roles')

    def revoke_security_role(
        self, security_role: SecurityRole | str, project: 'Project | str'
    ) -> None:  # NOSONAR
        """Removes a Security Role from the user for given project.

        Args:
            security_role: Security Role ID or object
            project: Project name or object
        """

        security_role = (
            security_role
            if isinstance(security_role, SecurityRole)
            else SecurityRole(self.connection, id=str(security_role))
        )

        security_role.revoke_from([self.id], project)
        if config.verbose:
            logger.info(
                f"Revoked Security Role '{security_role.name}' from user: '{self.name}'"
            )
        self.fetch('security_roles')

    @method_version_handler('11.3.0200')
    def list_security_filters(
        self, projects: str | list[str] | None = None, to_dictionary: bool = False
    ) -> dict:
        """Get the list of security filters for user. They can be filtered by
        the projects' ids.

        Args:
            projects (str or list of str, optional): collection of projects' ids
                which is used for filtering data
            to_dictionary: If True returns security filters as dicts, by default
                (False) returns them as objects.

        Returns:
            Dictionary with project names as keys and list with security
            filters as values. In case of no security filter for the given user
            in the particular project, then this project is not placed in
            the dictionary.
        """
        from mstrio.modeling.security_filter import SecurityFilter

        objects_ = users.get_security_filters(self.connection, self.id, projects)
        projects_ = objects_.get("projects")

        objects_ = {
            project_.get("name"): project_.get("securityFilters")
            for project_ in projects_
            if project_.get("securityFilters")
        }

        security_filters = {
            name: [
                SecurityFilter.from_dict(sec_filter, self.connection)
                for sec_filter in sec_filters
            ]
            for (name, sec_filters) in objects_.items()
        }
        if to_dictionary:
            return objects_
        return security_filters

    def apply_security_filter(self, security_filter: "SecurityFilter | str") -> bool:
        """Apply a security filter to the user.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be applied to the user.
        Returns:
            True when applying was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.modeling.security_filter import SecurityFilter

            security_filter = SecurityFilter.from_dict(
                {"id": security_filter}, self.connection
            )
        return security_filter.apply(self.id)

    def revoke_security_filter(self, security_filter: "SecurityFilter | str") -> bool:
        """Revoke a security filter from the user.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be revoked from the user.

        Returns:
            True when revoking was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.modeling.security_filter import SecurityFilter

            security_filter = SecurityFilter.from_dict(
                {"id": security_filter}, self.connection
            )
        return security_filter.revoke(self.id)

    def grant_privilege(
        self, privilege: "str | list[str] | Privilege | list[Privilege]"
    ) -> None:
        """Grant privileges directly to the user.

        Args:
            privilege: list of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege

        privileges = [
            priv['id']
            for priv in Privilege._validate_privileges(self.connection, privilege)
        ]
        existing_ids = [
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='GRANTED')
        ]
        succeeded, failed = self._update_nested_properties(
            privileges, "privileges", "add", existing_ids
        )

        if succeeded:
            self.fetch(
                'privileges'
            )  # fetch the object properties and set object attributes
            if config.verbose:
                logger.info(f"Granted privilege(s) {succeeded} to '{self.name}'")
        if failed and config.verbose:
            logger.info(f"User '{self.name}' already has privilege(s) {failed}")

    def revoke_privilege(
        self, privilege: "str | list[str] | Privilege | list[Privilege]"
    ) -> None:
        """Revoke directly granted user privileges.

        Args:
            privilege: list of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege

        privileges = {
            priv['id']
            for priv in Privilege._validate_privileges(self.connection, privilege)
        }
        existing_ids = [
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='ALL')
        ]
        directly_granted = {
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='GRANTED')
        }
        to_revoke = list(privileges.intersection(directly_granted))
        not_directly_granted = list(
            (set(existing_ids) - directly_granted).intersection(privileges)
        )

        if not_directly_granted:
            msg = (
                f"Privileges {sorted(not_directly_granted)} are inherited and will be "
                "omitted. Only directly granted privileges can be revoked by this "
                "method."
            )
            helper.exception_handler(msg, exception_type=Warning)

        succeeded, failed = self._update_nested_properties(
            to_revoke, "privileges", "remove", existing_ids
        )
        if succeeded:
            self.fetch(
                'privileges'
            )  # fetch the object properties and set object attributes
            if config.verbose:
                logger.info(f"Revoked privilege(s) {succeeded} from '{self.name}'")
        if failed and config.verbose:
            logger.warning(f"User '{self.name}' does not have privilege(s) {failed}")

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke directly granted user privileges.

        Args:
            force: If True, no additional prompt will be shown before revoking
                all privileges from User.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to revoke all privileges from user "
                f"'{self.name}'? [Y/N]: "
            )
        if force or user_input == 'Y':
            to_revoke = [
                privilege['privilege']['id']
                for privilege in self.list_privileges(mode='GRANTED')
            ]
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                logger.info(
                    f"User '{self.name}' does not have any directly granted privileges"
                )

    def list_privileges(
        self, mode: PrivilegeMode | str = PrivilegeMode.ALL, to_dataframe: bool = False
    ) -> list:
        """List privileges for user.

        Args:
            mode: Filter by source of privileges. One of: `ALL`, `INHERITED`,
                or `GRANTED`. See: `privilege.PrivilegeMode` enum.
            to_dataframe: If True, return a `DataFrame` object containing
                privileges.
        """
        self.fetch('privileges')

        def to_df(priv_list):
            priv_dict = {}
            for priv in priv_list:
                priv_dict[priv['privilege']['id']] = priv['privilege']['name']
            df = DataFrame.from_dict(priv_dict, orient='index', columns=['Name'])
            df.index.name = 'ID'
            return df

        if not isinstance(mode, PrivilegeMode):
            try:
                mode = PrivilegeMode(mode)
            except ValueError:
                msg = (
                    "Wrong privilege mode has been passed, allowed modes are ['ALL'/"
                    "'INHERITED'/'GRANTED']. See: `privilege.PrivilegeMode` enum."
                )
                helper.exception_handler(msg, ValueError)

        privileges = []
        if mode == PrivilegeMode.ALL:
            privileges = self.privileges
        elif mode == PrivilegeMode.INHERITED:
            for privilege in self.privileges:
                is_inherited = False
                for source in privilege['sources']:
                    is_inherited = not source['direct'] or is_inherited
                if is_inherited:
                    privileges.append(privilege)
        else:  # GRANTED
            for privilege in self.privileges:
                is_granted = False
                for source in privilege['sources']:
                    is_granted = source['direct'] or is_granted
                if is_granted:
                    privileges.append(privilege)

        return to_df(privileges) if to_dataframe else privileges

    def disconnect(self, nodes: str | list[str] | None = None) -> None:
        """Disconnect all active user connection sessions for the specified
        node.

        Args:
            nodes: list of node names
        """
        temp_connections = UserConnections(self.connection)
        temp_connections.disconnect_users(users=self, nodes=nodes)

    def delete(self, force: bool = False) -> bool:
        """Deletes the user.
        Deleting the user will not remove the user's shared files.

                Args:
            force: If True, no additional prompt will be shown before deleting
                User.
        Returns:
            True for success. False otherwise.
        """
        return super().delete(force=force)

    def _to_dataframe_as_columns(
        self, properties: list[str] | None = None
    ) -> pd.DataFrame:
        """Exports user object to dataframe, with properties as columns

        Args:
            properties (list, optional): list of properties to be exported

        Returns: dataframe
        """
        excluded_keys = ['connection']
        selected_keys = properties or (self.list_properties().keys() - excluded_keys)

        def convert(obj, inside=False):
            if isinstance(obj, IntFlag):
                return obj.value
            if isinstance(obj, (str, int)):
                return obj
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, datetime):
                return str(obj)

            result = None

            if isinstance(obj, list):
                result = [convert(el, inside=True) for el in obj]
            if isinstance(obj, Dictable):
                result = dict(sorted(obj.to_dict().items()))
            if isinstance(obj, dict):
                result = {
                    key: convert(value, inside=True) for key, value in obj.items()
                }

            return result if inside else json.dumps(result)

        data = {
            key: convert(value)
            for key, value in self.list_properties().items()
            if key in selected_keys
        }
        return pd.DataFrame(data, index=[0])

    @classmethod
    def to_datafame_from_list(
        cls, objects: list['User'], properties: list[str] | None = None
    ) -> pd.DataFrame:
        """Exports list of user objects to dataframe.
        The properties that are lists, dictionaries, or objects of
        custom classes, are first converted to dictionary using `to_dict()`
        method, then serialized string as json.

        Args:
            objects (list): list of user objects to be exported
            properties (list, optional): list of properties of user object
                to be exported

        Returns: dataframe

        Raises:
            TypeError if `objects` parameter contains objects other than
             of type User
        """
        dataframes = []

        for obj in objects:
            if not isinstance(obj, User):
                raise TypeError('All objects in the list must be of type User.')

            dataframes.append(obj._to_dataframe_as_columns(properties))

        return pd.concat(dataframes, ignore_index=True)

    @classmethod
    def to_csv_from_list(
        cls,
        objects: list['User'],
        path: str | None = None,
        properties: list[str] | None = None,
    ) -> str | None:
        """Exports list of user objects to csv (if path is provided)
        or to string (if path is not provided).
        The properties that are lists, dictionaries, or objects of
        custom classes, are first converted to dictionary using `to_dict()`
        method, then serialized string as json.

        Args:
            objects (list): list of user objects to be exported
            path (str, optional): a path specifying where to save the csv file
            properties (list, optional): list of properties of user object
                to be exported

        Returns: str or None

        Raises:
            TypeError if `objects` parameter contains objects other than
             of type User
        """
        dataframe = cls.to_datafame_from_list(objects, properties)
        return dataframe.to_csv(index=False, path_or_buf=path)

    @property
    def memberships(self):
        return self._memberships

    @property
    def initials(self):
        return self._initials

    @property
    def addresses(self):
        return self._addresses

    @property
    def security_roles(self):
        return self._security_roles

    @property
    def privileges(self):
        self.fetch('privileges')
        return self._privileges

    @property
    @method_version_handler('11.3.0500')
    def default_timezone(self):
        return self._default_timezone

    @property
    @method_version_handler('11.3.0700')
    def language(self):
        return self._language

    @property
    def security_filters(self):
        if not self._security_filters:
            self._security_filters = self.list_security_filters()
        return self._security_filters
