import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import filters
from mstrio.modeling.schema import ObjectSubType
from mstrio.object_management import SearchPattern, search_operations
from mstrio.object_management.folder import Folder
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    construct_expression_body,
    delete_none_values,
    filter_params_for_func,
    find_object_with_name,
    get_string_exp_body,
    get_valid_project_id,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

from mstrio.modeling.expression import Expression, ExpressionFormat  # isort:skip

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0000')
def list_filters(
    connection: "Connection",
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    **filters,
) -> list["Filter"] | list[dict]:
    """Get a list of Filter objects or dicts. Optionally filter the
    objects by specifying filters parameter.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        name (str, optional): value the search pattern is set to, which
            will be applied to the names of filters being searched
        to_dictionary (bool, optional): If `True` returns dictionaries, by
            default (`False`) returns `Filter` objects.
        limit (int, optional): limit the number of elements returned. If `None`
            (default), all objects are returned.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        show_expression_as (ExpressionFormat or str, optional): specify how
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
        **filters: Available filter parameters: ['id', 'name',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'owner', 'ext_type']
    Returns:
        list of filter objects or list of filter dictionaries.
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=not project_name,
    )

    objects = search_operations.full_search(
        connection,
        object_types=ObjectSubTypes.FILTER,
        project=project_id,
        pattern=search_pattern,
        name=name,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects
    return [
        Filter.from_dict(
            source={
                "show_expression_as": (
                    show_expression_as
                    if isinstance(show_expression_as, ExpressionFormat)
                    else ExpressionFormat(show_expression_as)
                ),
                "show_filter_tokens": show_filter_tokens,
                **obj,
            },
            connection=connection,
        )
        for obj in objects
    ]


@class_version_handler('11.3.0000')
class Filter(Entity, CopyMixin, DeleteMixin, MoveMixin):
    """Python representation of Strategy One Filter object.

    Attributes:
        name: name of the filter
        id: filter ID
        description: description of the filter
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
        qualification: the filter definition written as an expression tree
            over predicate nodes, Filter support all kinds of predicates
            but bandings
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        hidden: Specifies whether the object is hidden
    """

    _OBJECT_TYPE = ObjectTypes.FILTER
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'sub_type': ObjectSubType,
        'qualification': Expression.from_dict,
    }
    _API_GETTERS = {
        (
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'acg',
            'acl',
            'hidden',
            'comments',
        ): objects_processors.get_info,
        (
            'id',
            'name',
            'description',
            'sub_type',
            'date_created',
            'date_modified',
            'path',
            'version_id',
            'is_embedded',
            'primary_locale',
            'qualification',
            'destination_folder_id',
        ): filters.get_filter,
    }
    _API_PATCH: dict = {
        (
            'name',
            'description',
            'qualification',
            'destination_folder_id',
            'is_embedded',
        ): (filters.update_filter, "put"),
        (
            'folder_id',
            'hidden',
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }
    _PATCH_PATH_TYPES = {
        **Entity._PATCH_PATH_TYPES,
        'destination_folder_id': str,
        'qualification': dict,
        'is_embedded': bool,
    }

    _ALLOW_NONE_ATTRIBUTES = ['qualification']

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        name: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ):
        """Initialize filter object by its identifier.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): identifier of a pre-existing filter containing
                the required data. Defaults to None.
            name (str, optional): name of a pre-existing filter containing
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
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            found_filter = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_filters,
            )
            id = found_filter['id']
        super().__init__(
            connection=connection,
            object_id=id,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.primary_locale = kwargs.get('primary_locale', default_value)
        self.is_embedded = kwargs.get('is_embedded', default_value)
        self.destination_folder_id = kwargs.get('destination_folder_id', default_value)
        self.qualification = (
            Expression.from_dict(kwargs.get('qualification'), self.connection)
            if kwargs.get('qualification')
            else default_value
        )
        self._sub_type = (
            ObjectSubType(kwargs.get('sub_type'))
            if kwargs.get('sub_type')
            else default_value
        )
        self._path = kwargs.get('path', default_value)
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        self._show_filter_tokens = kwargs.get('show_filter_tokens', False)

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        destination_folder: Folder | str,
        qualification: Expression | dict | str | None = None,
        description: str | None = None,
        is_embedded: bool | None = False,
        primary_locale: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ) -> "Filter":
        """Create a new filter in a specific project.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`
            name (str): name of a new filter
            destination_folder (str or object): a globally unique identifier or
                unique folder name used to distinguish between metadata objects
                within the same project
            qualification (Expression, dict or str, optional): new filter
                qualification definition. It can be provided as `Expression`
                object, dictionary or string representing filter expression.
            description (str, optional): optional description of a new
                filter
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
            show_filter_tokens (bool, optional): Specify whether "qualification"
                is returned in "tokens" format,
                along with `text` and `tree` formats.
                - If omitted or false, only `text` and `tree`
                formats are returned.
                - If true, all `text`, "tree" and `tokens` formats are returned.
            hidden (bool, optional): Specifies whether the object is hidden.
                Default value: False.

        Returns:
            Filter object
        """
        qualification = {} if qualification is None else qualification
        body = {
            "information": {
                "name": name,
                "description": description,
                "destinationFolderId": (
                    destination_folder.id
                    if isinstance(destination_folder, Folder)
                    else destination_folder
                ),
                "primaryLocale": primary_locale,
                "isEmbedded": is_embedded,
            }
        }
        body = delete_none_values(body, recursion=True)
        body['qualification'] = construct_expression_body(qualification)

        response = filters.create_filter(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
            show_filter_tokens=show_filter_tokens,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created filter named: '{name}' with ID: '"
                f"{response['id']}'"
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
        name: str | None = None,
        description: str | None = None,
        destination_folder_id: str | None = None,
        qualification: Expression | dict | str | None = None,
        is_embedded: bool | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ):
        """Alter the filter properties.

        Args:
            name (str, optional): name of a filter
            description(str, optional): description of a filter
            destination_folder_id (str, optional): a globally unique identifier
                used to distinguish between objects within the same project
            qualification (Expression, dict or str, optional): new filter
                qualification definition. It can be provided as `Expression`
                object, dictionary or string representing filter expression.
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            hidden (bool, optional): Specifies whether the object is hidden.
                Default value: False.
            comments (str, optional): long description of the filter
            owner: (str, User, optional): owner of the filter
        """
        qualification = (
            {}
            if self.qualification is None and qualification is None
            else qualification
        )
        if isinstance(qualification, str):
            qualification = get_string_exp_body(qualification)
        if isinstance(owner, User):
            owner = owner.id
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @property
    def sub_type(self):
        return self._sub_type

    @property
    def path(self):
        return self._path
