from dataclasses import dataclass
from enum import auto
import logging
from typing import Optional

from mstrio import config
from mstrio.api import objects, transformations
from mstrio.connection import Connection
from mstrio.modeling.expression import Expression, ExpressionFormat
from mstrio.modeling.schema import SchemaObjectReference
from mstrio.modeling.schema.helpers import ObjectSubType
from mstrio.object_management import search_operations
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.types import ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    Dictable,
    filter_params_for_func,
    get_valid_project_id
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0500')
def list_transformations(
    connection,
    name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    **filters
) -> list["Transformation"] | list[dict]:
    """Get list of Transformation objects or dicts with them.

    Optionally use `to_dictionary` to choose output format.
    Optionally filter transformations by specifying 'name'.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): characters that the transformation name must
            begin with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Transformation object
        limit (integer, optional): limit the number of elements returned. If
            None all objects are returned.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        show_expression_as (ExpressionFormat, str): specify how expressions
            should be presented
            Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        **filters: Available filter parameters:
            id str: Transformation's ID
            name str: Transformation's name
            date_created str: format: 2001-01-02T20:48:05.000+0000
            date_modified str: format: 2001-01-02T20:48:05.000+0000
            version str: Transformation's version
            owner dict: e.g. {'id': <user's id>, 'name': <user's name>},
                with one or both of the keys: id, name
            acg str | int: access control group

    Returns:
        list with Transformation objects or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects_ = search_operations.full_search(
        connection,
        object_types=Transformation._OBJECT_TYPE,
        project=project_id,
        name=name,
        pattern=search_pattern,
        limit=limit,
        **filters
    )
    if to_dictionary:
        return objects_
    else:
        show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat
        ) else ExpressionFormat(show_expression_as)
        return [
            Transformation.from_dict(
                {
                    **obj_, 'show_expression_as': show_expression_as
                }, connection
            ) for obj_ in objects_
        ]


class MappingType(AutoName):
    """Enumeration constants used to specify mapping type"""
    ONE_TO_ONE = auto()
    MANY_TO_MANY = auto()


@class_version_handler('11.3.0500')
class Transformation(Entity, MoveMixin, DeleteMixin):
    """Python representation of MicroStrategy Transformation object.

    Attributes:
        id: transformation's ID
        name: transformation's name
        sub_type: string literal used to identify the type of a metadata object
        description: transformation's description
        type: object type, ObjectTypes enum
        subtype: object subtype, ObjectSubTypes enum
        ext_type: object extended type, ExtendedType enum
        attributes: list of attributes used in the transformation
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        mapping_type: transformation's mapping type, MappingType enum
        owner: User object that is the owner
        version_id: the version number this object is currently carrying
        primary_locale: The primary locale of the object, in the IETF BCP 47
            language tag format, such as "en-US".If no particular locale is set
            as the primary locale (for example, if the project is not
            internationalized), the field will be omitted.
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
    """
    _OBJECT_TYPE = ObjectTypes.ROLE
    _API_GETTERS = {
        (
            'id',
            'sub_type',
            'name',
            'description',
            'date_created',
            'date_modified',
            'primary_locale',
            'mapping_type',
            'attributes',
            'is_embedded'
        ): transformations.get_transformation,
        ('type', 'subtype', 'version', 'owner', 'acg', 'acl', 'ext_type'): objects.get_object_info
    }
    _API_PATCH = {
        ('name', 'description', 'mapping_type', 'attributes',
         'destination_folder_id'): (transformations.update_transformation, 'partial_put'),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "attributes": (
            lambda source,
            connection:
            [TransformationAttribute.from_dict(content, connection) for content in source]
        ),
        "mapping_type": MappingType,
    }

    def __init__(
        self, connection: Connection, id=None, name=None, show_expression_as=ExpressionFormat.TREE
    ):
        """Initializes a new instance of Transformation class

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): Transformation's ID. Defaults to None.
            name (str, optional): Transformation's name. Defaults to None.
            show_expression_as (ExpressionFormat or str, optional):
                specify how expressions should be presented.
                Defaults to ExpressionFormat.TREE.

                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS` or `tokens`

        Raises:
            AttributeError: if both `id` and `name` are not provided.
            ValueError: if Transformation with the given `name` doesn't exist.
        """
        if id is None:
            transformation = super()._find_object_with_name(
                connection=connection, name=name, listing_function=list_transformations
            )
            id = transformation['id']
        super().__init__(
            connection=connection, object_id=id, name=name, show_expression_as=show_expression_as
        )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._sub_type = kwargs.get('sub_type')
        self._is_embedded = kwargs.get('is_embedded')
        self._attributes = [
            TransformationAttribute.from_dict(attr, self._connection)
            for attr in kwargs.get('attributes')
        ] if kwargs.get('attributes') else None
        self._mapping_type = kwargs.get('mapping_type')
        self._version_id = kwargs.get('version_id')
        self._primary_locale = kwargs.get('primary_locale')
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat
        ) else ExpressionFormat(show_expression_as)

    def list_properties(self):
        properties = super().list_properties()
        redundant_keys = [
            'hidden',
            'icon_path',
            'comments',
            'certified_info',
            'project_id',
            'target_info',
            'view_media',
            'abbreviation'
        ]
        [properties.pop(key, None) for key in redundant_keys]
        return properties

    @classmethod
    @method_version_handler('11.3.0500')
    def create(
        cls,
        connection: 'Connection',
        sub_type: ObjectSubType | str,
        name: str,
        destination_folder: Folder | str,
        attributes: list,
        mapping_type: MappingType | str,
        is_embedded: bool = False,
        description: Optional[str] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE
    ) -> 'Transformation':
        """Create Transformation object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            sub_type: transformation's sub_type
            name: transformation's name
            destination_folder: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id.
            attributes: list of base transformation attributes
            mapping_type: transformation's mapping type
            is_embedded: If true indicates that the target object of this
                reference is embedded within this object. Alternatively if
                this object is itself embedded, then it means that the target
                object is embedded in the same container as this object.
            description: transformation's description
            show_expression_as (ExpressionFormat, str): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`

        Returns:
            Transformation class object.
        """
        body = {
            'information': {
                'subType': get_enum_val(sub_type, ObjectSubType),
                'name': name,
                'isEmbedded': is_embedded,
                'description': description,
                'destinationFolderId': destination_folder
            },
            'attributes': [attribute.to_dict() for attribute in attributes],
            'mappingType': mapping_type
        }
        body = delete_none_values(body, recursion=True)
        response = transformations.create_transformation(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat)
        ).json()

        if config.verbose:
            logger.info(
                f"Successfully created transformation named: '{name}' with ID: '{response['id']}'"
            )

        return cls.from_dict(
            source={
                **response, 'show_expression_as': show_expression_as
            }, connection=connection
        )

    def alter(
        self,
        name: Optional[str] = None,
        destination_folder_id: Optional[Folder | str] = None,
        attributes: Optional[list] = None,
        mapping_type: Optional[MappingType] = None,
        description: Optional[str] = None
    ):
        """Alter transformation properties.

        Args:
            name: transformation's name
            destination_folder_id: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id.
            attributes: list of base transformation attributes
            mapping_type: transformation's mapping type
            description: transformation's description
        """

        name = name or self.name
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @property
    def sub_type(self):
        return self._sub_type

    @property
    def attributes(self):
        return self._attributes

    @property
    def mapping_type(self):
        return self._mapping_type

    @property
    def version_id(self):
        return self._version_id

    @property
    def primary_locale(self):
        return self._primary_locale

    @property
    def is_embedded(self):
        return self._is_embedded


@dataclass
class TransformationAttributeForm(Dictable):
    """Class representation of Transformation Attribute Form

    Attributes:
        id: A globally unique identifier used to distinguish between metadata
            objects within the same project. It is possible for two metadata
            objects in different projects to have the same Object Id.
        name: transformation attribute form name
        lookup_table: schema reference of a lookup table
        expression: A generic specification for a calculation stored within a
            metadata object. The expression is represented as a tree over nodes.
            Most internal nodes (called operator nodes) are defined by applying
            a function to the operator's child nodes.
    """

    _FROM_DICT_MAP = {
        "lookup_table": SchemaObjectReference,
        "expression": Expression,
    }

    id: str
    name: str
    lookup_table: SchemaObjectReference
    expression: Expression

    def list_properties(self, camel_case=True) -> dict:
        """Lists all properties of transformation attribute form."""
        return self.to_dict(camel_case=camel_case)


@dataclass
class TransformationAttribute(Dictable):
    """Class representation of Transformation Attribute

    Attributes:
        id: A globally unique identifier used to distinguish between metadata
            objects within the same project. It is possible for two metadata
            objects in different projects to have the same Object Id.
        base_attribute: Object that specifies the base attribute of the
            transformation attribute.
        forms: Object that specifies the transformation attribute form.
    """

    _FROM_DICT_MAP = {
        "base_attribute": SchemaObjectReference,
        "forms": ([TransformationAttributeForm.from_dict])
    }

    id: str
    base_attribute: SchemaObjectReference
    forms: list[TransformationAttributeForm]

    def list_properties(self, camel_case=True) -> dict:
        """Lists all properties of transformation attribute."""
        return self.to_dict(camel_case=camel_case)
