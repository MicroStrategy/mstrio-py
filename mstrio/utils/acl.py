from enum import Enum, IntFlag
from typing import Any, Optional, TYPE_CHECKING, TypeVar

import pandas as pd

from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.utils.helper import Dictable, exception_handler, filter_obj_list, IServerError

if TYPE_CHECKING:
    from mstrio.server import Project
    from mstrio.users_and_groups import UserOrGroup
    from mstrio.utils.entity import Entity


class Rights(IntFlag):
    """"Enumeration constants used to specify the access granted attribute of
    the DSS objects. """
    EXECUTE = 0b10000000
    USE = 0b01000000
    CONTROL = 0b00100000
    DELETE = 0b00010000
    WRITE = 0b00001000
    READ = 0b00000100
    USE_EXECUTE = 0b00000010  # This constant is deprecated
    BROWSE = 0b00000001
    INHERITABLE = 0b100000000000000000000000000000


class Permissions(Enum):
    """Enumeration constants used to specify combination of Rights values
    similar to workstation Security Access.

    TODO: This has to be string-based to discern between 'Denied All'
    and 'Full Control', which have the same mask.
    """
    DENIED_ALL = 'Denied All'
    DEFAULT_ALL = 'Default All'
    CONSUME = 'Consume'
    VIEW = 'View'
    MODIFY = 'Modify'
    FULL_CONTROL = 'Full Control'


class AggregatedRights(IntFlag):
    """Enumeration constants used to specify combination of Rights values."""
    NONE = 0b00000000
    CONSUME = 0b01000101
    VIEW = 0b11000101
    MODIFY = 0b11011101
    ALL = 0b11111111


AGGREGATED_RIGHTS_MAP = {
    Permissions.VIEW: AggregatedRights.VIEW,
    Permissions.MODIFY: AggregatedRights.MODIFY,
    Permissions.FULL_CONTROL: AggregatedRights.ALL,
    Permissions.DENIED_ALL: AggregatedRights.ALL,
    Permissions.DEFAULT_ALL: AggregatedRights.NONE,
    Permissions.CONSUME: AggregatedRights.CONSUME,
}

T = TypeVar("T")


class ACE(Dictable):

    _FROM_DICT_MAP = {
        'rights': Rights,
    }

    def __init__(
        self,
        deny: bool,
        entry_type: int,
        rights: Rights | int,
        trustee_id: str,
        trustee_name: str,
        trustee_type: int,
        trustee_subtype: int,
        inheritable: bool
    ):
        """Set ACL object.

        Args:
            deny: Specifies whether access is denied
            entry_type: Access control entry type (1 for object access).
                Possible values can be found in EnumDSSXMLAccessEntryType
            rights: Rights assigned to the designated trustee
            trustee_id: User ID of the designated trustee
            trustee_name: User name of the designated trustee
            trustee_type: Type of the designated trustee
            trustee_subtype: Sub-type of the designated trustee
            inheritable: Specifies whether access control is inherited
        """

        self.rights = rights if isinstance(rights, Rights) else Rights(rights)
        if self.rights not in range(256) and self.rights not in range(536_870_912, 536_871_167):
            msg = (
                "Wrong `rights` value, please provide value in range 0-255 or combination of "
                "Rights enums"
            )
            exception_handler(msg)
        self.deny = deny
        self.entry_type = entry_type
        self.trustee_id = trustee_id
        self.trustee_name = trustee_name
        self.trustee_type = trustee_type
        self.trustee_subtype = trustee_subtype
        self.inheritable = inheritable

    def __eq__(self, other: object) -> bool:
        if len(self.__dict__) != len(other.__dict__):
            return False
        for attr in self.__dict__:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @classmethod
    def from_dict(cls, source: dict[str, Any], connection: Connection):

        def translate_names(name: str):
            if name == "type":
                return "entry_type"
            return name

        modified_source = {translate_names(key): val for key, val in source.items()}
        return super().from_dict(modified_source, connection)

    def to_dict(self, camel_case=True):

        def translate_names(name: str):
            if name == "entry_type" or name == "entryType":
                return "type"
            return name

        result_dict = super().to_dict(camel_case=camel_case)
        return {translate_names(key): val for key, val in result_dict.items()}

    def _get_request_body(self, op):
        result_dict = {
            "op": op,
            "trustee": self.trustee_id,
            "rights": self.rights.value,
            "type": self.entry_type,
            "denied": self.deny,
            "inheritable": self.inheritable
        }
        return result_dict


