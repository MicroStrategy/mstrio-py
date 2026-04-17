"""Module for handling tenant management operations in Strategy One."""

import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import folders as folders_api
from mstrio.object_management.search_enums import SearchDomain
from mstrio.object_management.search_operations import full_search, quick_search
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity, TenantMixin
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import get_args_from_func, get_default_args_from_func
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.response_processors import tenant as tenant_processors
from mstrio.utils.version_helper import class_version_handler
from mstrio.utils.wip import WipLevels, module_wip

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.types import TypeOrSubtype
    from mstrio.users_and_groups import User, UserGroup


module_wip(globals(), "11.6.5.101", WipLevels.ERROR)  # NOSONAR


logger = logging.getLogger(__name__)


PROJECTS_CONFIGURATION_FOLDER_ID = '73F7482211D3596C60001B8F67019608'


def list_tenants(
    connection: "Connection",
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list["Tenant"] | list[dict]:
    """List tenant objects or dictionaries.

    Optionally filter the returned tenants by specifying `filters`
    parameters.

    Args:
        connection: Strategy One connection object
        to_dictionary (bool, optional): If True, returns list of dicts.
            If False (default), returns list of Tenant objects.
        limit (int, optional): Maximum number of tenants to retrieve.
            Defaults to None (retrieve all).
        **filters: Available filter parameters: ['id', 'name',
            'description', 'date_created', 'date_modified']

    Returns:
        list[Tenant | dict]: List of tenants or dictionaries

    Examples:
        >>> list_tenants(connection, name='My Tenant')
    """
    tenants = full_search(
        connection,
        domain=SearchDomain.CONFIGURATION,
        object_types=[ObjectSubTypes.TENANT],
        limit=limit,
        to_dictionary=to_dictionary,
        **filters,
    )

    if config.verbose:
        logger.info(f"Retrieved {len(tenants)} tenant(s) from the I-Server.")

    return tenants


@class_version_handler("11.6.0100")
class Tenant(Entity, DeleteMixin, TenantMixin):
    """Object representation of Strategy One Tenant.

    Attributes:
        connection: A Strategy One connection object
        id: Tenant ID
        name: Tenant name
        suffix: Tenant suffix
        description: Tenant description
    """

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
    }

    _OBJECT_TYPE = ObjectTypes.USER
    _OBJECT_SUBTYPE = ObjectSubTypes.TENANT

    _API_GETTERS = {
        **Entity._API_GETTERS,
        (
            'id',
            'name',
            'description',
            'suffix',
        ): tenant_processors.get_tenant_data,
    }

    _REST_ATTR_MAP = {
        'tenant_suffix': 'suffix',
    }

    _API_DELETE = staticmethod(tenant_processors.delete_tenant)

    _API_PATCH: dict = {
        **Entity._API_PATCH,
        (
            'name',
            'description',
            'hidden',
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }

    _PATCH_PATH_TYPES = {
        'suffix': str,
    }

    _MEMBER_TYPES: frozenset = frozenset([ObjectTypes.USER, ObjectSubTypes.USER_GROUP])

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize Tenant object by passing `id` or `name`.

        Args:
            connection: Strategy One connection object
            id: Tenant ID
            name: Tenant name
        """

        if id is None and name is None:
            raise ValueError("Either 'id' or 'name' must be provided.")

        if id is None:
            from mstrio.utils.resolvers import get_tenant_id_from_params_set

            id = get_tenant_id_from_params_set(connection, tenant_name=name)
        passed_id = id

        super().__init__(connection=connection, object_id=id, name=name)

        if self.id in ('', None):
            logger.warning(
                f"Tenant with ID '{passed_id}' was removed and no longer exists. "
                "Some Tenant class methods may not work."
            )

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._suffix = kwargs.get("suffix", default_value)

        self._DELETE_CONFIRM_MSG = (
            f"Are you sure you want to delete tenant '{self.name}' "
            f"with ID: {self.id}?\n"
            "This action cannot be undone.\n"
            "Please type the tenant name to confirm: "
        )
        self._DELETE_SUCCESS_MSG = (
            f"Tenant '{self.name}' has been successfully deleted."
        )
        self._DELETE_PROMPT_ANSWER = self.name

    @staticmethod
    def _make_member_entry(member_id: str, member_type: int | str) -> dict:
        """Build a member entry dict in the API-expected shape.

        Args:
            member_id (str): The object ID of the member.
            member_type (int | str): The type value of the member.

        Returns:
            dict: Dict with `memberId` and `memberTypeValue` keys.
        """
        return {'memberId': member_id, 'memberTypeValue': member_type}

    def _build_member_list(
        self,
        members: 'User | UserGroup | dict | str | list[User | UserGroup | dict | str]',
    ) -> list[dict]:
        """Build normalized member entries for tenant member operations.

        Args:
            members (User | UserGroup | dict | str | list): Member or list
                of members. Each member can be:
                - A User or UserGroup object
                - A dict with 'id' and 'type' keys
                - A string (object ID)

        Returns:
            list[dict]: List of entries with `memberId` and
                `memberTypeValue` keys.

        Raises:
            ValueError: If a dict member has unsupported type.
        """
        from mstrio.users_and_groups.user import User
        from mstrio.users_and_groups.user_group import UserGroup

        members_list = members if isinstance(members, list) else [members]

        string_ids = [member for member in members_list if isinstance(member, str)]
        fetched_info = self._fetch_members_info(string_ids)

        supported_types = {obj_type.value for obj_type in self._MEMBER_TYPES}
        member_list = []
        for member in members_list:
            if isinstance(member, str):
                member_list.append(fetched_info[member])
            elif isinstance(member, (User, UserGroup)):
                member_list.append(
                    self._make_member_entry(member.id, member._OBJECT_TYPE.value)
                )
            else:
                member_type = member.get('type')
                try:
                    member_type_value = get_enum_val(member_type, ObjectTypes)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Member dict with ID '{member.get('id')}' has type "
                        f"'{member_type}', which is not a supported member "
                        f"type. Only User and UserGroup are allowed."
                    ) from error

                if member_type_value not in supported_types:
                    raise ValueError(
                        f"Member dict with ID '{member.get('id')}' has type "
                        f"'{member_type}', which is not a supported member "
                        f"type. Only User and UserGroup are allowed."
                    )
                member_list.append(
                    self._make_member_entry(member.get('id'), member_type_value)
                )

        return member_list

    def _fetch_members_info(self, object_ids: list[str]) -> dict[str, dict]:
        """Fetch object info for multiple IDs to retrieve their types.

        Performs a single full_search restricted to User, UserGroup,
        and Tenant types at the configuration domain level, resolving
        all requested IDs in one call.

        Args:
            object_ids (list[str]): Object IDs to look up.

        Returns:
            dict[str, dict]: Mapping of object ID to member info dict
                with `memberId` and `memberTypeValue` keys.

        Raises:
            ValueError: If any object is not found or its type cannot
                be determined.
        """
        if not object_ids:
            return {}

        results = full_search(
            self.connection,
            domain=SearchDomain.CONFIGURATION,
            object_types=list(self._MEMBER_TYPES),
            to_dictionary=True,
        )

        # Group by ID to detect ambiguous duplicates
        hits_by_id: dict[str, list[dict]] = {}
        for r in results:
            obj_id = r.get('id')
            if obj_id in object_ids:
                hits_by_id.setdefault(obj_id, []).append(r)

        member_info: dict[str, dict] = {}
        for object_id in object_ids:
            hits = hits_by_id.get(object_id)
            if not hits:
                raise ValueError(
                    f"Cannot resolve member ID '{object_id}' for tenant "
                    f"'{self.id}': no User or UserGroup object with this "
                    f"ID was found. For object operations use "
                    f" assign_to_tenant/unassign_from_tenant methods instead."
                )
            if len(hits) > 1:
                raise ValueError(
                    f"Cannot resolve member ID '{object_id}' for tenant "
                    f"'{self.id}': found {len(hits)} objects with this ID, "
                    f"expected exactly one."
                )

            obj_type = hits[0].get('type')
            if not obj_type:
                raise ValueError(
                    f"Cannot resolve member ID '{object_id}' for tenant "
                    f"'{self.id}': object was found but its type could not "
                    f"be determined."
                )

            if config.verbose:
                logger.debug(
                    "Resolved object ID '%s' to type '%s'.", object_id, obj_type
                )

            member_info[object_id] = self._make_member_entry(object_id, obj_type)

        return member_info

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        suffix: str | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter tenant properties.

        Args:
            name (str, optional): New tenant name
            description (str, optional): New tenant description
            suffix (str, optional): New tenant suffix
            journal_comment (str, optional): Comment that will be added to the
                tenant's change journal entry
        """
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        suffix_value = properties.pop('suffix', None)

        if properties:
            self._alter_properties(**properties)

        # current implementation of _API_PATCH do not expect
        # query params so we are calling method directly here
        if suffix_value is not None:
            tenant_processors.update_tenant_suffix(
                self.connection,
                self.id,
                tenant_suffix=suffix_value,
            )
            self._suffix = suffix_value

    def enable(self) -> None:
        """Enable the tenant on the I-Server."""
        self._update_status(enabled=True)

    def disable(self) -> None:
        """Disable the tenant on the I-Server."""
        self._update_status(enabled=False)

    def _update_status(self, enabled: bool) -> None:
        """Toggle the enabled/disabled status of the tenant.

        Args:
            enabled (bool): Whether to enable (True) or disable (False)
                the tenant
        """
        tenant_processors.update_tenant_status(
            self.connection,
            self.id,
            enabled=enabled,
        )

        status = "enabled" if enabled else "disabled"
        if config.verbose:
            logger.info(f"Tenant '{self.id}' has been {status}.")

    def add_members(
        self,
        members: 'User | UserGroup | dict | str | list[User | UserGroup | dict | str]',
    ) -> None:
        """Add members to the tenant.

        Args:
            members (User | UserGroup | dict | str | list): Member or list
                of members to add. Each member can be:
                - A User or UserGroup object
                - A dict with 'id' and 'type' keys (User or UserGroup
                    types only)
                - A string (object ID) - resolves type automatically
                - A list of any combination of the above
        """
        member_list = self._build_member_list(members)
        tenant_processors.add_tenant_members(
            self.connection,
            self.id,
            members=member_list,
        )

        if config.verbose:
            logger.info(f"{len(member_list)} member(s) added to tenant '{self.id}'.")

    def remove_members(
        self,
        members: 'User | UserGroup | dict | str | list[User | UserGroup | dict | str]',
    ) -> None:
        """Remove members from the tenant.

        Args:
            members (User | UserGroup | dict | str | list): Member or list
                of members to remove. Each member can be:
                - A User or UserGroup object
                - A dict with 'id' and 'type' keys (User or UserGroup
                    types only)
                - A string (object ID) - resolves type automatically
                - A list of any combination of the above
        """
        member_list = self._build_member_list(members)
        tenant_processors.remove_tenant_members(
            self.connection,
            members=member_list,
        )

        if config.verbose:
            logger.info(
                f"{len(member_list)} member(s) removed from tenant '{self.id}'."
            )

    def assign_to_tenant(
        self,
        members: dict | Entity | list[dict | Entity],
    ) -> None:
        """Assign objects to this tenant.

        Works with all configuration objects, unlike add_members
        which is restricted to User and UserGroup.

        Args:
            members (dict | Entity | list): Object(s) to assign to
                the tenant. Each member can be:
                - An Entity object
                    (Application, Project, Schedule, Content Group, etc.)
                - A dict with 'id' and 'type' keys
                - A list of any combination of the above
        """
        member_list = self._build_object_list(members)

        tenant_processors.add_tenant_members(
            self.connection,
            self.id,
            members=member_list,
        )

        if config.verbose:
            logger.info(f"{len(member_list)} object(s) assigned to tenant '{self.id}'.")

    def unassign_from_tenant(
        self,
        members: dict | Entity | list[dict | Entity],
    ) -> None:
        """Unassign objects from this tenant.

        Works with all configuration objects, unlike remove_members which is
        restricted to User, UserGroup, and Tenant objects.

        Args:
            members (dict | Entity | list): Object(s) to unassign
                from the tenant. Each member can be:
                - An Entity object
                    (Application, Project, Schedule, Content Group, etc.)
                - A dict with 'id' and 'type' keys
                - A list of any combination of the above
        """
        member_list = self._build_object_list(members)

        tenant_processors.remove_tenant_members(
            self.connection,
            members=member_list,
        )

        if config.verbose:
            logger.info(
                f"{len(member_list)} object(s) unassigned from tenant '{self.id}'."
            )

    def _build_object_list(
        self,
        members: 'dict | Entity | list[dict | Entity]',
    ) -> list[dict]:
        """Build normalized object entries for tenant object operations.

        Args:
            members (dict | Entity | list): Object or list of objects.
                Each member can be:
                - An Entity object
                - A dict with 'id' and 'type' keys

        Returns:
            list[dict]: List of entries with `memberId` and
                `memberTypeValue` keys.
        """
        members_list = members if isinstance(members, list) else [members]

        member_list = []
        for member in members_list:
            if isinstance(member, Entity):
                member_list.append(
                    self._make_member_entry(member.id, member._OBJECT_TYPE.value)
                )
            else:
                member_list.append(
                    self._make_member_entry(member.get('id'), member.get('type'))
                )

        return member_list

    def list_members(
        self,
        to_dictionary: bool = True,
        limit: int | None = None,
        object_types: 'TypeOrSubtype | None' = None,
    ) -> 'list[dict] | list[User | UserGroup]':
        """List all members (User, UserGroup) of this tenant.

        Args:
            to_dictionary (bool, optional): If True, returns list of dicts.
                If False, returns list of objects. Default is True.
            limit (int, optional): Maximum number of members to retrieve.
                Defaults to None (retrieve all).
            object_types (ObjectTypes | ObjectSubTypes | list, optional):
                Filter members by object type(s). Accepted values are
                `ObjectTypes.USER` and `ObjectSubTypes.USER_GROUP`.
                Defaults to None (retrieves both types).

        Returns:
            list[dict | User | UserGroup]: List of tenant members
                as dictionaries or mapped objects

        Raises:
            ValueError: If object_types contains unsupported types
        """
        if object_types is None:
            object_types = list(self._MEMBER_TYPES)
        else:
            types_to_check = (
                object_types if isinstance(object_types, list) else [object_types]
            )
            for obj_type in types_to_check:
                if obj_type not in self._MEMBER_TYPES:
                    raise ValueError(
                        f"Object type '{obj_type}' is not supported for "
                        f"list_members. Accepted values are "
                        f"ObjectTypes.USER and ObjectSubTypes.USER_GROUP."
                    )

        members = quick_search(
            self.connection,
            limit=limit,
            to_dictionary=to_dictionary,
            object_types=object_types,
            tenants=[self.id],
        )

        if config.verbose:
            logger.info(f"Retrieved {len(members)} member(s) from tenant '{self.id}'.")

        return members

    def list_objects(
        self,
        object_types: 'TypeOrSubtype',
        to_dictionary: bool = True,
        limit: int | None = None,
    ) -> list[dict | Entity]:
        """List all configuration objects of specified types
            belonging to this tenant.

        Args:
            object_types (ObjectTypes | ObjectSubTypes | list):
                Required. Object type(s) to search for. Can be a single
                ObjectTypes or ObjectSubTypes value, or a list of any
                combination.
            to_dictionary (bool, optional): If True, returns list of dicts.
                If False, returns list of objects. Default is True.
            limit (int, optional): Maximum number of objects to retrieve.
                Defaults to None (retrieve all).

        Returns:
            list[dict | objects]: List of tenant configuration objects
                as dictionaries or mapped objects

        Raises:
            ValueError: If object_types is None or empty
        """
        if object_types is None:
            raise ValueError(
                'object_types parameter is required and cannot be None. '
                'Specify one or more object types to search for.'
            )

        requested_types = (
            object_types if isinstance(object_types, list) else [object_types]
        )

        def _is_project_type(obj_type) -> bool:
            try:
                return (
                    get_enum_val(obj_type, (ObjectTypes, ObjectSubTypes))
                    == ObjectTypes.PROJECT.value
                )
            except (TypeError, ValueError):
                return False

        includes_project = any(
            _is_project_type(obj_type) for obj_type in requested_types
        )
        non_project_types = [
            obj_type for obj_type in requested_types if not _is_project_type(obj_type)
        ]

        objects_list = []

        if non_project_types:
            search_types: TypeOrSubtype = (
                non_project_types[0]
                if len(non_project_types) == 1
                else non_project_types
            )
            objects_list.extend(
                quick_search(
                    self.connection,
                    limit=limit,
                    to_dictionary=True,
                    object_types=search_types,
                    tenants=[self.id],
                )
            )

        if includes_project:
            response = folders_api.get_folder_contents(
                self.connection,
                id=PROJECTS_CONFIGURATION_FOLDER_ID,
                limit=-1,
                offset=0,
                project_id=None,
            )
            projects = response.json()
            if isinstance(projects, list):
                projects = [
                    project
                    for project in projects
                    if project.get('mdTenantId') == self.id
                ]
                objects_list.extend(projects)

        if limit is not None:
            objects_list = objects_list[:limit]

        if not to_dictionary:
            from mstrio.utils.object_mapping import map_objects_list

            objects_list = map_objects_list(self.connection, objects_list)

        if config.verbose:
            logger.info(
                f"Retrieved {len(objects_list)} object(s) of type "
                f"{object_types} from tenant '{self.id}'."
            )

        return objects_list

    def list_projects(
        self,
        to_dictionary: bool = True,
        limit: int | None = None,
    ) -> list[dict | Project]:
        """List all projects belonging to this tenant.

        Args:
            to_dictionary (bool, optional): If True, returns list of dicts.
                If False, returns list of Project objects. Default is True.
            limit (int, optional): Maximum number of projects to retrieve.
                Defaults to None (retrieve all).

        Returns:
            list[dict | Project]: List of projects as dictionaries
                or mapped objects
        """
        return self.list_objects(
            object_types=ObjectTypes.PROJECT,
            to_dictionary=to_dictionary,
            limit=limit,
        )

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        suffix: str | None = None,
        fields: str | None = None,
    ) -> "Tenant":
        """Create a new tenant on the I-Server.

        Args:
            connection: Strategy One connection object
            name (str): Name of the tenant to create
            suffix (str, optional): Suffix for the tenant. Defaults to None.
            fields (str, optional): Comma-separated list of fields to retrieve
                in the response. Defaults to None.

        Returns:
            Tenant: The newly created Tenant object
        """
        tenant_data = tenant_processors.create_tenant(
            connection,
            name=name,
            suffix=suffix,
            fields=fields,
        )

        tenant = cls.from_dict(source=tenant_data, connection=connection)

        if config.verbose:
            logger.info(
                f"Successfully created tenant named: '{name}' with ID: "
                f"'{tenant_data.get('id')}'"
            )

        return tenant

    @property
    def suffix(self) -> str | None:
        """Tenant suffix."""
        return self._suffix
