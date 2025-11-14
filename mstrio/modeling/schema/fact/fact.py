import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import facts
from mstrio.connection import Connection
from mstrio.modeling.expression import ExpressionFormat, FactExpression
from mstrio.modeling.schema.helpers import (
    DataType,
    ObjectSubType,
    SchemaObjectReference,
)
from mstrio.object_management import search_operations
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    Dictable,
    filter_params_for_func,
    find_object_with_name,
)
from mstrio.utils.resolvers import (
    get_folder_id_from_params_set,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0100')
def list_facts(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> list["Fact"] | list[dict]:
    """Get list of Fact objects or dicts with them.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        name (optional, str): value the search pattern is set to, which
            will be applied to the names of facts being searched
        to_dictionary (optional, bool): If `True` returns dictionaries, by
            default (`False`) returns `Fact` objects.
        limit (optional, int): limit the number of elements returned. If `None`
            (default), all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        show_expression_as (optional, enum or str): specify how expressions
            should be presented.
            Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['id', 'name',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'owner', 'ext_type']

    Returns:
        list of fact objects or list of fact dictionaries.
    """
    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    objects = search_operations.full_search(
        connection,
        object_types=ObjectTypes.FACT,
        project=proj_id,
        name=name,
        pattern=search_pattern,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects
    else:
        show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        return [
            Fact.from_dict(
                source={'show_expression_as': show_expression_as, **obj},
                connection=connection,
                with_missing_value=True,
            )
            for obj in objects
        ]


@class_version_handler('11.3.0100')
class Fact(Entity, CopyMixin, DeleteMixin, MoveMixin):
    """Python representation for Strategy One `Fact` object.

    Attributes:
        id: fact's ID
        name: fact's name
        sub_type: string literal used to identify the type of a metadata object
        description: fact's description
        type: object type, `ObjectTypes` enum
        subtype: object subtype, `ObjectSubTypes` enum
        ext_type: object extended type, `ExtendedType` enum
        ancestors: list of ancestor folders
        date_created: creation time, `DateTime` object
        date_modified: last modification time `DateTime` object
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        is_embedded: if `True` indicates that the target object of this
            reference is embedded within this object. Alternatively if this
            object is itself embedded, then it means that the target object is
            embedded in the same container as this object
        data_type: dataype that the engine should use to store a intermediate
            values for this fact, `DataType` object
        expressions: Array with a member object for each separately defined
            expression currently in use by a fact. Often a fact expression takes
            the form of just a single column name, but more complex expressions
            are possible.
        entry_level: this is the natural level (in other words a set of
            attributes) of the fact. This property is not set by the architects.
            Instead it is deduced by the platform by examining the specification
            of the fact, and considering the attributes and the relationships
            between them. Because it can only be computed by considering the
            schema as a whole, the value is not automatically updated each time
            the fact is modified. It will be correct following a schema update
            operation.
        owner: `User` object that is the owner
        acg: access rights (see `EnumDSSXMLAccessRightFlags` for possible
            values)
        acl: object access control list
        version_id: the version number this object is currently carrying
        hidden: Specifies whether the object is hidden
    """

    _OBJECT_TYPE = ObjectTypes.FACT

    _API_GETTERS = {
        (
            'id',
            'sub_type',
            'name',
            'is_embedded',
            'description',
            'destination_folder_id',
            'path',
            'data_type',
            'expressions',
            'entry_level',
        ): facts.read_fact,
        (
            'abbreviation',
            'type',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl',
            'target_info',
            'hidden',
            'comments',
        ): objects_processors.get_info,
    }
    _API_PATCH = {
        ('data_type', 'expressions'): (facts.update_fact, 'partial_put'),
        ('name', 'description', 'folder_id', 'hidden', 'comments', 'owner'): (
            objects_processors.update,
            'partial_put',
        ),
    }

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'data_type': DataType.from_dict,
        'expressions': (
            lambda source, connection: [
                FactExpression.from_dict(content, connection) for content in source
            ]
        ),
        'entry_level': (
            lambda source, connection: [
                SchemaObjectReference.from_dict(content, connection)
                for content in source
            ]
        ),
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> None:
        """Initialize a new instance of Fact class.

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Args:
             connection (object): Strategy One connection object returned by
                `connection.Connection()`.
            id (optional, str): Identifier of a pre-existing fact containing the
                required data.
            name (optional, str): name of a fact object containing
                the required data.
            show_expression_as (optional, enum or str): specify how expressions
                should be presented.
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`

        Raises:
            ValueError: if both `id` and `name` are not provided, if there
                are multiple facts with given `name`, if project is not
                selected in provided `connection` or if Fact with given `name`
                doesn't exist.
        """
        connection._validate_project_selected()
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            fact = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_facts,
                search_pattern=SearchPattern.EXACTLY,
            )
            id = fact['id']
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
            show_expression_as=show_expression_as,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        """Initialize all properties when creating `Fact` object from
        a dictionary."""
        super()._init_variables(default_value=default_value, **kwargs)
        self._sub_type = kwargs.get('sub_type', default_value)
        self._is_embedded = kwargs.get('is_embedded', default_value)
        self._destination_folder_id = kwargs.get('destination_folder_id', default_value)
        data_type = kwargs.get('data_type')
        self.data_type = (
            default_value if data_type is None else DataType.from_dict(data_type)
        )
        expressions = kwargs.get('expressions')
        self._expressions = (
            default_value
            if expressions is None
            else [FactExpression.from_dict(expression) for expression in expressions]
        )
        entry_level = kwargs.get('entry_level')
        self._entry_level = (
            default_value
            if entry_level is None
            else [SchemaObjectReference.from_dict(obj) for obj in entry_level]
        )
        self._version_id = kwargs.get('version_id')
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        expressions: list[FactExpression | dict],
        destination_folder: 'Folder | tuple[str] | list[str] | str | None' = None,
        destination_folder_path: tuple[str] | list[str] | str | None = None,
        data_type: DataType | dict | None = None,
        description: str | None = None,
        is_embedded: bool = False,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> "Fact":
        """Create new fact object.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (str): new fact's name
            sub_type (str, enum): new fact's sub_type
            destination_folder (Folder | tuple | list | str, optional): Folder
                object or ID or name or path specifying the folder where to
                create object.
            destination_folder_path (str, optional): Path of the folder.
                The path has to be provided in the following format:
                    /MicroStrategy Tutorial/Public Objects/Metrics
            expressions (list): List of `FactExpression` objects or dictionaries
                representing the fact object.
            data_type (object or dict): `DataType` object or dict with
                definition of data type and precision
            description (str): new fact's description
            is_embedded (optional, bool): `True` indicates that the target
                object of this reference is embedded within this object.
                Alternatively if this object is itself embedded, then it means
                that the target object is embedded in the same container as this
                object. Default value is `False`.
            show_expression_as (optional, enum or str): specify how
                expressions should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS` or `tokens`

        Returns:
            `Fact` class object.
        """
        if not isinstance(expressions, list):
            expressions = [expressions]

        dest_id = get_folder_id_from_params_set(
            connection,
            connection.project_id,
            folder=destination_folder,
            folder_path=destination_folder_path,
        )
        body = {
            "information": {
                "name": name,
                "subType": ObjectSubType.FACT.value,
                "isEmbedded": is_embedded,
                "description": description,
                "destinationFolderId": dest_id,
            },
            "dataType": (
                data_type.to_dict() if isinstance(data_type, DataType) else data_type
            ),
            "expressions": [
                (e.to_dict() if isinstance(e, Dictable) else e) for e in expressions
            ],
            "entryLevel": [],
        }
        response = facts.create_fact(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created fact named: '{name}' with ID: '"
                f"{response['id']}'."
            )

        return cls.from_dict(
            source={**response, 'show_expression_as': show_expression_as},
            connection=connection,
        )

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        data_type: DataType | dict | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ):
        """Alter fact properties.

        Args:
            name (optional, str): fact's name
            description (optional, str): fact's description
            data_type (optional, object or dict): fact's data type definition
            hidden (bool, optional): Specifies whether the object is hidden.
                Default value: False.
            comments (optional, str): fact's long description
            owner (optional, str or User): owner of the fact object
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        if data_type:
            properties['expressions'] = self.expressions
        self._alter_properties(**properties)

    def get_tables(
        self, expression: FactExpression | str | None = None
    ) -> list[SchemaObjectReference]:
        """Get list of all tables in given fact expression. If expression
        argument is not specified, list all tables for fact.

        Args:
            expression (optional, str or object): id of the fact expression or
                `FactExpression` object to get tables from.

        Returns:
            List of tables in given `FactExpression` or all tables for fact.
        """
        expressions = self.expressions
        if expression:
            expression_id = (
                expression.id if isinstance(expression, FactExpression) else expression
            )
            expressions = [expr for expr in expressions if expr.id == expression_id]
        tables_list = {tab for expr in expressions for tab in expr.tables}
        return list(tables_list)

    def add_expression(self, expression: FactExpression | dict) -> None:
        """Add expression to the fact.

        Args:
            expression (optional, object or dict): `FactExpression` object or
                dictionary having all necessary information to be added to the
                fact.
        """
        expressions = self.expressions.copy()
        expressions.append(expression)
        self._alter_properties(expressions=expressions)

    def remove_expression(self, expression: str) -> None:
        """Remove expression from the fact.

        Args:
            expression (str): id of `FactExpression` object to be removed
        """
        expressions = self.expressions.copy()
        expressions = [expr for expr in expressions if expr.id != expression]
        self._alter_properties(expressions=expressions)

    @property
    def sub_type(self):
        return self._sub_type

    @property
    def is_embedded(self):
        return self._is_embedded

    @property
    def destination_folder_id(self):
        return self._destination_folder_id

    @property
    def expressions(self):
        """List of `FactExpressions` defined in `Fact` object."""
        return self._expressions

    @property
    def entry_level(self):
        """Natural level (a set of attributes) of the fact."""
        return self._entry_level
