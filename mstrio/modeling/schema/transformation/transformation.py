import logging
from dataclasses import dataclass
from enum import auto
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import transformations
from mstrio.connection import Connection
from mstrio.modeling.expression import Expression, ExpressionFormat
from mstrio.modeling.schema import SchemaObjectReference
from mstrio.modeling.schema.helpers import ObjectSubType
from mstrio.object_management import search_operations
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    Dictable,
    delete_none_values,
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


@method_version_handler('11.3.0500')
def list_transformations(
    connection,
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
) -> list["Transformation"] | list[dict]:
    """Get list of Transformation objects or dicts with them.

    Optionally use `to_dictionary` to choose output format.
    Optionally filter transformations by specifying 'name'.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
        name (string, optional): characters that the transformation name must
            begin with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Transformation object
        limit (integer, optional): limit the number of elements returned. If
            None all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        show_expression_as (ExpressionFormat, str): specify how expressions
            should be presented
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
        **filters: Available filter parameters:
            id str: Transformation's ID
            name str: Transformation's name
            description str: Transformation's description
            date_created str: format: 2001-01-02T20:48:05.000+0000
            date_modified str: format: 2001-01-02T20:48:05.000+0000
            version str: Transformation's version
            owner dict | str | User: Owner ID
            acg str | int: access control group
            subtype str: object's subtype
            ext_type str: object's extended type

    Returns:
        list with Transformation objects or list of dictionaries
    """
    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    objects_ = search_operations.full_search(
        connection,
        object_types=Transformation._OBJECT_TYPE,
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
        return objects_
    else:
        show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        return [
            Transformation.from_dict(
                source={**obj_, 'show_expression_as': show_expression_as},
                connection=connection,
                with_missing_value=True,
            )
            for obj_ in objects_
        ]


class MappingType(AutoName):
    """Enumeration constants used to specify mapping type"""

    ONE_TO_ONE = auto()
    MANY_TO_MANY = auto()


@class_version_handler('11.3.0500')
class Transformation(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Python representation of Strategy One Transformation object.

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
        hidden: Specifies whether the object is hidden
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
            'is_embedded',
        ): transformations.get_transformation,
        (
            'type',
            'subtype',
            'version',
            'owner',
            'acg',
            'acl',
            'ext_type',
            'hidden',
            'comments',
        ): objects_processors.get_info,
    }
    _API_PATCH = {
        (
            'name',
            'description',
            'mapping_type',
            'attributes',
            'destination_folder_id',
        ): (transformations.update_transformation, 'partial_put'),
        (
            'hidden',
            'comments',
            'owner',
        ): (objects_processors.update, "partial_put"),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "attributes": (
            lambda source, connection: [
                TransformationAttribute.from_dict(content, connection)
                for content in source
            ]
        ),
        "mapping_type": MappingType,
    }

    def __init__(
        self,
        connection: Connection,
        id=None,
        name=None,
        show_expression_as=ExpressionFormat.TREE,
    ):
        """Initializes a new instance of Transformation class

        Args:
            connection (Connection): Strategy One connection object returned
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
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            transformation = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_transformations,
                search_pattern=SearchPattern.EXACTLY,
            )
            id = transformation['id']
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
            show_expression_as=show_expression_as,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._sub_type = kwargs.get('sub_type', default_value)
        self._is_embedded = kwargs.get('is_embedded', default_value)
        self._attributes = (
            [
                TransformationAttribute.from_dict(attr, self._connection)
                for attr in kwargs.get('attributes')
            ]
            if kwargs.get('attributes')
            else default_value
        )
        self._mapping_type = kwargs.get('mapping_type', default_value)
        self._version_id = kwargs.get('version_id')
        self._primary_locale = kwargs.get('primary_locale', default_value)
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )

    def list_properties(self, excluded_properties: list[str] | None = None) -> dict:
        excluded_properties = excluded_properties or []
        excluded_properties.extend(
            [
                'hidden',
                'icon_path',
                'comments',
                'certified_info',
                'project_id',
                'target_info',
                'view_media',
                'abbreviation',
            ]
        )
        return super().list_properties(excluded_properties=excluded_properties)

    @classmethod
    @method_version_handler('11.3.0500')
    def create(
        cls,
        connection: 'Connection',
        sub_type: ObjectSubType | str,
        name: str,
        attributes: list,
        mapping_type: MappingType | str,
        destination_folder: 'Folder | tuple[str] | list[str] | str | None' = None,
        destination_folder_path: tuple[str] | list[str] | str | None = None,
        is_embedded: bool = False,
        description: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> 'Transformation':
        """Create Transformation object.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            sub_type: transformation's sub_type
            name: transformation's name
            destination_folder (Folder | tuple | list | str, optional): Folder
                object or ID or name or path specifying the folder where to
                create object.
            destination_folder_path (str, optional): Path of the folder.
                The path has to be provided in the following format:
                    /MicroStrategy Tutorial/Public Objects/Metrics
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
        dest_id = get_folder_id_from_params_set(
            connection,
            connection.project_id,
            folder=destination_folder,
            folder_path=destination_folder_path,
        )
        body = {
            'information': {
                'subType': get_enum_val(sub_type, ObjectSubType),
                'name': name,
                'isEmbedded': is_embedded,
                'description': description,
                'destinationFolderId': dest_id,
            },
            'attributes': [attribute.to_dict() for attribute in attributes],
            'mappingType': mapping_type,
        }
        body = delete_none_values(body, recursion=True)
        response = transformations.create_transformation(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
        ).json()

        if config.verbose:
            logger.info(
                f"Successfully created transformation named: '{name}' with ID: '"
                f"{response['id']}'"
            )

        return cls.from_dict(
            source={**response, 'show_expression_as': show_expression_as},
            connection=connection,
        )

    def alter(
        self,
        name: str | None = None,
        attributes: list | None = None,
        mapping_type: MappingType | None = None,
        description: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ):
        """Alter transformation properties.

        Args:
            name: transformation's name
            attributes: list of base transformation attributes
            mapping_type: transformation's mapping type
            description: transformation's description
            hidden (bool, optional): Specifies whether the object is hidden.
                Default value: False.
            comments: long description of the transformation
           owner: (str, User, optional): owner of the transformation
        """

        name = name or self.name
        if isinstance(owner, User):
            owner = owner.id
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

    _FROM_DICT_MAP = {"lookup_table": SchemaObjectReference, "expression": Expression}

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
        "forms": ([TransformationAttributeForm.from_dict]),
    }

    id: str
    base_attribute: SchemaObjectReference
    forms: list[TransformationAttributeForm]

    def list_properties(self, camel_case=True) -> dict:
        """Lists all properties of transformation attribute."""
        return self.to_dict(camel_case=camel_case)
