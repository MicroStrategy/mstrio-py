from typing import List, Optional, TYPE_CHECKING, Union

from pandas import DataFrame, read_csv
from requests.exceptions import HTTPError

from mstrio.access_and_security.security_role import SecurityRole
from mstrio.api import users
import mstrio.config as config
from mstrio.connection import Connection
from mstrio.users_and_groups.user_connections import UserConnections
from mstrio.utils import helper
from mstrio.utils.entity import (Entity, ObjectTypes, Permissions, set_custom_permissions,
                                 set_permission)
from mstrio.access_and_security.privilege_mode import PrivilegeMode

if TYPE_CHECKING:
    from mstrio.access_and_security.privilege import Privilege
    from mstrio.server.application import Application
    from mstrio.users_and_groups.user_group import UserGroup


def create_users_from_csv(connection: Connection, csv_file: str) -> List["User"]:
    """Create new user objects from csv file. Possible header values for the
    users are the same as in the `User.create()` method.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        csv_file: path to file containing at minimum 'username' and 'full_name'
            headers'.
    """
    return User._create_users_from_csv(connection=connection, csv_file=csv_file)


def list_users(connection: Connection, name_begins: Optional[str] = None,
               abbreviation_begins: Optional[str] = None, to_dictionary: bool = False,
               limit: Optional[int] = None, **filters) -> Union[List["User"], List[dict]]:
    """Get list of user objects or user dicts. Optionally filter the users by
    specifying 'name_begins', 'abbreviation_begins' or other filters.

    Wildcards available for name_begins and abbreviation_begins:
        ? - any character
        * - 0 or more of any characters
        e.g name_begins = ?onny wil return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins: characters that the user name must begin with.
        abbreviation_begins: characters that the abbreviation must begin with.
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None`, all objects are
            returned.
        **filters: Available filter parameters: ['id', 'name', 'abbreviation',
            'description', 'type', 'subtype', 'date_created', 'date_modified',
            'version', 'acg', 'icon_path', 'owner', 'initials']

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


class User(Entity):
    """Object representation of MicroStrategy User object.

    Attributes:
        connection: A MicroStrategy connection object
        id: User ID
        name: User name
        username: User username
        full_name: full name of the User
        intitials: User initials, derived from user's last name or username
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
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd HH:mm:ss" in UTC
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        version: Version ID
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
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
    }
    _OBJECT_TYPE = ObjectTypes.USER
    _API_GETTERS = {
        ('id', 'name', 'type', 'subtype', 'ext_type', 'abbreviation', 'date_created',
         'date_modified', 'version', 'owner', 'ancestors', 'username', 'full_name', 'enabled',
         'password_modifiable', 'require_new_password', 'standard_auth', 'memberships', 'acg',
         'acl', 'trust_id', 'initials'): users.get_user_info,
        'addresses': users.get_addresses,
        'security_roles': users.get_user_security_roles,
        'privileges': users.get_user_privileges,
    }
    # TODO add basic patch endpoint from entity similar to _API_GETTERS
    _API_PATCH = [users.update_user_info]

    def __init__(self, connection: Connection, username: Optional[str] = None,
                 name: Optional[str] = None, id: Optional[str] = None) -> None:
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
                "Please specify either 'id', 'username' or 'name' parameter in the constructor.")

        if id is None:
            users = User._get_user_ids(
                connection=connection,
                abbreviation_begins=username,
                abbreviation=username,
            ) if username is not None else User._get_user_ids(
                connection=connection,
                name_begins=name,
                name=name,
            )

            if users:
                [id] = users
            else:
                temp_name = name if name else username
                helper.exception_handler("There is no user: '{}'".format(temp_name),
                                         exception_type=ValueError)

        super().__init__(connection=connection, object_id=id, username=username, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.username = kwargs.get("username")
        self.full_name = kwargs.get("full_name")
        self.enabled = kwargs.get("enabled")
        self.password_modifiable = kwargs.get("password_modifiable")
        self.password_expiration_date = kwargs.get("password_expiration_date")
        self.standard_auth = kwargs.get("standard_auth")
        self.require_new_password = kwargs.get("require_new_password")
        self.ldapdn = kwargs.get("ldapdn")
        self.trust_id = kwargs.get("trust_id")

        self._initials = kwargs.get("initials")
        self._addresses = kwargs.get("addresses")
        self._memberships = kwargs.get("memberships")
        self._security_roles = kwargs.get("security_roles")
        self._privileges = kwargs.get("privileges")

    @classmethod
    def create(cls, connection: Connection, username: str, full_name: str,
               password: Optional[str] = None, description: Optional[str] = None,
               enabled: bool = True, password_modifiable: bool = True,
               password_expiration_date: Optional[str] = None, require_new_password: bool = True,
               standard_auth: bool = True, ldapdn: Optional[str] = None,
               trust_id: Optional[str] = None, database_auth_login: Optional[str] = None,
               memberships: list = []) -> "User":
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
            password_expiration_date: Expiration date of user password,
                "yyyy-MM-dd HH:mm:ss" in UTC
            require_new_password: Specifies if user is required to provide a new
                password.
            standard_auth: Specifies whether standard authentication is allowed
                for user.
            ldapdn: User's LDAP distinguished name
            trust_id: Unique user ID provided by trusted authentication provider
            database_auth_login: Database Authentication Login
            memberships: specify User Groups which User will be member.
        """
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
            "memberships": memberships
        }
        response = users.create_user(connection, body).json()
        if config.verbose:
            print("Successfully created user named: '{}' with ID: '{}'".format(
                response.get('username'), response.get('id')))
        return cls.from_dict(source=response, connection=connection)

    @classmethod
    def _create_users_from_csv(cls, connection: Connection, csv_file: str) -> List["User"]:
        func = cls.create
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
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
    def _get_users(cls, connection: Connection, name_begins: Optional[str] = None,
                   abbreviation_begins: Optional[str] = None, to_dictionary: bool = False,
                   limit: Optional[int] = None, **filters) -> Union[List["User"], List[dict]]:
        msg = "Error getting information for a set of users."
        objects = helper.fetch_objects_async(
            connection,
            users.get_users_info,
            users.get_users_info_async,
            limit=limit,
            chunk_size=1000,
            error_msg=msg,
            name_begins=name_begins,
            abbreviation_begins=abbreviation_begins,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @classmethod
    def _get_user_ids(cls, connection: Connection, name_begins: Optional[str] = None,
                      abbreviation_begins: Optional[str] = None, limit: Optional[int] = None,
                      **filters) -> List[str]:
        user_dicts = User._get_users(
            connection=connection,
            name_begins=name_begins,
            abbreviation_begins=abbreviation_begins,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [user['id'] for user in user_dicts]

    def alter(self, username: Optional[str] = None, full_name: Optional[str] = None,
              description: Optional[str] = None, password: Optional[str] = None,
              enabled: Optional[bool] = None, password_modifiable: Optional[bool] = None,
              password_expiration_date: Optional[str] = None, standard_auth: Optional[bool] = None,
              require_new_password: Optional[bool] = None, ldapdn: Optional[str] = None,
              trust_id: Optional[str] = None, database_auth_login: Optional[str] = None) -> None:
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
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        self._alter_properties(**properties)

    def add_address(self, name: Optional[str] = None, address: Optional[str] = None,
                    default: bool = True) -> None:
        """Add new address to the user object.

        Args:
            name: User-specified name for the address
            address: The actual value of the address i.e. email address
                associated with this address name/id
            default: Specifies whether this address is the default address
                (change isDefault parameter).
        """
        helper.validate_param_value('address', address, str, regex=r"[^@]+@[^@]+\.[^@]+",
                                    valid_example="name@mail.com")
        helper.validate_param_value('name', name, str)
        helper.validate_param_value('default', default, bool)
        body = {
            "name": name,
            "deliveryMode": "EMAIL",
            "device": "GENERIC_EMAIL",
            "value": address,
            "default": default
        }
        response = users.create_address(self.connection, self.id, body)
        if response.ok:
            if config.verbose:
                print("Added address '{}' for user '{}'".format(address, self.name))
            setattr(self, "_addresses", response.json().get('addresses'))

    def remove_address(self, name: Optional[str] = None, address: Optional[str] = None,
                       id: Optional[str] = None) -> None:
        """Remove existing address from the user object. Specify either address
        ID or name. Warning, address names are not unique and can potentially
        remove multiple addresses.

        Args:
            name: User-specified name for the address
            address: The actual value of the address i.e. email address
                associated with this address name/id
            id: ID of the address.
        """
        initial_addresses = self.addresses
        if name is None and id is None and address is None or (name and id and address):
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the method.")
        if id is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, id=id)
            new_addresses = helper.filter_list_of_dicts(initial_addresses, id='!={}'.format(id))
        elif address is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, value=address)
            new_addresses = helper.filter_list_of_dicts(initial_addresses,
                                                        value='!={}'.format(address))
        elif name is not None:
            addresses = helper.filter_list_of_dicts(initial_addresses, name=name)
            new_addresses = helper.filter_list_of_dicts(initial_addresses,
                                                        name='!={}'.format(name))

        for addr in addresses:
            response = users.delete_address(self.connection, id=self.id, address_id=addr['id'])
            if response.ok:
                if config.verbose:
                    print("Removed address '{}' with id {} from user '{}'".format(
                        addr['name'], addr['id'], self.name))
                setattr(self, "_addresses", new_addresses)

    def delete(self, force: bool = False) -> bool:
        """Deletes the user.

        Deleting the user will not remove the user's shared files.

        Args:
            force: If True, no additional prompt will be showed before deleting
                User.

        Returns:
            True for success. False otherwise.
        """
        user_input = 'N'
        if not force:
            user_input = input((f"Deleting the user will not remove the user's shared files. Are "
                                f"you sure you want to delete user '{self.name}' with ID: "
                                f"{self.id}? [Y/N]: "))
        if force or user_input == 'Y':
            response = users.delete_user(self.connection, self.id)
            if response.status_code == 204 and config.verbose:
                print("Successfully deleted user {}".format(self.name))
            return response.ok
        else:
            return False

    def add_to_user_groups(
            self, user_groups: Union[str, "UserGroup", List[Union[str, "UserGroup"]]]) -> None:
        """Adds this User to user groups specified in user_groups.

        Args:
            user_groups: list of `UserGroup` objects or IDs
        """
        succeeded, failed = self._update_nested_properties(user_groups, "memberships", "add")
        if succeeded and config.verbose:
            print("Added user '{}' to group(s): {}".format(self.name, succeeded))
        elif failed and config.verbose:
            print("User {} is already a member of {}".format(self.name, failed))

    def remove_from_user_groups(
            self, user_groups: Union[str, "UserGroup", List[Union[str, "UserGroup"]]]) -> None:
        """Removes this User from user groups specified in user_groups.

        Args:
            user_groups: list of `UserGroup` objects or IDs
        """
        succeeded, failed = self._update_nested_properties(user_groups, "memberships", "remove")
        if succeeded and config.verbose:
            print("Removed user '{}' from group(s): {}".format(self.name, succeeded))
        elif failed and config.verbose:
            print("User {} is not in {} group(s)".format(self.name, failed))

    def remove_from_all_user_groups(self) -> None:
        """Removes this User from all user groups."""
        memberships = getattr(self, 'memberships')
        existing_ids = [obj.get('id') for obj in memberships]
        self.remove_from_user_groups(user_groups=existing_ids)

    def set_permission(self, permission: Permissions, to_objects: Union[str, List[str]],
                       object_type: ObjectTypes,
                       application: Optional[Union[str, "Application"]] = None,
                       propagate_to_children: Optional[bool] = None):
        """Set permission to perform actions on given object(s).

        Function is used to set permission of the trustee to perform given
        actions on the provided objects. Within one execution of the function
        permission will be set in the same manner for each of the provided
        objects.
        Permission is the predefined set of rights. All objects to which the
        rights will be given have to be of the same type which is also provided.

        Args:
            permission: The Permission which defines set of rights.
                See: `Permissions` enum
            to_objects: (str, list(str)): List of object ids on access list
                to which the permissions will be set
            object_type: Type of objects on access list
            application (str, Application): Object or id of Application in which
                the object is located. If not passed, Application
                (application_id) selected in Connection object is used.
            propagate_to_children: Flag used in the request to determine if
                those rights will be propagated to children of the user group
        """
        set_permission(connection=self.connection, trustee_id=self.id, permission=permission,
                       to_objects=to_objects, object_type=object_type, application=application,
                       propagate_to_children=propagate_to_children)

    def set_custom_permissions(self, to_objects: Union[str, List[str]], object_type: ObjectTypes,
                               application: Optional[Union[str, "Application"]] = None,
                               execute: Optional[str] = None, use: Optional[str] = None,
                               control: Optional[str] = None, delete: Optional[str] = None,
                               write: Optional[str] = None, read: Optional[str] = None,
                               browse: Optional[str] = None):
        """Set custom permissions to perform actions on given object(s).

        Function is used to set rights of the trustee to perform given actions
        on the provided objects. Within one execution of the function rights
        will be set in the same manner for each of the provided objects.
        None of the rights is necessary, but if provided then only possible
        values are 'grant' (to grant right), 'deny' (to deny right), 'default'
        (to reset right) or None which is default value and means that nothing
        will be changed for this right. All objects to which the rights will be
        given have to be of the same type which is also provided.

        Args:
            to_objects: (str, list(str)): List of object ids on access list to
                which the permissions will be set
            object_type (int): Type of objects on access list
            application (str, Application): Object or id of Application in which
                the object is located. If not passed, Application
                (application_id) selected in Connection object is used.
            execute (str): value for right "Execute". Available are 'grant',
                'deny', 'default' or None
            use (str): value for right "Use". Available are 'grant',
                'deny', 'default' or None
            control (str): value for right "Control". Available are 'grant',
                'deny', 'default' or None
            delete (str): value for right "Delete". Available are 'grant',
                'deny', 'default' or None
            write  (str): value for right "Write". Available are 'grant',
                'deny', 'default' or None
            read (str): value for right "Read". Available are 'grant',
                'deny', 'default' or None
            browse (str): value for right "Browse. Available are 'grant',
                'deny', 'default' or None
        """
        set_custom_permissions(connection=self.connection, trustee_id=self.id,
                               to_objects=to_objects, object_type=object_type,
                               application=application, execute=execute, use=use, control=control,
                               delete=delete, write=write, read=read, browse=browse)

    def assign_security_role(self, security_role: Union[SecurityRole, str],
                             application: Union["Application", str]) -> None:
        """Assigns a Security Role to the user for given application.

        Args:
            security_role: Security Role ID or object
            application: Application name or object
        """
        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.grant_to([self.id], application)
        if config.verbose:
            print("Assigned Security Role '{}' to user: '{}'".format(security_role.name,
                                                                     self.name))

    def revoke_security_role(self, security_role: Union[SecurityRole, str],
                             application: Union["Application", str]) -> None:
        """Removes a Security Role from the user for given application.

        Args:
            security_role: Security Role ID or object
            application: Application name or object
        """
        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.revoke_from([self.id], application)
        if config.verbose:
            print("Revoked Security Role '{}' from user: '{}'".format(
                security_role.name, self.name))

    def grant_privilege(self, privilege: Union[str, List[str], "Privilege",
                                               List["Privilege"]]) -> None:
        """Grant privileges directly to the user.

        Args:
            privilege: list of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege
        privileges = [
            priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)
        ]
        existing_ids = [
            privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')
        ]
        succeeded, failed = self._update_nested_properties(privileges, "privileges", "add",
                                                           existing_ids)

        if succeeded:
            self.fetch('privileges')  # fetch the object properties and set object attributes
            if config.verbose:
                print("Granted privilege(s) {} to '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User '{}' already has privilege(s) {}".format(self.name, failed))

    def revoke_privilege(self, privilege: Union[str, List[str], "Privilege",
                                                List["Privilege"]]) -> None:
        """Revoke directly granted user privileges.

        Args:
            privilege: list of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege
        privileges = set(
            [priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)])
        existing_ids = [
            privilege['privilege']['id'] for privilege in self.list_privileges(mode='ALL')
        ]
        directly_granted = set(
            [privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')])
        to_revoke = list(privileges.intersection(directly_granted))
        not_directly_granted = list(
            (set(existing_ids) - directly_granted).intersection(privileges))

        if not_directly_granted:
            msg = (f"Privileges {sorted(not_directly_granted)} are inherited and will be ommited. "
                   "Only directly granted privileges can be revoked by this method.")
            helper.exception_handler(msg, exception_type=Warning)

        succeeded, failed = self._update_nested_properties(to_revoke, "privileges", "remove",
                                                           existing_ids)
        if succeeded:
            self.fetch('privileges')  # fetch the object properties and set object attributes
            if config.verbose:
                print("Revoked privilege(s) {} from '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User '{}' does not have privilege(s) {}".format(self.name, failed))

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke directly granted user privileges.

        Args:
            force: If True, no additional prompt will be showed before revoking
                all privileges from User.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to revoke all privileges from user '{}'? [Y/N]: ".format(
                    self.name))
        if force or user_input == 'Y':
            to_revoke = [
                privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')
            ]
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                print("User '{}' does not have any directly granted privileges".format(self.name))

    def list_privileges(self, mode: PrivilegeMode = PrivilegeMode.ALL,
                        to_dataframe: bool = False) -> list:
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
                msg = ("Wrong privilege mode has been passed, allowed modes are "
                       "['ALL'/'INHERITED'/'GRANTED']. See: `privilege.PrivilegeMode` enum.")
                helper.exception_handler(msg, ValueError)

        privileges = list()
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

    def disconnect(self, nodes: Union[str, List[str]] = None) -> None:
        """Disconnect all active user connection sessions for the specified
        node.

        Args:
            nodes: list of node names
        """
        temp_connections = UserConnections(self.connection)
        temp_connections.disconnect_users(users=self, nodes=nodes)

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
        return self._privileges
