from copy import deepcopy
from enum import auto
import logging
from typing import Callable, List, Optional, TYPE_CHECKING, Union
import warnings

from mstrio import config
from mstrio.api import attributes, hierarchies, objects, tables
from mstrio.connection import Connection
from mstrio.modeling.expression import Expression, FactExpression
from mstrio.modeling.schema.attribute import AttributeForm, Relationship
from mstrio.modeling.schema.helpers import (AttributeDisplays, AttributeSorts, DataType,
                                            FormReference, ObjectSubType, SchemaObjectReference)
from mstrio.object_management import search_operations
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import delete_none_values, filter_params_for_func

if TYPE_CHECKING:
    from mstrio.modeling.schema.attribute import Attribute

logger = logging.getLogger(__name__)


class ExpressionFormat(AutoName):
    """"Expression format to be fetched from server, it might be tree or token:
    - tree: tree data structure fully defining the expression. This format can
    be used if you want to examine and modify the expression programmatically.
    - tokens: list of parsed tokens. This format can be used if you want
    to examine and modify the expression using the parser component. Note that
    generating tokens requires additional time.
    """
    TREE = auto()
    TOKENS = auto()


def list_attributes(connection: Connection, name: Optional[str] = None,
                    attribute_subtype: Optional[ObjectSubTypes] = None,
                    to_dictionary: bool = False, limit: Optional[int] = None,
                    show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE,
                    **filters) -> Union[List["Attribute"], List[dict]]:
    """Get list of Attribute objects or dicts with them.
    Optionally filter attributes by specifying 'name', 'attribute_subtype'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): characters that the attribute name must
            begin with
        attribute_subtype (ObjectSubTypes): one of attribute subtypes:
            attribute, attribute_abstract, attribute_recursive, attribute_role,
            attribute_transformation
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Attribute objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        show_expression_as (ExpressionFormat, str): specify how expressions
            should be presented
            Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        **filters: Available filter parameters:
            id str: Attribute's ID
            name str: Attribute's name
            date_created str: format: 2001-01-02T20:48:05.000+0000
            date_modified str: format: 2001-01-02T20:48:05.000+0000
            version str: Attribute's version
            owner dict: e.g. {'id': <user's id>, 'name': <user's name>},
                with one or both of the keys: id, name
            acg str | int: access control group

    Returns:
        list with Attribute objects or list of dictionaries
    """
    if attribute_subtype is None:
        attribute_subtype = ObjectTypes.ATTRIBUTE
    objects_ = search_operations.full_search(connection, object_types=attribute_subtype,
                                             project=connection.project_id, name=name,
                                             pattern=SearchPattern.BEGIN_WITH, limit=limit,
                                             **filters)
    if to_dictionary:
        return objects_
    else:
        show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat) else ExpressionFormat(show_expression_as)
        return [
            Attribute.from_dict({
                **obj_, 'show_expression_as': show_expression_as
            }, connection) for obj_ in objects_
        ]