class ACLMixin:
    """ACLMixin class adds Access Control List (ACL) management for supporting
    objects.

    An ACL is a set of permissions on objects so that users or user groups have
    control over individual objects in the system. Those permissions decide
    whether or not a user can perform a particular class of operations on a
    particular object. For example, a user may have permissions to view and
    execute a report , but cannot modify the report definition or delete the
    report.

    NOTE: Must be mixedin with Entity or its subclasses.
    """

    def list_acl(self, to_dataframe: bool = False, to_dictionary: bool = False,
                 **filters) -> pd.DataFrame | list[dict | ACE]:
        """Get Access Control List (ACL) for this object. Optionally filter
        ACLs by specifying filters.

        Args:
            to_dataframe(bool, optional): if True, return datasets as
                pandas DataFrame
            to_dictionary(bool, optional): if True, return datasets as dicts
            **filters: Available filter parameters: [deny, type, rights,
                trustee_id, trustee_name, trustee_type, trustee_subtype,
                inheritable]

        Examples:
            >>> list_acl(deny=True, trustee_name="John")
        """
        acl = filter_obj_list(self.acl, **filters)
        if to_dataframe:
            return pd.DataFrame(acl)
        elif to_dictionary:
            return [acl_obj.to_dict() for acl_obj in acl]
        else:
            return acl

    def acl_add(
        self: "Entity",
        rights: int | Rights | AggregatedRights,
        trustees: "list[UserOrGroup] | UserOrGroup",
        denied: bool = False,
        inheritable: Optional[bool] = None,
        propagate_to_children: Optional[bool] = None
    ) -> None:
        """Add Access Control Element (ACE) to the object ACL.

        Note:
            Argument `propagate_to_children` is used only for objects with
            type `ObjectTypes.FOLDER`.

        Args:
            rights: The degree to which the user or group is granted or denied
                access to the object. The available permissions are defined in
                `Rights` and `AggregatedRights` Enums
            trustees: list of trustees (`User` or `UserGroup` objects or ids) to
                update the ACE for
            denied: flag to indicate granted or denied access to the object
            inheritable: Applies only to folders. If set, any objects placed in
                the folder inherit the folder's entry in the ACL.
            propagate_to_children: used for folder objects only, default value
                is None, if set to True/False adds `propagateACLToChildren`
                keyword to the request body and sets its value accordingly

        Examples:
            >>> obj.acl_add(rights=Rights.BROWSE | Rights.EXECUTE,
            >>>             trustees=user_obj, denied=True)
        """
        self._update_acl(
            op="ADD",
            rights=rights,
            trustees=trustees,
            denied=denied,
            inheritable=inheritable,
            propagate_to_children=propagate_to_children
        )

    def acl_remove(
        self: "Entity",
        rights: int | Rights | AggregatedRights,
        trustees: "list[UserOrGroup] | UserOrGroup",
        denied: bool = False,
        inheritable: Optional[bool] = None,
        propagate_to_children: Optional[bool] = None
    ) -> None:
        """Remove Access Control Element (ACE) from the object ACL.

        Note:
            Argument `propagate_to_children` is used only for objects with
            type `ObjectTypes.FOLDER`.

        Args:
            rights: The degree to which the user or group is granted or denied
                access to the object. The available permissions are defined in
                `Rights` and `AggregatedRights` Enums
            trustees: list of trustees (`User` or `UserGroup` objects or ids) to
                update the ACE for
            denied: flag to indicate granted or denied access to the object
            inheritable: Applies only to folders. If set, any objects placed in
                the folder inherit the folder's entry in the ACL.
            propagate_to_children: used for folder objects only, default value
                is None, if set to True/False adds `propagateACLToChildren`
                keyword to the request body and sets its value accordingly

        Examples:
            >>> obj.acl_remove(rights=Rights.BROWSE | Rights.EXECUTE,
            >>>                trustees=user_obj, denied=True)
        """
        self._update_acl(
            op="REMOVE",
            rights=rights,
            trustees=trustees,
            denied=denied,
            inheritable=inheritable,
            propagate_to_children=propagate_to_children
        )

    def acl_alter(
        self: "Entity",
        rights: int | Rights | AggregatedRights,
        trustees: "list[UserOrGroup] | UserOrGroup",
        denied: bool = False,
        inheritable: Optional[bool] = None,
        propagate_to_children: Optional[bool] = None
    ) -> None:
        """Alter an existing Access Control Element (ACE) of the object ACL.

        Note:
            Argument `propagate_to_children` is used only for objects with
            type `ObjectTypes.FOLDER`.

        Args:
            rights: The degree to which the user or group is granted or denied
                access to the object. The available permissions are defined in
                `Rights` and `AggregatedRights` Enums
            trustees: list of trustees (`User` or `UserGroup` objects or ids) to
                update the ACE for
            denied: flag to indicate granted or denied access to the object
            inheritable: Applies only to folders. If set, any objects placed in
                the folder inherit the folder's entry in the ACL.
            propagate_to_children: used for folder objects only, default value
                is None, if set to True/False adds `propagateACLToChildren`
                keyword to the request body and sets its value accordingly

        Examples:
            >>> obj.acl_alter(rights=Rights.BROWSE | Rights.EXECUTE,
            >>>               trustees=user_obj, denied=True)
        """
        self._update_acl(
            op="REPLACE",
            rights=rights,
            trustees=trustees,
            denied=denied,
            inheritable=inheritable,
            propagate_to_children=propagate_to_children
        )

    def _update_acl(
        self: "Entity",
        op: str,
        rights: int | Rights | AggregatedRights,
        trustees: "list[UserOrGroup] | UserOrGroup",
        denied: bool = False,
        inheritable: Optional[bool] = None,
        propagate_to_children: Optional[bool] = None,
    ) -> None:
        """Updates the ACL for this object, performs operation defined by the
        `op` parameter on all objects from `trustees` list.

        Note:
            Argument `propagate_to_children` is used only for objects with
            type `ObjectTypes.FOLDER`.

        Args:
            op: ACL update operator, available values are "ADD", "REMOVE" and
                "REPLACE"
            rights: value of rights to use by the operator
            trustees: list of trustees to update the ACE for
            denied: flag to indicate granted or denied access to the object
            inheritable: Applies only to folders. If set, any objects placed in
                the folder inherit the folder's entry in the ACL.
            propagate_to_children: used for folder objects only, default value
                is None, if set to True/False adds `propagateACLToChildren`
                keyword to the request body and sets its value accordingly
        """

        response = modify_rights(
            connection=self.connection,
            object_type=self._OBJECT_TYPE,
            ids=self.id,
            op=op,
            rights=rights,
            trustees=trustees,
            denied=denied,
            inheritable=inheritable,
            propagate_to_children=propagate_to_children
        )

        self._set_object_attributes(**response)


