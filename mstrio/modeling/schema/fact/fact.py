import logging
from typing import List, Optional, Union

from mstrio import config
from mstrio.api import facts, objects
from mstrio.connection import Connection
from mstrio.modeling.expression import FactExpression
from mstrio.modeling.schema.helpers import DataType, ObjectSubType, SchemaObjectReference
from mstrio.modeling.schema.attribute import ExpressionFormat
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.object_management import search_operations
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import Dictable, filter_params_for_func

logger = logging.getLogger(__name__)


def list_facts(
    connection: Connection,
    name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE,
    **filters,
) -> Union[List["Fact"], List[dict]]:
    """Get list of Fact objects or dicts with them.

    Note:
        If argument `project_id` is not passed then `project_id` is taken from
        `Connection` object.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        name (optional, str): Optional parameter used to limit search result to
            facts that begins with the given name.
        to_dictionary (optional, bool): If `True` returns dictionaries, by
            default (`False`) returns `Fact` objects.
        limit (optional, int): limit the number of elements returned. If `None`
            (default), all objects are returned.
        project_id (str, optional): Project ID
        show_expression_as (optional, enum or str): specify how expressions
            should be presented.
            Avalable values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        **filters: Available filter parameters: ['id', 'name', 'description',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'icon_path', 'owner']

    Returns:
        list of fact objects or list of fact dictionaries.
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    objects = search_operations.full_search(connection, object_types=ObjectTypes.FACT,
                                            project=project_id, name=name,
                                            pattern=SearchPattern.BEGIN_WITH, limit=limit,
                                            **filters)
    if to_dictionary:
        return objects
    else:
        show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat) else ExpressionFormat(show_expression_as)
        return [
            Fact.from_dict({
                'show_expression_as': show_expression_as,
                **obj,
            }, connection) for obj in objects
        ]


class Fact(Entity, DeleteMixin):
    """Python representation for Microstrategy `Fact` object.

    Attributes:
        id: fact's ID
        name: fact's name
        sub_type: string literal used to identify the type of a metadata object
        description: fact's description
        type: object type, `ObjectTypes` enum
        subtype: object subtype, `ObjectSupTypes` enum
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
    """
    _OBJECT_TYPE = ObjectTypes.FACT
    _DELETE_NONE_VALUES_RECURSION = False
    _API_GETTERS = {
        ('id', 'sub_type', 'name', 'is_embedded', 'description', 'destination_folder_id', 'path',
         'data_type', 'expressions', 'entry_level'): facts.read_fact,
        ('abbreviation', 'type', 'ext_type', 'date_created', 'date_modified', 'version', 'owner',
         'icon_path', 'view_media', 'ancestors', 'certified_info', 'acg', 'acl',
         'target_info'): objects.get_object_info
    }
    _API_PATCH = {
        ('data_type', 'expressions'): (facts.update_fact, 'partial_put'),
        ('name', 'description'): (objects.update_object, 'partial_put')
    }

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'data_type': DataType.from_dict,
        'expressions': (lambda source, connection:
                        [FactExpression.from_dict(content, connection) for content in source]),
        'entry_level':
            (lambda source, connection:
             [SchemaObjectReference.from_dict(content, connection) for content in source]),
    }

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 name: Optional[str] = None,
                 show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE) -> None:
        """Initialize a new instance of Fact class.

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Args:
             connection (object): MicroStrategy connection object returned by
                `connection.Connection()`.
            id (optional, str): Identifier of a pre-existing fact containing the
                required data.
            name (optional, str): name of a fact object containing
                the required data.
            show_expression_as (optional, enum or str): specify how expressions
                should be presented.
                Avalable values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`

        Raises:
            AttributeError: if both `id` and `name` are not provided, if there
                are multiple facts with given `name` or if project is not
                selected in provided `connection`
            ValueError: if Fact with given `name` doesn't exist.
        """
        connection._validate_project_selected()
        if id is None:
            if name is None:
                raise AttributeError(
                    "Please specify either 'name' or 'id' parameter in the constructor.")
            facts = list_facts(connection=connection, name=name, to_dictionary=True)
            if facts:
                if len(facts) > 1:
                    raise AttributeError(
                        "There are multiple facts with this name. Please initialize with id.")
                id = facts[0]['id']
            else:
                raise ValueError(f"There is no Fact with given name: '{name}'")
        elif name and id:
            raise AttributeError(
                "Please specify either 'name' or 'id' parameter in the constructor.")
        super().__init__(connection=connection, object_id=id, name=name,
                         show_expression_as=show_expression_as)

    def _init_variables(self, **kwargs) -> None:
        """Initialize all properties when creating `Fact` object from
        a dictionary."""
        super()._init_variables(**kwargs)
        self._id = kwargs.get('id')
        self._sub_type = kwargs.get('sub_type')
        self.name = kwargs.get('name')
        self._is_embedded = kwargs.get('is_embedded')
        self.description = kwargs.get('description')
        self._destination_folder_id = kwargs.get('destination_folder_id')
        data_type = kwargs.get('data_type')
        self.data_type = None if data_type is None else DataType.from_dict(data_type)
        expressions = kwargs.get('expressions')
        self._expressions = None if expressions is None else [
            FactExpression.from_dict(expression) for expression in expressions
        ]
        entry_level = kwargs.get('entry_level')
        self._entry_level = None if entry_level is None else [
            SchemaObjectReference.from_dict(obj) for obj in entry_level
        ]
        self._version_id = kwargs.get('version_id')
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat) else ExpressionFormat(show_expression_as)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        destination_folder: Union[Folder, str],
        expressions: List[Union[FactExpression, dict]],
        data_type: Optional[Union[DataType, dict]] = None,
        description: Optional[str] = None,
        is_embedded: bool = False,
        show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE,
    ) -> "Fact":
        """Create new fact object.

        Args:
            connection (object): MicroStrategy connection object returned
                by `connection.Connection()`
            name (str): new fact's name
            sub_type (str, enum): new fact's sub_type
            destination_folder (str or object): A globally unique identifier or
                unique folder name used to distinguish between metadata objects
                within the same project.
                It is possible for two metadata objects in different
                projects to have the same Object Id.
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
                Avalable values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS` or `tokens`

        Returns:
            `Fact` class object.
        """
        if not isinstance(expressions, list):
            expressions = [expressions]
        body = {
            "information": {
                "name": name,
                "subType": ObjectSubType.FACT.value,
                "isEmbedded": is_embedded,
                "description": description,
                "destinationFolderId": destination_folder.id if isinstance(
                    destination_folder, Folder) else destination_folder,
            },
            "dataType": data_type.to_dict() if isinstance(data_type, DataType) else data_type,
            "expressions": [(e.to_dict() if isinstance(e, Dictable) else e) for e in expressions],
            "entryLevel": []
        }
        response = facts.create_fact(
            connection=connection, body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat)).json()
        if config.verbose:
            logger.info(f"Successfully created fact named: '{name}' with ID: '{response['id']}'.")

        return cls.from_dict(
            source={
                **response, 'show_expression_as': show_expression_as
            },
            connection=connection,
        )

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        data_type: Optional[Union[DataType, dict]] = None,
    ):
        """Alter fact properties.

        Args:
            name (optional, str): fact's name
            description (optional, str): fact's description
            data_type (optional, object or dict): fact's data type definition
        """
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        if data_type:
            properties['expressions'] = self.expressions
        self._alter_properties(**properties)

    def get_tables(
            self, expression: Optional[Union[FactExpression,
                                             str]] = None) -> List[SchemaObjectReference]:
        """ Get list of all tables in given fact expression. If expression
        argument is not specified, list all tables for fact.

        Args:
            expression (optional, str or object): id of the fact expression or
                `FactExpression` object to get tables from.

        Returns:
            List of tables in given `FactExpression` or all tables for fact.
        """
        expressions = [expr for expr in self.expressions]
        if expression:
            expression_id = expression.id if isinstance(expression, FactExpression) else expression
            expressions = [expr for expr in expressions if expr.id == expression_id]
        tables_list = set([tab for expr in expressions for tab in expr.tables])
        return list(tables_list)

    def add_expression(self, expression: Union[FactExpression, dict]) -> None:
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