class Attribute(Entity, DeleteMixin):  # noqa
    """Python representation of MicroStrategy Attribute object.

    Attributes:
        id: attribute's ID
        name: attribute's name
        sub_type: string literal used to identify the type of a metadata object
        description: attribute's description
        type: object type, ObjectTypes enum
        subtype: object subtype, ObjectSubTypes enum
        ext_type: object extended type, ExtendedType enum
        ancestors: list of ancestor folders
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        forms: the list of attribute forms
        attribute_lookup_table: Information about an object referenced within
            the specification of another object. An object reference typically
            contains only enough fields to uniquely identify the referenced
            objects.
        key_form: a key form of an attribute
        displays: The collections of attribute displays and browse displays
        sorts: the collections of attribute sorts and browse sorts
            of the attribute.
        relationships: the list of relationships that one attribute has.
        is_embedded: If true indicates that the target object of this
            reference is embedded within this object. Alternatively if
            this object is itself embedded, then it means that the target
            object is embedded in the same container as this object.
        owner: User object that is the owner
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
        version_id: the version number this object is currently carrying
        """
    _DELETE_NONE_VALUES_RECURSION = True

    _OBJECT_TYPE = ObjectTypes.ATTRIBUTE
    _API_GETTERS = {
        ('id', 'sub_type', 'name', 'is_embedded', 'description', 'destination_folder_id', 'forms',
         'attribute_lookup_table', 'key_form', 'displays', 'sorts',
         'relationships'): attributes.get_attribute,
        ('abbreviation', 'type', 'ext_type', 'date_created', 'date_modified', 'version', 'owner',
         'icon_path', 'view_media', 'ancestors', 'certified_info', 'acg', 'acl',
         'target_info'): objects.get_object_info
    }
    _API_PATCH = {
        ('id', 'sub_type', 'name', 'is_embedded', 'description', 'destination_folder_id', 'forms',
         'attribute_lookup_table', 'key_form', 'displays', 'sorts'):
            (attributes.update_attribute, 'partial_put'),  # noqa
        ('relationships'): (hierarchies.update_attribute_relationships, 'partial_put')
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "forms": (lambda source, connection:
                  [AttributeForm.from_dict(content, connection) for content in source]),
        "relationships": (lambda source, connection:
                          [Relationship.from_dict(content, connection) for content in source]),
        "attribute_lookup_table": SchemaObjectReference.from_dict,
        "key_form": FormReference.from_dict,
        "displays": AttributeDisplays.from_dict,
        "sorts": AttributeSorts.from_dict,
    }

    @staticmethod
    def validate_key_form(key_form: FormReference, forms: List[AttributeForm],
                          error_msg: Optional[str] = None) -> FormReference:

        # if forms is None or len(forms) < 1:
        if not forms:
            raise AttributeError("`forms` can not be empty.")
        elif len(forms) == 1:
            return FormReference(name=forms[0].name)
        elif key_form is None or not any(form.is_referenced_by(key_form) for form in forms):
            raise AttributeError(
                error_msg or "Please select a `key_form` from the `forms` provided.")  # noqa
        return key_form

    @staticmethod
    def check_if_referenced_forms_exist(error_msg: str, forms: List[AttributeForm],
                                        refs: List[FormReference]):
        """Check if all references point to a form in forms."""
        for ref in refs:
            flag = False
            for form in forms:
                if form.is_referenced_by(ref):
                    flag = True
            if flag is False:
                raise AttributeError(error_msg)

    @classmethod
    def validate_displays(cls, displays: AttributeDisplays,
                          forms: List[AttributeForm]) -> AttributeDisplays:
        # Displays CAN'T be empty. Create and populate with form refs
        if displays is None:
            form_refs = [FormReference(id=form.id) for form in forms]
            return AttributeDisplays(report_displays=form_refs, browse_displays=form_refs)
        if displays.report_displays == []:
            displays.report_displays = [FormReference(id=form.id) for form in forms]
        if displays.browse_displays == []:
            displays.browse_displays = [FormReference(id=form.id) for form in forms]

        # Validate if displays use form refs not present in forms
        error_msg = "FormReference present in `displays` is not present in `forms`."
        cls.check_if_referenced_forms_exist(error_msg, forms, displays.report_displays)
        cls.check_if_referenced_forms_exist(error_msg, forms, displays.browse_displays)
        return displays

    @classmethod
    def validate_sorts(cls, sorts: AttributeSorts,
                       forms: List[AttributeForm]) -> Optional[AttributeSorts]:
        if sorts is None:
            return None

        # Validate if sorts use form refs not present in forms
        error_msg = "FormReference present in `sort` is not present in `forms`."
        cls.check_if_referenced_forms_exist(error_msg, forms,
                                            [attr_sort.form for attr_sort in sorts.report_sorts])
        cls.check_if_referenced_forms_exist(error_msg, forms,
                                            [attr_sort.form for attr_sort in sorts.browse_sorts])
        return sorts

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        name: str,
        sub_type: Union[ObjectSubType, str],
        destination_folder: Union[Folder, str],
        forms: List[AttributeForm],
        key_form: FormReference,
        displays: AttributeDisplays,
        description: Optional[str] = None,
        is_embedded: bool = False,
        attribute_lookup_table: Optional[SchemaObjectReference] = None,
        sorts: Optional[AttributeSorts] = None,
        show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE,
    ) -> "Attribute":
        """Alter attribute properties.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: attribute's name
            sub_type: attribute's sub_type
            destination_folder_id: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id.
            forms: attribute's forms list
            key_form: a key form of an attribute
            displays: The collections of attribute displays and browse displays
                of the attribute.
            description: attribute's description
            is_embedded: If true indicates that the target object of this
                reference is embedded within this object. Alternatively if
                this object is itself embedded, then it means that the target
                object is embedded in the same container as this object.
            attribute_lookup_table: Information about an object referenced
                within the  specification of another object. An object reference
                typically contains only enough fields to uniquely identify
                the referenced objects.
            sorts: The collections of attribute sorts and browse sorts
                of the attribute.
            show_expression_as (ExpressionFormat, str): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`

        Returns:
            Attribute class object.
        """
        # Validate dependencies on forms
        key_form = cls.validate_key_form(key_form=key_form, forms=forms)
        displays = cls.validate_displays(displays=displays, forms=forms)
        sorts = cls.validate_sorts(sorts, forms)

        body = {
            'information': {
                'name': name,
                'subType': get_enum_val(sub_type, ObjectSubType),
                'isEmbedded': is_embedded,
                'description': description,
                'destinationFolderId': destination_folder.id if isinstance(
                    destination_folder, Folder) else destination_folder,
            },
            'forms': [form.to_dict() for form in forms] if forms else None,
            'attributeLookupTable': attribute_lookup_table.to_dict()
                                    if attribute_lookup_table else None,  # noqa
            'keyForm': key_form.to_dict() if key_form else None,
            'displays': displays.to_dict() if displays else None,
            'sorts': sorts.to_dict() if sorts else None,
        }
        body = delete_none_values(body, recursion=True)
        response = attributes.create_attribute(
            connection, body=body, show_expression_as=get_enum_val(show_expression_as,
                                                                   ExpressionFormat)).json()

        if config.verbose:
            logger.info(
                f"Successfully created attribute named: '{name}' with ID: '{response['id']}'")

        return cls.from_dict(source={
            **response, 'show_expression_as': show_expression_as
        }, connection=connection)

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 name: Optional[str] = None,
                 show_expression_as: Union[ExpressionFormat, str] = ExpressionFormat.TREE) -> None:
        """Initializes a new instance of Attribute class

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): Attribute's ID. Defaults to None.
            name (str, optional): Attribute's name. Defaults to None.
            show_expression_as (ExpressionFormat or str, optional):
                specify how expressions should be presented.
                Defaults to ExpressionFormat.TREE.

                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Raises:
            AttributeError: if both `id` and `name` are not provided.
            ValueError: if Attribute with the given `name` doesn't exist.
        """
        if id is None:
            if name is None:
                raise AttributeError(
                    "Please specify either 'name' or 'id' parameter in the constructor.")
            attributes = list_attributes(connection=connection, name=name, to_dictionary=True)
            if attributes:
                if len(attributes) > 1:
                    raise AttributeError(
                        "There are multiple attributes with this name. Please initialize with id.")
                id = attributes[0]['id']
            else:
                raise ValueError(f"There is no Attribute with the given name: '{name}'")
        elif name and id:
            raise AttributeError(
                "Please specify either 'name' or 'id' parameter in the constructor.")
        super().__init__(connection=connection, object_id=id, name=name,
                         show_expression_as=show_expression_as)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._id = kwargs.get('id')
        self._sub_type = kwargs.get('sub_type')
        self.name = kwargs.get('name')
        self._is_embedded = kwargs.get('is_embedded')
        self.description = kwargs.get('description')
        self._destination_folder_id = kwargs.get('destination_folder_id')
        self._forms = [
            AttributeForm.from_dict(expr, self._connection) for expr in kwargs.get('forms')
        ] if kwargs.get('forms') else None
        self._attribute_lookup_table = SchemaObjectReference.from_dict(
            kwargs.get('attribute_lookup_table')) if kwargs.get('attribute_lookup_table') else None
        self._key_form = FormReference.from_dict(
            kwargs.get('key_form')) if kwargs.get('key_form') else None
        self._displays = AttributeDisplays.from_dict(
            kwargs.get('displays')) if kwargs.get('displays') else None
        self._sorts = AttributeSorts.from_dict(
            kwargs.get('sorts')) if kwargs.get('sorts') else None
        self._relationships = [kwargs.get('relationships')
                              ] if kwargs.get('relationships') else None  # noqa
        self._version_id = kwargs.get('version_id')
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat) else ExpressionFormat(show_expression_as)

    def alter(
        self,
        sub_type: Optional[str] = None,
        name: Optional[str] = None,
        is_embedded: Optional[bool] = None,
        description: Optional[str] = None,
        destination_folder_id: Optional[str] = None,
        forms: Optional[List[AttributeForm]] = None,
        attribute_lookup_table: Optional[SchemaObjectReference] = None,
        key_form: Optional[FormReference] = None,
        displays: Optional[AttributeDisplays] = None,
        sorts: Optional[AttributeSorts] = None,
        relationships: Optional[Relationship] = None,
    ):
        """Alter attribute properties.

        Args:
            name: attribute's name
            description: attribute's description
            is_embedded: If true indicates that the target object of this
                reference is embedded within this object. Alternatively if
                this object is itself embedded, then it means that the target
                object is embedded in the same container as this object.
            destination_folder_id: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id.
            forms: attribute's forms list
            attribute_lookup_table: Information about an object referenced
                within the  specification of another object. An object reference
                typically contains only enough fields to uniquely identify
                the referenced objects.
            key_form: a key form of an attribute
            displays: The collections of attribute displays and browse displays
                of the attribute.
            sorts: The collections of attribute sorts and browse sorts
                of the attribute.
            relationships: the list of relationships that one attribute has.
        """
        key_form = self.validate_key_form(key_form or self.key_form, forms or self.forms)
        displays = self.validate_displays(displays or self.displays, forms or self.forms)
        sorts = self.validate_sorts(sorts or self.sorts, forms or self.forms)

        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    # Attribute relationships management
    def add_child(self, child: Optional[SchemaObjectReference] = None,
                  joint_child: Optional[List[SchemaObjectReference]] = None,
                  relationship_type: Relationship.RelationshipType = Relationship.RelationshipType
                  .ONE_TO_MANY, table: Optional[SchemaObjectReference] = None) -> None:
        """Add a child to the attribute.

        Args:
            child: SchemaObjectReference of an attribute
            joint_child: list of SchemaObjectReferences of an attributes
            relationship_type: RelationshipType enum object, by default
                RelationshipType.ONE_TO_MANY
            table: SchemaObjectReference of a lookup table, if not passed
                attribute lookup table is used
        """
        if (child and joint_child) or (not child and not joint_child):
            raise ValueError("Please specify either 'child' or 'joint_child' parameter.")
        elif child:
            for rel in self.relationships:
                if hasattr(rel, 'child') and rel.child == child:
                    warnings.warn(f"{child.name} already is a child of the attribute '{self.id}'"
                                  " and will be omitted.")
                    return None
        elif joint_child:
            for rel in self.relationships:
                if hasattr(rel, 'joint_child') and rel.joint_child == joint_child:
                    children = "[" + ", ".join(child.name for child in joint_child) + "]"
                    warnings.warn(
                        f"{children} already is a joint_child of the attribute '{self.id}'"
                        " and will be omitted.")
                    return None

        parent = SchemaObjectReference.create_from(self)
        table = table or self.attribute_lookup_table

        return self._update_relationships(
            Relationship(relationship_type, table, parent, child, joint_child))

    def add_parent(self, parent: SchemaObjectReference, relationship_type: Relationship
                   .RelationshipType = Relationship.RelationshipType.ONE_TO_MANY,
                   table: Optional[SchemaObjectReference] = None) -> None:
        """Add a parent to the attribute.

        Args:
            parent: SchemaObjectReference of an attribute
            relationship_type: RelationshipType enum object, by default
                RelationshipType.ONE_TO_MANY
            table: SchemaObjectReference of a lookup table, if not passed
                attribute lookup table is used
        """
        for rel in self.relationships:
            if rel.parent.object_id == parent.object_id:
                warnings.warn(f"{parent.name} already is a parent of the attribute '{self.id}'"
                              " and will be omitted.")
                return None
        child = SchemaObjectReference.create_from(self)
        table = table or self.attribute_lookup_table

        return self._update_relationships(Relationship(relationship_type, table, parent, child))

    def remove_child(self, child: Optional[SchemaObjectReference] = None,
                     joint_child: Optional[List[SchemaObjectReference]] = None) -> None:
        """Removes a child of the attribute.

        Args:
            child: SchemaObjectReference of an attribute to be removed
                from child relationship
            joint_child: list of SchemaObjectReferences of an attributes
                to be removed from joint child relationship
        """
        if (child and joint_child) or (not child and not joint_child):
            raise ValueError("Please specify either 'child' or 'joint_child' parameter.")
        elif joint_child:
            for rel in self.relationships:
                if hasattr(rel, 'joint_child') and rel.joint_child == joint_child:
                    return self._update_relationships(rel, add=False)
            child_name = "[" + ", ".join(child.name for child in joint_child) + "]"
        elif child:
            for rel in self.relationships:
                if hasattr(rel, 'child') and rel.child == child:
                    return self._update_relationships(rel, add=False)
            child_name = child.name

        warnings.warn(f"{child_name} is not a child/joint_child of the attribute '{self.id}'"
                      " and will be omitted.")

    def remove_parent(self, parent: SchemaObjectReference) -> None:
        """Removes a parent of the attribute.

        Args:
            parent: SchemaObjectReference of an attribute to be removed
                from parent relationship
        """
        for rel in self.relationships:
            if rel.parent.object_id == parent.object_id and parent.object_id != self.id:
                return self._update_relationships(rel, add=False)

        warnings.warn(
            f"{parent.name} is not a parent of the attribute '{self.id}' and will be omitted.")

    def _update_relationships(self, relationship: Relationship, add=True) -> None:
        """Inner method for sending updated relationships list.

        Args:
            relationship: relationship to add or remove
            add: if True the relationship will be added to the attribute
                relationships, else it will be removed from them
        """
        relationships = self.relationships.copy()
        if add:
            relationships.append(relationship)
        else:
            relationships = [rel for rel in relationships if rel != relationship]
        self._alter_properties(relationships=relationships)

    def list_relationship_candidates(
            self, already_used: bool = True,
            to_dictionary: bool = True) -> Union[dict, List[SchemaObjectReference]]:
        """Lists potential relationship candidates for the Attribute.

        Args:
            already_used: whether to show Attributes References, which
                are already parents or children
            to_dictionary: whether to return results as a dict or list
        Returns:
            Dictionary with table names as keys and list
            of SchemaObjectReferences of the attributes as values
            if to_dictionary set to True, list of SchemaObjectReference
            of attributes as list otherwise.
        """
        key_form_expressions = [
            expr for form in self.forms if form.id == self.key_form.id for expr in form.expressions
        ]
        potential_tables = [tab for exp in key_form_expressions for tab in exp.tables]

        result = {}
        for tab in potential_tables:
            table = tables.get_table(self.connection, tab.object_id,
                                     project_id=self.connection.project_id)
            attribute_references = table.json()['attributes']
            candidates = [
                SchemaObjectReference.from_dict(attr['information'])
                for attr in attribute_references
                if attr['information']['objectId'] != self.id
            ]
            if candidates:
                result[tab.name] = candidates

        if already_used is False:
            children = [
                rel.child
                for rel in self.relationships
                if hasattr(rel, 'child') and rel.child.object_id != self.id
            ]
            parents = [rel.parent for rel in self.relationships if rel.parent.object_id != self.id]
            used = [*children, *parents]
            result = {
                tab: [candidate for candidate in candidates if candidate not in used
                     ] for tab, candidates in result.items()  # noqa
            }

        if to_dictionary is False:
            result = list({ref for references in list(result.values()) for ref in references})

        return result

    def list_tables(
            self, expression: Optional[Union[FactExpression,
                                             str]] = None) -> List[SchemaObjectReference]:
        """List all tables in the given expression. If expression is not
        specified, list all tables for attribute.

        Args:
            expression: the expression for which to list tables

        Returns:
            List of tables in the given expression or all tables for attribute.
        """
        expressions = [
            expr for form in self.forms if form.expressions for expr in form.expressions
        ]
        if expression:
            expression_id = expression.id if isinstance(expression, FactExpression) else expression
            expressions = [expr for expr in expressions if expr.id == expression_id]

        table_list = {tab for expr in expressions for tab in expr.tables}

        return list(table_list)

    # Attribute forms management
    def __alter_form_with_id(self, form_id: str, func: Callable, params: dict):
        forms = []
        is_form_found = False

        for form in self.forms:
            if form.id == form_id:
                is_form_found = True
                func(form, **params)
            forms.append(form)

        if not is_form_found:
            raise ValueError(f"Attribute Form with ID: {form_id} has not been found.")

        self._alter_properties(forms=forms)

    def get_form(self, id: str = None, name: str = None) -> Optional[AttributeForm]:
        """Retrieve a certain attribute form of a local instance of
        Attribute object.

        Args:
            id: ID of the attribute form. It has priority over `name` parameter
            name: name of the attribute form
        """
        if id:
            for form in self.forms:
                if form.id == id:
                    return form
        elif name:
            for form in self.forms:
                if form.name == name:
                    return form
        else:
            raise ValueError("Provide id or name.")

    def get_fact_expression(self, expression_id: str, form_id: str = None,
                            form_name: str = None) -> Optional[FactExpression]:
        """Retrieve a certain fact expression of a local instance of
        Attribute object.

        Args:
            form_id: ID of the attribute form. It have priority over `name`
                parameter
            form_name: name of the attribute form
            expression_id: ID of the fact expression
        """
        form = self.get_form(form_id, form_name)
        return form.get_fact_expression(expression_id)

    def add_form(
        self,
        form: Optional[AttributeForm] = None,
        name: Optional[str] = None,
        expressions: Optional[List[FactExpression]] = None,
        lookup_table: Optional[SchemaObjectReference] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        display_format: Optional[AttributeForm.DisplayFormat] = None,
        data_type: Optional[DataType] = None,
        alias: Optional[str] = None,
        child_forms: Optional[List[FormReference]] = None,
        geographical_role: Optional[AttributeForm.GeographicalRole] = None,
        time_role: Optional[AttributeForm.TimeRole] = None,
        is_form_group: bool = False,
        is_multilingual: bool = False,
    ):
        """Create new attribute form and add it to the `attribute.forms` list.
        The form can be added from completed `AttributeForm` objects provided
        in `form` patameter, or by filling other parameters.

        Args:
            form: complete `AttibuteForm` object that will be added to
                the Attribute
            name: The name of the attribute form set by the attribute. Unlike
                category, which is the systemic name associated with each
                reusable form, this name is specific to the attribute using this
                form
            expressions: Array with a member object for each separately defined
                expression currently in use by a fact. Often a fact expression
                takes the form of just a single column name, but more complex
                expressions are possible.
            lookup_table: lookup table of the AttributeForm. It has to be a
                lookup table used in one of the expressions assigned to
                AttributeForm
            description: description of the AttributeForm
            category: The category of the attribute form. Unlike name, this
                field is independent of the attribute using this form. This
                field can only be set when creating a new form. Once a form
                is created, its category becomes non-mutable. If not provided
                (or set as None) when an attribute is being created, a custom
                category will be automatically generated.
            display_format: display format of the AttributeForm
            data_type: Representation in the object model for a data-type that
                could be used for a SQL column.
            alias: alias of the AttributeForm
            child_forms: only used if 'is_form_group' is set to true
            geographical_role: identifies the type of geographical information
                this form represents
            time_role: time role of the AttributeForm
            is_form_group: A boolean field indicating whether this form is
                a form group (if true) or a simple form (if false).
            is_multilingual: A boolean field indicating whether this field is
                multilingual. Any key form of the attribute is not allowed
                to be set as multilingual.
        """
        if form and isinstance(form, AttributeForm):
            self._alter_properties(forms=self.forms + [form])
        elif expressions and lookup_table:
            properties = filter_params_for_func(AttributeForm.local_create, locals(),
                                                exclude=['self'])
            properties = delete_none_values(properties, recursion=True)
            new_form = AttributeForm.local_create(connection=self.connection, **properties)
            self._alter_properties(forms=self.forms + [new_form])
        else:
            raise AttributeError(
                'Please provide either `form` or `expressions` and `lookup_table`')

    @classmethod
    def _remove_form_from_displays(cls, form_to_be_removed: AttributeForm,
                                   forms: List[AttributeForm],
                                   displays: AttributeDisplays) -> AttributeDisplays:
        """Remove all references to the form from local instance of displays,
        AttributeDisplays object.

        Args:
            form_to_be_removed: form that will be removed
            forms: Attribute.forms list without the form that will be
                removed
            displays: Attribute.displays from which the form will be removed

        Return:
            AttributeDisplays object without references to the removed form
        """
        displays = deepcopy(displays)
        for index in range(len(displays.report_displays)):
            if form_to_be_removed.is_referenced_by(displays.report_displays[index]):
                displays.report_displays.pop(index)
                break
        for index in range(len(displays.browse_displays)):
            if form_to_be_removed.is_referenced_by(displays.browse_displays[index]):
                displays.browse_displays.pop(index)
                break
        return cls.validate_displays(displays, forms)

    @classmethod
    def _remove_form_from_sorts(cls, form_to_be_removed: AttributeForm, forms: List[AttributeForm],
                                sorts: AttributeSorts) -> AttributeSorts:
        """Remove all references to the form from local instance of displays,
        AttributeSorts object.

        Args:
            form_to_be_removed: form that will be removed
            forms: Attribute.forms list without the form that will be
                removed
            sorts: Attribute.sorts from which the form will be removed

        Return:
            AttributeSorts object without references to the removed form
        """
        sorts = deepcopy(sorts)
        for index in range(len(sorts.report_sorts)):
            if form_to_be_removed.is_referenced_by(sorts.report_sorts[index].form):
                sorts.report_sorts.pop(index)
                break
        for index in range(len(sorts.browse_sorts)):
            if form_to_be_removed.is_referenced_by(sorts.browse_sorts[index].form):
                sorts.browse_sorts.pop(index)
                break
        return cls.validate_sorts(sorts, forms)

    def remove_form(self, form_id: str, new_key_form: Optional[FormReference] = None):
        """Remove attribute form with a given `form_id`. If this form was
        present in `displays` or `sorts`, it will be automatically removed
        from there.

        Args:
            form_id: ID of the form that should be removed
            new_key_form: new value of the attribute's `key_form` parameter.
                Mandatory if the form that is to be removed is the current
                key form, otherwise optional.
        """
        new_forms = []
        form_to_del = None
        for form in self.forms:
            if form.id == form_id:
                form_to_del = form
            else:
                new_forms.append(form)

        # Make sure the key form is changed if needed, and other basic logic
        new_key_form = new_key_form or self.key_form
        if form_to_del is None:
            raise ValueError(f'Attribute with ID {self.id} does not '
                             f'contain attribute form with ID {form_id}.')
        elif len(new_forms) == 0:
            raise ValueError('You can not delete the last attribute form')
        elif form_to_del.is_referenced_by(self.key_form):
            error_msg = 'You are trying to delete the current key form. Please chose new key form.'
            # Assign new key form if possible
            new_key_form = self.validate_key_form(new_key_form, new_forms, error_msg)

        # Make sure the form that is also removed from displays and sorts
        displays = self._remove_form_from_displays(form_to_del, new_forms, self.displays)
        sorts = self._remove_form_from_sorts(form_to_del, new_forms, self.sorts)

        self._alter_properties(key_form=new_key_form, forms=new_forms, displays=displays,
                               sorts=sorts)

    def alter_form(
        self,
        form_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        display_format: Optional[AttributeForm.DisplayFormat] = None,
        data_type: Optional[DataType] = None,
        expressions: Optional[List[FactExpression]] = None,
        alias: Optional[str] = None,
        lookup_table: Optional[SchemaObjectReference] = None,
        child_forms: Optional[List[FormReference]] = None,
        geographical_role: Optional[AttributeForm.GeographicalRole] = None,
        time_role: Optional[AttributeForm.TimeRole] = None,
        is_form_group: Optional[bool] = None,
        is_multilingual: Optional[bool] = None,
    ):
        """Alter attribute form with a given `form_id`.

        Args:
            form_id: ID of the attribute form that will be altered
            name: The name of the attribute form set by the attribute. Unlike
                category, which is the systemic name associated with each
                reusable form, this name is specific to the attribute using
                this form
            description: description of the AttributeForm
            display_format: display format of the AttributeForm
            data_type: Representation in the object model for a data-type that
                could be used for a SQL column.
            expressions: Array with a member object for each separately defined
                expression currently in use by a fact. Often a fact expression
                takes the form of just a single column name, but more complex
                expressions are possible.
            alias: alias of the AttributeForm
            lookup_table: lookup table of the AttributeForm. It has to be a
                lookup table used in one of the expressions assigned to
                AttributeForm
            child_forms: only used if 'is_form_group' is set to true
            geographical_role: identifies the type of geographical information
                this form represents
            time_role: time role of the AttributeForm
            is_form_group: A boolean field indicating whether this form is
                a form group (if true) or a simple form (if false).
            is_multilingual: A boolean field indicating whether this field is
                multilingual. Any key form of the attribute is not allowed
                to be set as multilingual."""
        form_properties = filter_params_for_func(AttributeForm.local_alter, locals(),
                                                 exclude=['self'])
        self.__alter_form_with_id(form_id, AttributeForm.local_alter, form_properties)

    # Attribute form expressions management
    def alter_fact_expression(
        self,
        form_id: str,
        fact_expression_id: str,
        expression: Optional['Expression'] = None,
        tables: Optional[List[SchemaObjectReference]] = None,
    ):
        """Alter fact expression of the attribute form with given ID
        Args:
            form_id: ID of the form that uses certain expression
            fact_expression_id: ID of the fact expression that is to be altered,
            expression: new expressions of the fact expression
            tables: new tables of the fact expression
        """
        expression_properties = filter_params_for_func(AttributeForm._alter_expression, locals(),
                                                       exclude=['self'])
        self.__alter_form_with_id(form_id, AttributeForm._alter_expression, {
            'fact_expression_id': fact_expression_id,
            **expression_properties
        })

    def add_fact_expression(self, form_id: str, expression: FactExpression):
        """Add expression to the form.
        Args:
            form_id: ID of the form to which the expression is to be added,
            expression: the expression that is to be added,
        """
        self.__alter_form_with_id(form_id, AttributeForm._add_fact_expression,
                                  {'expression': expression})

    def remove_fact_expression(self, form_id: str, fact_expression_id: str,
                               new_lookup_table: Optional[SchemaObjectReference] = None):
        """Remove expression from the form. If the expressions left are
        not using lookup table assigned to the form, provide new lookup
        table for the form.

        Args:
            form_id: ID of the form from which the expression is to be removed,
            expression_id: ID of the expression that is to be removed,
            new_lookup_table: new lookup table of the form
        """
        self.__alter_form_with_id(form_id, AttributeForm._remove_fact_expression, {
            'fact_expression_id': fact_expression_id,
            'new_lookup_table': new_lookup_table
        })

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        result.pop('_showExpressionAs', None)

        return result

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
    def forms(self):
        return self._forms

    @property
    def attribute_lookup_table(self):
        return self._attribute_lookup_table

    @property
    def key_form(self):
        return self._key_form

    @property
    def displays(self):
        return self._displays

    @property
    def sorts(self):
        return self._sorts

    @property
    def relationships(self):
        return self._relationships
