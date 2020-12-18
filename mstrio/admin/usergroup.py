from typing import TYPE_CHECKING, Dict, List, Union

import mstrio.config as config
from mstrio.admin.security_role import SecurityRole
from mstrio.api import usergroups
from mstrio.utils import helper
from mstrio.utils.entity import (Entity, ObjectTypes, set_custom_permissions,
                                 set_permission)
from pandas import DataFrame

if TYPE_CHECKING:
    from mstrio.admin.application import Application
    from mstrio.admin.privilege import Privilege
    from mstrio.admin.user import User
    from mstrio.connection import Connection


def list_usergroups(connection: "Connection", name_begins: str = None,
                    to_dictionary: bool = False, limit: int = None, **filters) -> List["UserGroup"]:
    """Get list of User Group objects or User Group dicts. Optionally filter
    the User Groups by specifying 'name_begins' or other filters.

    Wildcards available for name_begins:
        ? - any character
        * - 0 or more of any characters
        e.g name_begins = ?onny wil return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins: Begining of a User Groups name which we want to list
        to_dictionary: If True returns dict, by default (False) returns
            User Group objects
        limit: limit the number of elements returned to a sample of User Groups.
            If `None`, all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'abbreviation', 'description', 'subtype', 'date_created',
            'date_modified', 'version', 'acg', 'owner', 'ext_type']


    Examples:
        >>> list_usergroups(connection, name_begins='Group',
                            description='New group')
    """
    return UserGroup._get_usergroups(connection=connection, name_begins=name_begins,
                                     to_dictionary=to_dictionary, limit=limit, **filters)


