from enum import auto
from typing import List, Optional, TYPE_CHECKING

from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.modeling.expression import Expression, FactExpression
from mstrio.modeling.schema.helpers import DataType, FormReference, SchemaObjectReference
from mstrio.types import ObjectTypes
from mstrio.utils.entity import Entity
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import delete_none_values, exception_handler, filter_params_for_func

if TYPE_CHECKING:
    from mstrio.modeling.schema.attribute.attribute_form import AttributeForm


class AttributeForm(Entity):  # noqa
    """The Attribute Form Object

    Args:
        connection: a `Connection` object tied to the desired environment
        id: Attribute Form ID. Note that Form ID is associated with the form
            category used. Multiple forms that use the same category will have
            the same ID. However, since no two forms within the same attribute
            can use the same category, no two forms will share an ID in
            the same attribute.
        name: The name of the attribute form set by the attribute. Unlike
            category, which is the systemic name associated with each reusable
            form, this name is specific to the attribute using this form.
        description: description of the AttributeForm
        category: The category of the attribute form. Unlike name, this field
            is independent of the attribute using this form. This field can
            only be set when creating a new form. Once a form is created, its
            category becomes non-mutable. If not provided (or set as None) when
            an attribute is being created, a custom category will be
            automatically generated.
        form_type: A read-only field indicating the type of this form. A custom
            form is created if its category is set to None.
        display_format: display format of the AttributeForm
        data_type: Representation in the object model for a data-type that
            could be used for a SQL column.
        expressions: Array with a member object for each separately defined
            expression currently in use by a fact. Often a fact expression
            takes the form of just a single column name, but more complex
            expressions are possible.
        alias: alias of the AttributeForm
        lookup_table: lookup table of the AttributeForm. It has to be a lookup
            table used in one of the expressions assigned to AttributeForm
        child_forms: only used if 'is_form_group' is set to true
        geographical_role: identifies the type of geographical information this
            form represents
        time_role: time role of the AttributeForm
        is_form_group: A boolean field indicating whether this form is a form
            group (if true) or a simple form (if false).
        is_multilingual: A boolean field indicating whether this field is
            multilingual. Any key form of the attribute is not allowed to be
            set as multilingual.
    """

    class FormType(AutoName):
        """Enumeration constants used to specify a type of this form."""
        CUSTOM = auto()
        SYSTEM = auto()

    class DisplayFormat(AutoName):
        """Enumeration constants used to specify display format of
        the attribute form."""
        NUMBER = auto()
        TEXT = auto()
        PICTURE = auto()
        URL = auto()
        EMAIL = auto()
        HTML_TAG = auto()
        DATE = auto()
        TIME = auto()
        SYMBOL = auto()
        PHONE_NUMBER = auto()
        DATE_TIME = auto()
        BIG_DECIMAL = auto()

    class GeographicalRole(AutoName):
        """Enumeration constants used to specify geographical role of
        the attribute form."""
        NONE = auto()
        CITY = auto()
        STATE = auto()
        COUNTRY = auto()
        LOCATION = auto()
        LATITUDE = auto()
        LONGITUDE = auto()
        OTHER = auto()
        ZIP_CODE = auto()
        COUNTY = auto()
        AREA_CODE = auto()
        GEOMETRY = auto()

    class TimeRole(AutoName):
        """Enumeration constants used to specify time role of
        the attribute form."""
        NONE = auto()
        DATE = auto()
        TIME = auto()
        SECOND = auto()
        MINUTE = auto()
        HOUR = auto()
        DAY = auto()
        WEEK = auto()
        MONTH = auto()
        QUARTER = auto()
        YEAR = auto()
        SEASONAL_ROOT = auto()
        YEAR_OF_DECADE = auto()
        QUARTER_OF_YEAR = auto()
        MONTH_OF_YEAR = auto()
        MONTH_OF_QUARTER = auto()
        WEEK_OF_YEAR = auto()
        WEEK_OF_QUARTER = auto()
        WEEK_OF_MONTH = auto()
        DAY_OF_YEAR = auto()
        DAY_OF_QUARTER = auto()
        DAY_OF_MONTH = auto()
        DAY_OF_WEEK = auto()
        HOUR_OF_DAY = auto()
        MINUTE_OF_DAY = auto()
        MINUTE_OF_HOUR = auto()
        SECOND_OF_DAY = auto()
        SECOND_OF_HOUR = auto()
        SECOND_OF_MINUTE = auto()
        SEASONAL_END = auto()

    _OBJECT_TYPE = ObjectTypes.ATTRIBUTE_FORM
    _API_GETTERS = {
        (
            'id',
            'name',
            'abbreviation',
            'type',
            'subtype',
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
            'target_info'
        ): objects.get_object_info
    }

    def __init__(self, connection: Connection, id: str) -> None:
        super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.category = kwargs.get('category')
        if self.FormType.has_value(kwargs.get('type')):
            self.form_type = self.FormType(kwargs.get('type'))
        elif kwargs.get('type'):
            self.type = kwargs.get('type')

        self.is_multilingual = kwargs.get('is_multilingual', False)
        self.is_form_group = kwargs.get('is_form_group', False)
        self.geographical_role = self.GeographicalRole(
            kwargs.get('geographical_role')
        ) if kwargs.get('geographical_role') else None
        self.time_role = self.TimeRole(kwargs.get('time_role')
                                       ) if kwargs.get('time_role') else None
        self.display_format = self.DisplayFormat(kwargs.get('display_format')
                                                 ) if kwargs.get('display_format') else None
        self.data_type = DataType.from_dict(kwargs.get('data_type')
                                            ) if kwargs.get('data_type') else None

        self.expressions = [
            FactExpression.from_dict(expr, self._connection) for expr in kwargs.get('expressions')
        ] if kwargs.get('expressions') else None

        self.alias = kwargs.get('alias')
        self.lookup_table = SchemaObjectReference.from_dict(
            kwargs.get('lookup_table')
        ) if kwargs.get('lookup_table') else None

        self.child_forms = [
            FormReference.from_dict(expr, self._connection) for expr in kwargs.get('child_forms')
        ] if kwargs.get('child_forms') else None

    @classmethod
    def local_create(
        cls,
        connection: Connection,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        display_format: Optional[DisplayFormat] = None,
        data_type: Optional[DataType] = None,
        expressions: Optional[List[FactExpression]] = None,
        alias: Optional[str] = None,
        lookup_table: Optional[SchemaObjectReference] = None,
        child_forms: Optional[List[FormReference]] = None,
        geographical_role: Optional[GeographicalRole] = None,
        time_role: Optional[TimeRole] = None,
        is_form_group: bool = False,
        is_multilingual: bool = False,
    ) -> "AttributeForm":
        """Internal method that creates ONLY LOCAL AttributeForm object.
        In order to create an AttributeForm object on the server,
        use `Attribute.add_form()` method of a corresponding Attribute object.
        """
        properties = filter_params_for_func(cls.local_create, locals(), exclude=['connection'])
        properties = delete_none_values(properties, recursion=True)

        obj = cls.__new__(cls)
        for key, val in properties.items():
            setattr(obj, key, val)
        obj._id = None
        obj._connection = connection
        return obj

    def list_properties(self, camel_case=True) -> dict:
        """Lists all properties of attribute form."""
        return super().to_dict(camel_case=camel_case)

    def to_dict(self, camel_case=True) -> dict:

        return {
            key: val
            for key,
            val in self.list_properties(camel_case).items()
            if key not in [
                'id',
                'abbreviation',
                'type',
                'subtype',
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
                'formType'
            ]
        }

    def local_alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        display_format: Optional[DisplayFormat] = None,
        data_type: Optional[DataType] = None,
        expressions: Optional[List[FactExpression]] = None,
        alias: Optional[str] = None,
        lookup_table: Optional[SchemaObjectReference] = None,
        child_forms: Optional[List[FormReference]] = None,
        geographical_role: Optional[GeographicalRole] = None,
        time_role: Optional[TimeRole] = None,
        is_form_group: Optional[bool] = None,
        is_multilingual: Optional[bool] = None,
    ):
        """Make changes to a local copy of AttributeForm. In order to change
        an AttributeForm object on the server, use `Attribute.alter_form()`
        method of a corresponding Attribute object.
        """
        properties = filter_params_for_func(self.local_alter, locals())

        for key, val in delete_none_values(properties, recursion=True).items():
            self.__setattr__(name=key, value=val)

    def get_fact_expression(self, id: str) -> FactExpression:
        """Get a fact expression of a local instance of
        AttributeForm object.

        Args:
            id: id of the fact expression
        """
        expressions = [expr for expr in self.expressions if expr.id == id]
        if not expressions:
            raise ValueError(
                f"AttributeForm with id {self.id} does not contain "
                f"Fact Expressions with id {id}."
            )
        return expressions[0]

    # Attribute form expressions management
    def _add_fact_expression(self, expression: FactExpression):
        """
        Internal method that affects ONLY LOCAL AttributeForm object.
        To make changes on the server, use `Attribute._add_fact_expression()`
        method of a corresponding Attribute object.
        Add expression to the form.
        Args:
            form_id: id of the form to which the expression is to be added,
            expression: the expression that is to be added,
        """
        self.verify_is_simple_form(method_name_if_error='Adding expression')
        self.expressions.append(expression)

    def _remove_fact_expression(
        self, fact_expression_id: str, new_lookup_table: Optional[SchemaObjectReference] = None
    ):
        """
        Internal method that affects ONLY LOCAL AttributeForm object.
        To make changes on the server, use `Attribute._remove_fact_expression()`
        method of a corresponding Attribute object.
        Remove expression from the form. If the expressions left are
        not using lookup table assigned to the form, provide new lookup
        table for the form.

        Args:
            form_id: id of the form from which the expression is to be removed,
            fact_expression_id: id of the expression that is to be removed,
            new_lookup_table: new lookup table of the form. Used if the
                expression that is going to be removed used the current one
        """
        self.verify_is_simple_form(method_name_if_error='Removing expression')
        if len(self.expressions) == 1:
            exception_handler(
                "You can't remove the only expression "
                f"from the attribute form with id: {self.id}.",
                ValueError
            )
        ex_postition = next(
            (i for i, ex in enumerate(self.expressions) if ex.id == fact_expression_id), None
        )
        if ex_postition is None:
            exception_handler(
                f"The form with id: {self.id}, don't use "
                f"expression with id: {fact_expression_id}.",
                ValueError
            )
        removed_ex = self.expressions.pop(ex_postition)

        # AttributeForm can't use `lookup_table` that is not used in any of
        # its expressions.
        if self.lookup_table in removed_ex.tables:
            if len(self.expressions) == 1 and len(self.expressions[0].tables) == 1:
                self.lookup_table = self.expressions[0].tables[0]
            elif new_lookup_table is None:
                exception_handler(
                    "Please provide new lookup_table for the attribute form "
                    f"with id: {self.id}.",
                    AttributeError
                )
            else:
                self.lookup_table = new_lookup_table

    def _alter_expression(
        self,
        fact_expression_id: str,
        expression: Optional[Expression] = None,
        tables: Optional[List[SchemaObjectReference]] = None,
    ):
        """Internal method that affects ONLY LOCAL AttributeForm object.
        To make changes on the server, use `Attribute.alter_fact_expression()`
        method of a corresponding Attribute object.

        Args:
            fact_expression_id: id of the fact expression that is to be altered,
            expression: new expressions of the fact expression
            tables: new tables of the fact expression
        """
        self.verify_is_simple_form(method_name_if_error='Altering expressions')
        try:
            fact_expr = next(expr for expr in self.expressions if expr.id == fact_expression_id)
            fact_expr.local_alter(expression, tables)
        except StopIteration:
            exception_handler(
                f"Attribute Form: {self.id} does not have Fact Expression"
                f" with ID: {fact_expression_id}.",
                ValueError
            )

    def verify_is_simple_form(self, method_name_if_error: str):
        """Verify whether the form is a simple form and not a group form"""
        if self.is_form_group:
            exception_handler(
                f"{method_name_if_error} is not available for the form group.", AttributeError
            )

    def is_referenced_by(self, form_reference: FormReference) -> bool:
        """Check if attribute form is referenced in `form_reference`."""
        if ((self.id is not None and self.id == form_reference.id)
                or (self.name is not None and self.name == form_reference.name)):
            return True
        return False