class TrusteeACLMixin:
    """TrusteeACLMixin class adds ACL management for Trustee classes.

    Objects currently supporting this Mixin are: (`User` and `UserGroup`).
    """

    def set_permission(
        self,
        permission: Permissions | str,
        to_objects: str | list[str],
        object_type: "ObjectTypes | int",
        project: "Optional[Project | str]" = None,
        propagate_to_children: Optional[bool] = None
    ) -> None:
        """Set permission to perform actions on given object(s).

        Function is used to set permission of the trustee to perform given
        actions on the provided objects. Within one execution of the function
        permission will be set in the same manner for each of the provided
        objects. The only available values of permission are: 'View', 'Modify',
        'Full Control', 'Denied All', 'Default All'. Permission is the
        predefined set of rights. All objects to which the rights will be given
        have to be of the same type which is also provided.

        Args:
            permission: The Permission which defines set of rights. See:
                `Permissions` enum
            to_objects: List of object ids on access list for which the
                permissions will be set
            object_type: Type of objects on access list. See: `ObjectTypes` enum
            project: Object or id of Project where the object is
                located. If not passed, Project (project_id) selected in
                Connection object is used
            propagate_to_children: Flag used in the request to determine if
                those rights will be propagated to children of the trustee
        Returns:
            None
        """

        if not isinstance(permission, Permissions):
            try:
                permission = Permissions(permission)
            except ValueError:
                msg = (
                    "Invalid `permission` value. Available values are: 'View', "
                    "'Modify', 'Full Control', 'Denied All', 'Default All'. "
                    "See: Permissions enum."
                )
                exception_handler(msg)
        right_value = AGGREGATED_RIGHTS_MAP[permission].value
        denied = permission is Permissions.DENIED_ALL

        # those 2 tries are for clearing current rights (set to default values)
        try:
            modify_rights(
                connection=self.connection,
                object_type=object_type,
                trustees=self.id,
                op='REMOVE',
                rights=AggregatedRights.ALL.value,
                ids=to_objects,
                denied=(not denied),
                propagate_to_children=propagate_to_children,
                project=project
            )
        except IServerError:
            pass
        try:
            modify_rights(
                connection=self.connection,
                object_type=object_type,
                trustees=self.id,
                op='REMOVE',
                rights=AggregatedRights.ALL.value,
                ids=to_objects,
                denied=denied,
                propagate_to_children=propagate_to_children,
                project=project
            )
        except IServerError:
            pass

        if permission != Permissions.DEFAULT_ALL:
            modify_rights(
                connection=self.connection,
                object_type=object_type,
                trustees=self.id,
                op='ADD',
                rights=right_value,
                ids=to_objects,
                denied=denied,
                propagate_to_children=propagate_to_children,
                project=project
            )

    def set_custom_permissions(
        self,
        to_objects: str | list[str],
        object_type: "ObjectTypes | int",
        project: "Optional[Project | str]" = None,
        execute: Optional[str] = None,
        use: Optional[str] = None,
        control: Optional[str] = None,
        delete: Optional[str] = None,
        write: Optional[str] = None,
        read: Optional[str] = None,
        browse: Optional[str] = None
    ) -> None:
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
            object_type (int, ObjectTypes): Type of objects on access list
            project (str, Project): Object or id of Project in which
                the object is located. If not passed, Project
                (project_id) selected in Connection object is used.
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
        Returns:
            None
        """

        def modify_custom_rights(
            connection,
            trustee_id: str,
            right: Rights | list[Rights],
            to_objects: list[str],
            object_type: "ObjectTypes | int",
            denied: bool,
            default: bool = False,
            propagate_to_children: Optional[bool] = None,
            project: "Optional[Project | str]" = None
        ) -> None:

            right_value = _get_custom_right_value(right)
            try:
                modify_rights(
                    connection=connection,
                    trustees=trustee_id,
                    op='REMOVE',
                    rights=right_value,
                    ids=to_objects,
                    object_type=object_type,
                    project=project,
                    denied=(not denied),
                    propagate_to_children=propagate_to_children
                )
            except IServerError:
                pass

            op = 'REMOVE' if default else 'ADD'
            try:
                modify_rights(
                    connection=connection,
                    trustees=trustee_id,
                    op=op,
                    rights=right_value,
                    ids=to_objects,
                    object_type=object_type,
                    project=project,
                    denied=denied,
                    propagate_to_children=propagate_to_children
                )
            except IServerError:
                pass

        rights_dict = {
            Rights.EXECUTE: execute,
            Rights.USE: use,
            Rights.CONTROL: control,
            Rights.DELETE: delete,
            Rights.WRITE: write,
            Rights.READ: read,
            Rights.BROWSE: browse
        }
        if not set(rights_dict.values()).issubset({'grant', 'deny', 'default', None}):
            msg = (
                "Invalid value of the right. Available values are 'grant', 'deny', "
                "'default' or None."
            )
            raise ValueError(msg)

        grant_list = [right for right, value in rights_dict.items() if value == 'grant']
        deny_list = [right for right, value in rights_dict.items() if value == 'deny']
        default_list = [right for right, value in rights_dict.items() if value == 'default']

        modify_custom_rights(
            connection=self.connection,
            trustee_id=self.id,
            right=grant_list,
            to_objects=to_objects,
            object_type=object_type,
            denied=False,
            project=project
        )
        modify_custom_rights(
            connection=self.connection,
            trustee_id=self.id,
            right=deny_list,
            to_objects=to_objects,
            object_type=object_type,
            denied=True,
            project=project
        )
        modify_custom_rights(
            connection=self.connection,
            trustee_id=self.id,
            right=default_list,
            to_objects=to_objects,
            object_type=object_type,
            denied=True,
            project=project,
            default=True
        )


def modify_rights(
    connection,
    object_type: "ObjectTypes | int",
    ids: list[str] | str,
    op: str,
    rights: int,
    trustees: "list[UserOrGroup] | UserOrGroup",
    denied: bool = False,
    inheritable: Optional[bool] = None,
    propagate_to_children: Optional[bool] = None,
    project: "Optional[Project | str]" = None,
) -> None | dict:
    """Updates the ACL for all given objects specified by id from ids list,
    performs operation defined by the `op` parameter on all objects for
    every user or group from `trustees` list.

    Note:
        Argument `inheritable` and `propagate_to_children` are used only
        for objects with type `ObjectTypes.FOLDER`.

    Args:
        object_type (ObjectTypes, int): Type of every object from ids list.
            One of EnumDSSXMLObjectTypes. Ex. 34 (User or UserGroup),
            44 (Security Role), 32 (Project), 8 (Folder).
        ids (list[str], str): List of object ids or one object id on which
            operations will be performed.
        op (str): ACL update operator, available values are "ADD", "REMOVE"
            and "REPLACE".
        rights (int): Value of rights to use by the operator.
        trustees (list[UserOrGroup], UserOrGroup): List of trustees or one
            trustee to update the ACE for.
        denied (bool): Flag to indicate granted or denied access
            to the object.
        inheritable (bool, optional): Applies only to folders. If set, any
            objects placed in the folder inherit the folder's entry
            in the ACL.
        propagate_to_children (bool, optional): Used for folder objects
            only, default value is None, if set to True/False adds
            `propagateACLToChildren` keyword to the request body and sets
            its value accordingly.
        project (Project, str, optional): Project object or project id
            on which objects are stored, if not specified project id from
            connection will be used.

    Returns:
        Dict with updated object properties if there was only one id in ids
        list or None.
    """
    if not isinstance(ids, list):
        ids = [ids]
    if not isinstance(trustees, list):
        trustees = [trustees]
    if not isinstance(object_type, ObjectTypes):
        object_type = ObjectTypes(object_type)

    trustees = [trustee if isinstance(trustee, str) else trustee.id for trustee in trustees]
    project = project.id if project and not isinstance(project, str) else project
    if op not in ["ADD", "REMOVE", "REPLACE"]:
        raise ValueError("Wrong ACL operator passed. Please use ADD, REMOVE or REPLACE")

    for id in ids:
        for trustee in trustees:
            if inheritable is None and object_type is ObjectTypes.FOLDER:
                response = objects.get_object_info(
                    connection=connection,
                    id=id,
                    object_type=object_type.value,
                    project_id=project
                ).json()
                tmp = [
                    ace['inheritable']
                    for ace in response.get('acl', [])
                    if ace['trusteeId'] == trustee and ace['deny'] == denied
                ]
                inheritable = False if not tmp else tmp[0]

            body = {
                "acl": [
                    ACE(
                        rights=rights,
                        trustee_id=trustee,
                        deny=denied,
                        inheritable=inheritable,
                        trustee_name=None,
                        trustee_type=None,
                        trustee_subtype=None,
                        entry_type=1
                    )._get_request_body(op=op)
                ]
            }

            if propagate_to_children and object_type is ObjectTypes.FOLDER:
                body["propagateACLToChildren"] = propagate_to_children
                body["propagationBehavior"] = "overwrite_recursive"

            response = objects.update_object(
                connection=connection,
                id=id,
                body=body,
                object_type=object_type.value,
                project_id=project
            )
        if len(ids) == 1 and response.ok:
            return response.json()


def _parse_acl_rights_bin_to_dict(rights_bin: int) -> dict[Rights, bool]:
    return {right: rights_bin & right.value != 0 for right in Rights}


def _parse_acl_rights_dict_to_bin(rights_dict: dict[Rights, bool]) -> int:
    output = 0
    for right, given in rights_dict.items():
        if given:
            output |= right.value
    return output


def _get_custom_right_value(right: Rights | list[Rights]) -> int:
    right_value = 0
    if not isinstance(right, list):
        right = [right]
    for r in right:
        if not isinstance(r, Rights):
            try:
                r = Rights[r.upper()]
            except ValueError:
                msg = (
                    f"Invalid custom `right` value: {r}. Available values are: EXECUTE, USE, "
                    "CONTROL, DELETE, WRITE, READ, BROWSE. See: the Rights enum."
                )
                raise ValueError(msg)
        right_value |= r.value
    return right_value