class UserGroup(Entity):
    """Object representation of MicroStrategy User Group object.

    Attributes:
        connection: A MicroStrategy connection object
        memberships: User Groups that the User Group is a member of
        memebers: users that are members of User Group
        security_roles: security roles that the User Group is a member of
        privileges: user privileges per project
        id: User ID
        name: User name
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        abbreviation: Object abbreviation
        description: Object description
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd HH:mm:ss" in UTC
        version: Object version ID
        owner: Owner name and ID
        ancestors: List of ancestor folders
        settings: Settings of User Group
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """
    _PATCH_PATH_TYPES = {"name": str,
                         "description": str}
    _SUPPORTED_PATCH_OPERATIONS = {"add": "add",
                                   "remove": "remove",
                                   "change": "replace"}
    _OBJECT_TYPE = ObjectTypes.USERGROUP.value
    _API_GETTERS = {None: usergroups.get_user_group_info,
                    'memberships': usergroups.get_memberships,
                    'members': usergroups.get_members,
                    'security_roles': usergroups.get_security_roles,
                    'privileges': usergroups.get_privileges,
                    'settings': usergroups.get_settings}
    _API_PATCH = [usergroups.update_user_group_info]
    _ALLOWED_ATTRIBUTES = ['id', 'name', 'type', 'subtype', 'ext_type', 'abbreviation', 'date_created',
                           'date_modified', 'version', 'owner', 'ancestors', 'memberships', 'members',
                           'security_roles', 'privileges', 'settings', 'acg', 'acl']

    def __init__(self, connection: "Connection", name: str = None, id: str = None) -> None:
        """Initialize UserGroup object by passing name or id.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: name of User Group
            id: ID of User Group
        """
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.")

        if id is None:
            user_groups = UserGroup._get_usergroup_ids(
                connection=connection, name_begins=name, name=name)
            if user_groups:
                id = user_groups[0]
            else:
                helper.exception_handler("There is no User Group with the given name: '{}'".format(
                    name), exception_type=ValueError)
        super().__init__(connection=connection, object_id=id)

    @classmethod
    def create(cls, connection: "Connection", name: str, description: str = None,
               memberships: List[str] = [], members: List[str] = []):
        """Create a new User Group on the I-Server. Returns `UserGroup` object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name: Name of a newly created User Group
            description: Description of a newly created User Group
            memberships: Specify User Groups which newly created User Group
                will be member
            members: Specify Users which will be members of newly created User
                Group
        """
        body = {"name": name,
                "description": description,
                "memberships": memberships,
                "members": members}
        response = usergroups.create_user_group(connection, body)
        if response.ok:
            if config.verbose:
                print("Successfully created user group '{}'".format(name))
            return cls._from_single_response(connection, response.json())

    @classmethod
    def _get_usergroups(cls, connection: "Connection", name_begins: str = None,
                        to_dictionary: bool = False, limit: int = None, **filters) -> List["UserGroup"]:
        msg = "Error getting information for a set of User Groups."
        objects = helper.fetch_objects_async(connection,
                                             usergroups.get_info_all_user_groups,
                                             usergroups.get_info_all_user_groups_async,
                                             dict_unpack_value=None,
                                             limit=limit,
                                             chunk_size=1000,
                                             error_msg=msg,
                                             name_begins=name_begins,
                                             filters=filters)
        if to_dictionary:
            return objects
        else:
            return cls._from_bulk_response(connection, objects)

    @classmethod
    def _get_usergroup_ids(cls, connection: "Connection", name_begins: str = None,
                           limit: int = None, **filters) -> List[str]:
        group_dicts = UserGroup._get_usergroups(connection=connection,
                                                name_begins=name_begins,
                                                to_dictionary=True,
                                                limit=limit,
                                                **dict(filters))
        return [group['id'] for group in group_dicts]

    def alter(self, name: str = None, description: str = None):
        """Alter User Group name or/and description.

        Args:
            name: New name of the User Group
            description: New description of the User Group
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__    # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        self._alter_properties(**properties)

    def delete(self, force=False) -> bool:
        """Delete the User Group. Returns true if the User Group was
        successfully deleted.

        Args:
            force: If True, no additional prompt will be showed before deleting
                User Group.
        """
        if not force:
            user_input = input(
                "Are you sure you want to delete User Group '{}' with ID: {}? [Y/N]: ".format(self.name, self.id))
        if force or user_input == 'Y':
            response = usergroups.delete_user_group(self.connection, self.id)
            if response and config.verbose:
                print("Successfully deleted User Group {}".format(self.name))
            return True
        else:
            return False

    def add_users(self, users: Union[str, List[str], "User", List["User"]]) -> None:
        """Add members to the User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, "members", "add")
        if succeeded and config.verbose:
            print("Added {} user(s) to group {}".format(succeeded, self.name))
        if failed and config.verbose:
            print("User(s) {} is/are already a member of '{}'".format(failed, self.name))

    def remove_users(self, users: Union[str, List[str], "User", List["User"]]) -> None:
        """Remove members from User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, 'members', "remove")
        if succeeded and config.verbose:
            print("Removed user(s) '{}' from group {}".format(succeeded, self.name))
        if failed and config.verbose:
            print("User(s) {} is/are not members of '{}'".format(failed, self.name))

    def remove_all_users(self) -> None:
        """Remove all members from usergroup."""
        to_be_removed = [member['id'] for member in self.members]
        self.remove_users(to_be_removed)

    def list_members(self, **filters) -> List[dict]:
        """List usergroup members.

        Optionally filter the results by passing filter keyword arguments.

        Args:
            **filters: Available filter parameters: 'name', 'id', 'type',
                'abbreviation', subtype', 'date_created', 'date_modified',
                'version', 'acg', 'owner', source', ext_type', 'username',
                full_name', enabled'
        """
        return helper.filter_list_of_dicts(self.members, **filters)

    def add_to_usergroups(self, groups: Union[str, List[str], "UserGroup", List["UserGroup"]]) -> None:
        """Add User Group to passed groups.

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(groups, "memberships", "add")
        if succeeded and config.verbose:
            print("Added group '{}' to group(s): {}".format(self.name, succeeded))
        if failed and config.verbose:
            print("Group '{}' is already a member of {} group(s)".format(self.name, failed))

    def remove_from_usergroups(self, groups: Union[str, List[str], "UserGroup", List["UserGroup"]]) -> None:
        """Remove User Group from passed groups.

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(groups, 'memberships', "remove")
        if succeeded and config.verbose:
            print("Removed group '{}' from group(s): {}".format(
                self.name, succeeded))
        if failed and config.verbose:
            print("Group '{}' is not a member of {} group(s)".format(self.name, failed))

    def grant_privilege(self, privilege: Union[str, List[str], "Privilege", List["Privilege"]]) -> None:
        """Grant privileges directly to the User Group.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.admin.privilege import Privilege
        privileges = [priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)]
        existing_ids = [privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')]
        succeeded, failed = self._update_nested_properties(
            privileges, "privileges", "add", existing_ids)

        if succeeded:
            self.fetch('privileges')     # fetch the object properties and set object attributes
            if config.verbose:
                print("Granted privilege(s) {} to '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User Group '{}' already has privilege(s) {}".format(self.name, failed))

    def revoke_privilege(self, privilege: Union[str, List[str], "Privilege", List["Privilege"]]) -> None:
        """Revoke directly granted User Group privileges.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.admin.privilege import Privilege
        privileges = set([priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)])
        existing_ids = [privilege['privilege']['id'] for privilege in self.list_privileges(mode='ALL')]
        directly_granted = set([privilege['privilege']['id']
                                for privilege in self.list_privileges(mode='GRANTED')])
        to_revoke = list(privileges.intersection(directly_granted))
        not_directly_granted = list((set(existing_ids) - directly_granted).intersection(privileges))

        if not_directly_granted:
            msg = "Privileges {} are inherited and will be ommited. Only directly granted privileges can be revoked by this method.".format(
                sorted(not_directly_granted))
            helper.exception_handler(msg, exception_type=Warning)

        succeeded, failed = self._update_nested_properties(
            to_revoke, "privileges", "remove", existing_ids)
        if succeeded:
            self.fetch('privileges')     # fetch the object properties and set object attributes
            if config.verbose:
                print("Revoked privilege(s) {} from '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User group '{}' does not have privilege(s) {}".format(self.name, failed))

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke directly granted group privileges.

        Args:
            force: If True, no additional prompt will be showed before revoking
                all privileges from User Group
        """
        if not force:
            user_input = input(
                "Are you sure you want to revoke all privileges from user group '{}'? [Y/N]: ".format(self.name))
        if force or user_input == 'Y':
            to_revoke = [privilege['privilege']['id']
                         for privilege in self.list_privileges(mode='GRANTED')]
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                print("User Group '{}' does not have any directly granted privileges".format(self.name))

    def list_privileges(self, mode: str = 'ALL', to_dataframe: bool = False) -> list:
        """List privileges for user group.

        Args:
            mode: ['ALL'/'INHERITED'/'GRANTED'] specifies which privileges to
                list
            to_dataframe: If True, return a DataFrame object containing
                privileges
        """
        self.fetch('privileges')

        def to_df(priv_list):
            priv_dict = {}
            for priv in priv_list:
                priv_dict[priv['privilege']['id']] = priv['privilege']['name']
            df = DataFrame.from_dict(priv_dict, orient='index', columns=['Name'])
            df.index.name = 'ID'
            return df

        privileges = list()
        if mode == 'ALL':
            privileges = self.privileges
        elif mode == 'INHERITED':
            for privilege in self.privileges:
                is_inherited = False
                for source in privilege['sources']:
                    is_inherited = not source['direct'] or is_inherited
                if is_inherited:
                    privileges.append(privilege)
        elif mode == 'GRANTED':
            for privilege in self.privileges:
                is_granted = False
                for source in privilege['sources']:
                    is_granted = source['direct'] or is_granted
                if is_granted:
                    privileges.append(privilege)
        else:
            helper.exception_handler(
                "Wrong privilege mode has been passed, allowed modes are ['ALL'/'INHERITED'/'GRANTED']")

        return to_df(privileges) if to_dataframe else privileges

    def assign_security_role(self, security_role: Union[SecurityRole, str], application: Union["Application", str]) -> None:
        """Assigns a Security Role to the User Group for given application.

        Args:
            security_role: Security Role ID or object
            application: Application name or object
        """
        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.grant_to([self.id], application)
        if config.verbose:
            print("Assigned Security Role '{}' to group: '{}'".format(security_role.name, self.name))

    def revoke_security_role(self, security_role: Union[SecurityRole, str], application: Union["Application", str]) -> None:
        """Removes a Security Role from the User Group for given application.

        Args:
            security_role: Security Role ID or object
            application: Application name or object
        """
        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.revoke_from([self.id], application)
        if config.verbose:
            print("Revoked Security Role '{}' from group: '{}'".format(security_role.name, self.name))

    def get_settings(self) -> Dict:
        """Get the User Group settings from the I-Server."""
        res = self._API_GETTERS.get('settings')(self.connection, self.id, include_access=True)  # type: ignore
        return res.json()

    def set_permission(self, permission: str, to_objects: Union[str, List[str]],
                       object_type: int, propagate_to_children: bool = None):
        """Set permission to perform actions on given object(s).

        Function is used to set permission of the trustee to perform given
        actions on the provided objects. Within one execution of the function
        permission will be set in the same manner for each of the provided
        objects.
        Permission is the predefined set of rights. All objects to which the
        rights will be given have to be of the same type which is also provided.

        Args:
            permission (str): Name of permission which defines set of rights.
                Available values are 'View', 'Modify', 'Full Control',
                'Denied All', 'Default All'.
            to_objects: (str, list(str)): List of object ids on access list
                to which the permissions will be set
            object_type (int): Type of objects on access list
            propagate_to_chilren: Flag used in the request to determine if
                those rights will be propagated to children of the usergroup
        """
        set_permission(connection=self.connection, trustee_id=self.id, permission=permission,
                       to_objects=to_objects, object_type=object_type,
                       propagate_to_children=propagate_to_children)

    def set_custom_permissions(self, to_objects: Union[str, List[str]],
                               object_type: int, execute: str = None,
                               use: str = None, control: str = None,
                               delete: str = None, write: str = None,
                               read: str = None, browse: str = None):
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
        set_custom_permissions(connection=self.connection, trustee_id=self.id, to_objects=to_objects,
                               object_type=object_type, execute=execute, use=use, control=control,
                               delete=delete, write=write, read=read, browse=browse)
