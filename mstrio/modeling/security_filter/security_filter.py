from enum import Enum
import logging
from typing import List, Optional, TYPE_CHECKING, Type

from mstrio import config
from mstrio.api import objects, security_filters
from mstrio.modeling import ExpressionFormat
from mstrio.modeling.schema import ObjectSubType, SchemaObjectReference
from mstrio.object_management.folder import Folder
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User, UserGroup
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin, ObjectSubTypes
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    exception_handler,
    fetch_objects,
    filter_params_for_func,
    get_valid_project_id,
    get_valid_project_name
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

from mstrio.modeling.expression import Expression  # isort:skip

if TYPE_CHECKING:
    from mstrio.connection import Connection


logger = logging.getLogger(__name__)


@method_version_handler('11.3.0200')
def list_security_filters(
    connection: "Connection",
    name_contains: Optional[str] = None,
    to_dictionary: bool = False,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    user: Optional[User | str] = None,
    user_group: Optional[UserGroup | str] = None,
    **filters,
) -> list[Type["SecurityFilter"]] | list[dict]:
    """Get a list of Security Filter objects or dicts. Optionally filter the
    objects by specifying filters parameter.
    It can also be filtered by user or user group.

    Note: It is not possible to provide both `user` and `user_group` parameter.
        When both arguments are provided error is raised.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.
    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        name_contains (str, optional): Text that security filter's name
            must contain
        to_dictionary (bool, optional): If `True` returns dictionaries, by
            default (`False`) returns `SecurityFilter` objects.
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior.
        limit (int, optional): Limit the number of elements returned. If `None`
            (default), all objects are returned.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        show_expression_as (ExpressionFormat or str, optional): Specify how
            expressions should be presented
            Available values:
            - None
            (expression is returned in "text" format)
            - `ExpressionFormat.TREE` or `tree`
            (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`
            (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool, optional): Specify whether "qualification"
            is returned in "tokens" format,
            along with `text` and `tree` formats.
            - If omitted or false, only `text` and `tree`
            formats are returned.
            - If true, all `text`, `tree` and `tokens` formats are returned.
        user (str or object, optional): Id of user or `User` object used to
            filter security filters
        user_group (str or object, optional): Id of user group or `UserGroup`
            object used to filter security filters
        **filters: Available filter parameters: ['id', 'name', 'description',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'icon_path', 'owner']
    Returns:
        list of security filter objects or list of security filter dictionaries.
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )
    project_name = get_valid_project_name(
        connection=connection,
        project_id=project_id,
    )
    if user and user_group:
        exception_handler(
            "You cannot filter by both `user` and `user_group` at the same time.")

    if user:
        user = User(connection, id=user) if isinstance(user, str) else user
        # Filter security filters by user for project defined by
        # `project_name` - assigned based on valid `project_id`
        objects = user.list_security_filters(
            project_id, to_dictionary=True
        ).get(project_name, [])
    elif user_group:
        user_group = UserGroup(
            connection, id=user_group
        ) if isinstance(user_group, str) else user_group
        # filter security filters by the user group for project defined by
        # `project_name` - assigned based on valid `project_id`
        objects = user_group.list_security_filters(
            project_id, to_dictionary=True
        ).get(project_name, [])
    else:
        objects = fetch_objects(
            connection=connection,
            project_id=project_id,
            api=security_filters.get_security_filters,
            limit=limit,
            offset=offset,
            name_contains=name_contains,
            dict_unpack_value='securityFilters',
            filters=filters,
        )
    if to_dictionary:
        return objects

    return [
        SecurityFilter.from_dict(
            {
                "show_expression_as": show_expression_as
                if isinstance(show_expression_as, ExpressionFormat)
                else ExpressionFormat(show_expression_as),
                "show_filter_tokens": show_filter_tokens,
                **obj,
            },
            connection,
        )
        for obj in objects
    ]


class UpdateOperator(Enum):
    APPLY = "addElements"
    REVOKE = "removeElements"


@class_version_handler('11.3.0100')
class SecurityFilter(Entity, CopyMixin, DeleteMixin, MoveMixin):
    """Python representation of MicroStrategy Security Filter object.

    Attributes:
        name: name of the security filter
        id: security filter ID
        description: description of the security filter
        sub_type: string literal used to identify the type of a metadata object,
            ObjectSubType enum
        version: object version ID
        ancestors: list of ancestor folders
        type: object type, ObjectTypes enum
        ext_type: object extended type, ExtendedType enum
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        owner: User object that is the owner
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
        is_embedded: if true indicates that the target object of this reference
            is embedded within this object, if this field is omitted
            (as is usual) then the target is not embedded
        path: the path of the object, read only
        primary_locale: the primary locale of the object, in the IETF BCP 47
            language tag format, such as "en-US", read only
        qualification: the security filter definition written as an expression
            tree over predicate nodes, Security Filter support all kinds of
            predicates but bandings
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        top_level(list of SchemaObjectReference or list of dicts, optional):
            the top level attribute list
        bottom_level(list of SchemaObjectReference or list of dicts, optional):
            the bottom level attribute list
    """

    _OBJECT_TYPE = ObjectTypes.SECURITY_FILTER
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'sub_type': ObjectSubType,
        'qualification': Expression.from_dict,
        'top_level': [SchemaObjectReference.from_dict],
        'bottom_level': [SchemaObjectReference.from_dict],
    }
    _API_GETTERS = {
        ('type', 'subtype', 'ext_type', 'date_created', 'date_modified', 'version', 'owner',
         'ancestors', 'acg', 'acl'): objects.get_object_info,
        ('id', 'name', 'description', 'sub_type', 'date_created', 'date_modified', 'path',
         'version_id', 'is_embedded', 'primary_locale', 'qualification', 'destination_folder_id',
         'top_level', 'bottom_level'): security_filters.get_security_filter,
        ('users',): security_filters.get_security_filter_members,
    }
    _API_PATCH: dict = {
        ('name', 'description', 'qualification', 'destination_folder_id', 'is_embedded',
         'top_level', 'bottom_level'):
        (security_filters.update_security_filter, "put"),
        ('folder_id',): (objects.update_object, 'partial_put')
    }
    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'destination_folder_id': str,
        'qualification': dict,
        'is_embedded': bool,
        'top_level': list,
        'below_level': list,
    }
    _ALLOW_NONE_ATTRIBUTES = ['qualification']

    def __init__(
        self,
        connection: "Connection",
        id: Optional[str] = None,
        name: Optional[str] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ):
        """Initialize security filter object by its identifier.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            id (str): identifier of a pre-existing security filter containing
                the required data. Defaults to None.
            name (str): name of a pre-existing security filter containing
                required data. Defaults to None.
            show_expression_as (enum or str, optional): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS` or `tokens`
            show_filter_tokens (bool, optional): specify whether `qualification`
                is returned in `tokens` format, along with `text` and `tree`
                format
        """
        connection._validate_project_selected()
        if id is None:
            security_filter = super()._find_object_with_name(
                connection=connection, name=name, listing_function=list_security_filters
            )
            id = security_filter['id']
        super().__init__(
            connection=connection,
            object_id=id,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.primary_locale = kwargs.get('primary_locale')
        self.is_embedded = kwargs.get('is_embedded')
        self.destination_folder_id = kwargs.get('destination_folder_id')
        self.qualification = Expression.from_dict(
            kwargs.get('qualification'), self.connection) if kwargs.get('qualification') else None
        self._sub_type = ObjectSubType(kwargs.get('sub_type')) if kwargs.get('sub_type') else None
        self._path = kwargs.get('path')
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self.show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat) else ExpressionFormat(show_expression_as)
        self.show_filter_tokens = kwargs.get('show_filter_tokens', False)
        top_level = kwargs.get('top_level')
        self.top_level = [
            SchemaObjectReference.from_dict(level, self.connection) for level in top_level
        ] if top_level else None
        bottom_level = kwargs.get('bottom_level')
        self.bottom_level = [
            SchemaObjectReference.from_dict(level, self.connection) for level in bottom_level
        ] if bottom_level else None
        self.users = None
        self._members = kwargs.get("members")

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        destination_folder: Folder | str,
        qualification: Expression | dict,
        description: Optional[str] = None,
        is_embedded: bool = False,
        primary_locale: Optional[str] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        top_level: Optional[List[dict] | List[SchemaObjectReference]] = None,
        bottom_level: Optional[List[dict] | List[SchemaObjectReference]] = None,
    ) -> Type["SecurityFilter"]:
        """Create a new security filter in a specific project.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name (str): name of a new security filter
            destination_folder (str or object): a globally unique identifier or
                unique folder name used to distinguish between metadata objects
                within the same project
            qualification (Expression or dict, optional): new security filter
                definition written as an expression tree over predicate nodes.
                It can be provided as `Qualification` object or dictionary.
            description (str, optional): optional description of a new
                security filter
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            primary_locale (str, optional): the primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
            show_expression_as (ExpressionFormat or str, optional): specify how
                expressions should be presented
                Available values:
                - None
                (expression is returned in "text" format)
                - `ExpressionFormat.TREE` or `tree`
                (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`
                (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): specify whether "qualification"
                is returned in "tokens" format,
                along with `text` and `tree` formats.
                - If omitted or false, only `text` and `tree`
                formats are returned.
                - If true, all `text`, "tree" and `tokens` formats are returned.
            top_level(list of SchemaObjectReference or list of dicts, optional):
                the top level attribute list
            bottom_level(list of SchemaObjectReference or list of dicts,
                optional): the bottom level attribute list

        Returns:
            Security Filter object
        """
        body = {
            "information": {
                "name": name,
                "description": description,
                "destinationFolderId": destination_folder.id
                if isinstance(destination_folder, Folder)
                else destination_folder,
                "primaryLocale": primary_locale,
                "isEmbedded": is_embedded,
            },
            "topLevel": [
                SchemaObjectReference.to_dict(level) for
                level in top_level
            ] if top_level and all(
                [isinstance(level, SchemaObjectReference) for level in top_level]
            ) else top_level,
            "bottomLevel": [
                SchemaObjectReference.to_dict(level) for
                level in bottom_level
            ] if bottom_level and all(
                [isinstance(level, SchemaObjectReference) for level in bottom_level]
            ) else bottom_level,
        }
        body = delete_none_values(body, recursion=True)
        body["qualification"] = (
            qualification.to_dict() if isinstance(qualification, Expression)
            else qualification
        )
        response = security_filters.create_security_filter(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
            show_filter_tokens=show_filter_tokens,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created security filter named: '{name}' with ID: '{response['id']}'"
            )
        return cls.from_dict(
            source={
                **response,
                'show_expression_as': show_expression_as,
                'show_filter_tokens': show_filter_tokens,
            },
            connection=connection,
        )

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        destination_folder_id: Optional[str] = None,
        qualification: Optional[Expression | dict] = None,
        is_embedded: Optional[bool] = None,
        top_level: Optional[List[dict] | List[SchemaObjectReference]] = None,
        bottom_level: Optional[List[dict] | List[SchemaObjectReference]] = None,
    ):
        """Alter the security filter properties.

        Args:
            name (str, optional): name of a security filter
            description(str, optional): description of a security filter
            destination_folder_id (str, optional): a globally unique identifier
                used to distinguish between objects within the same project
            qualification (Expression, dict, optional): the security filter
            definition written as an expression tree over predicate nodes
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            top_level(list of SchemaObjectReference or list of dicts, optional):
                the top level attribute list
            bottom_level(list of SchemaObjectReference or list of dicts,
                optional): the bottom level attribute list
        """
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    def apply(
        self,
        users_and_groups: Optional[
            List[User] | List[UserGroup] | List[str] | User | UserGroup | str
        ] = None,
    ):
        """Updates members information for a specific security filter.
        Grants a security filter to users or user groups.

        Args:
            users_and_groups (string, object, list of strings or objects): list
            or a single element specifying to which users and user groups
            security filter will be applied. It is possible to provide the whole
            User or UserGroup object(s) or just id(s) of those objects. When
            providing a list it can contain User object(s), UserGroup object(s),
            id(s) at the same time.

        Returns:
            True when applying was successful. False otherwise.
        """
        return self._update_members(UpdateOperator.APPLY, users_and_groups)

    def revoke(
        self,
        users_and_groups: Optional[
            List[User] | List[UserGroup] | List[str] | User | UserGroup | str
        ] = None,
    ):
        """Updates members information for a specific security filter.
        Revokes a security filter from users or groups.

        Args:
            users_and_groups (string, object, list of strings or objects): list
            or a single element specifying to which users and user groups
            security filter will be applied. It is possible to provide the whole
            User or UserGroup object(s) or just id(s) of those objects. When
            providing a list it can contain User object(s), UserGroup object(s),
            id(s) at the same time.

        Returns:
            True when applying was successful. False otherwise.
        """
        return self._update_members(UpdateOperator.REVOKE, users_and_groups)

    def _update_members(
        self,
        op: UpdateOperator,
        users_and_groups: Optional[
            List[User] | List[UserGroup] | List[str] | User | UserGroup | str
        ] = None,
    ):
        """Update members of security filter."""
        users_or_groups = self._retrieve_ids_from_list(users_and_groups)
        body = {
            "operationList": [
                {
                    "op": op.value,
                    "path": "/members",
                    "value": users_or_groups
                }
            ]
        }
        res = security_filters.update_security_filter_members(
            self.connection, self.id, body, self.connection.project_id, throw_error=False
        )
        if res.ok:
            self._get_members()
            logger.info(f"Successfully updated members for security filter '{self.name}'")
        return res.ok

    @staticmethod
    def _retrieve_ids_from_list(
        objects: Optional[
            List[User] | List[UserGroup] | List[str] | User | UserGroup | str
        ] = None,
    ) -> List[str]:
        """Parsing a list which can contain at the same time User object(s),
        UserGroup object(s), id(s) to a list with id(s)."""

        objects = objects if isinstance(objects, list) else [objects]

        return [
            obj if isinstance(obj, str) else obj.id
            for obj in objects
        ]

    def _get_members(self):
        """Get the users and user groups that the specified security filter is
        applied to."""
        self._members = []
        self.fetch("users")
        for member in self.users:
            if member['subtype'] == ObjectSubTypes.USER.value:
                self._members.append(User.from_dict(member, self.connection))
            if member['subtype'] == ObjectSubTypes.USER_GROUP.value:
                self._members.append(UserGroup.from_dict(member, self.connection))
        return self._members

    @property
    def sub_type(self):
        return self._sub_type

    @property
    def path(self):
        return self._path

    @property
    def members(self):
        return self._get_members()
