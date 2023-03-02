"""This is the demo script to show how to manage metrics. This script will not
work without replacing parameters with real values. Its basic goal is to
present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling import (
    DataType,
    DefaultSubtotals,
    Dimensionality,
    DimensionalityUnit,
    FormatProperty,
    list_metrics,
    Metric,
    MetricFormat,
    ObjectSubType,
    SchemaManagement,
    SchemaObjectReference,
    SchemaUpdateType
)
from mstrio.modeling.expression import Expression, Token

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for. For the script to work correctly all occurences
# of `'<object_id>'` and others with form `<some_name>` need to be replaced with
# data specific to the object used.

# Define variables which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here
FOLDER_ID = $folder_id  # Insert folder ID here

conn = get_connection(workstationData, PROJECT_NAME)

# Example metric data.
# Parts of this dictionary will be used in the later parts of this demo script
METRIC_DATA = {
    'name': '<metric_name>',
    'sub_type': ObjectSubType.METRIC,
    'destination_folder': FOLDER_ID,
    "expression": Expression(
        text='Sum(Cost)',
        tokens=[
            Token(
                value='<token_value>',
                type=Token.Type.FUNCTION,
                target=SchemaObjectReference(sub_type=ObjectSubType.FUNCTION, object_id='<object_id>')
            ),
            Token(value='(', type=Token.Type.CHARACTER),
            Token(
                value='<token_value>',
                type=Token.Type.OBJECT_REFERENCE,
                target=SchemaObjectReference(sub_type=ObjectSubType.FACT, object_id='<object_id>')
            ),
            Token(value=')', type=Token.Type.CHARACTER),
            Token(value='', type=Token.Type.END_OF_TEXT)
        ]
    ),
    "dimensionality": Dimensionality(
        dimensionality_units=[
            DimensionalityUnit(
                dimensionality_unit_type=DimensionalityUnit.DimensionalityUnitType.ATTRIBUTE,
                aggregation=DimensionalityUnit.Aggregation.LAST_IN_RELATIONSHIP,
                filtering=DimensionalityUnit.Filtering.APPLY,
                group_by=True,
                relative_position=None,
                target=SchemaObjectReference(
                    sub_type=ObjectSubType.ATTRIBUTE,
                    name='<attribute_name>',
                    object_id='<object_id>'
                ),
                axis_collection=None
            ),
            DimensionalityUnit(
                dimensionality_unit_type=DimensionalityUnit.DimensionalityUnitType.ATTRIBUTE,
                aggregation=DimensionalityUnit.Aggregation.FIRST_IN_RELATIONSHIP,
                filtering=DimensionalityUnit.Filtering.IGNORE,
                group_by=True,
                relative_position=None,
                target=SchemaObjectReference(
                    sub_type=ObjectSubType.ATTRIBUTE, name='<attribute_name>', object_id='<object_id>'
                ),
                axis_collection=None
            )
        ]
    ),
    "conditionality": Metric.Conditionality(
        filter=SchemaObjectReference(
            sub_type=ObjectSubType.FILTER, name='<filter_name>', object_id='<object_id>'
        ),
        embed_method=Metric.Conditionality.EmbedMethod.METRIC_INTO_REPORT_FILTER,
        remove_elements=True
    ),
    'metric_format_type': Metric.MetricFormatType.HTML_TAG,
    "metric_subtotals": [
        Metric.MetricSubtotal(
            SchemaObjectReference(ObjectSubType.METRIC_SUBTOTAL, object_id='<object_id>')
        )
    ],
    "aggregate_from_base": False,
    "formula_join_type": Metric.FormulaJoinType.INNER,
    "smart_total": Metric.SmartTotal.DECOMPOSABLE_FALSE,
    "data_type": DataType(DataType.Type.INTEGER, 10, 0),
    "format": MetricFormat(
        values=[FormatProperty(type=FormatProperty.FormatType.NUMBER_CATEGORY, value=0)],
        header=[
            FormatProperty(type=FormatProperty.FormatType.NUMBER_CATEGORY, value=4),
            FormatProperty(type=FormatProperty.FormatType.NUMBER_DECIMAL_PLACES, value=1),
        ],
    ),
    "subtotal_from_base": False,
    "column_name_alias": "<column_name_alias>",
    "thresholds": None
}

# Metric management
# Get list of metrics, with examples of different conditions
list_of_all_metrics = list_metrics(connection=conn)
list_of_metrics_with_limit = list_metrics(connection=conn, limit=10)

# Define variables which can be later used in a script
METRIC_NAME = $metric_name  # Insert name of edited metric here
METRIC_ID = $metric_id  # Insert ID of edited metric here

list_of_metrics_by_name = list_metrics(connection=conn, name=METRIC_NAME)
list_of_metrics_by_id = list_metrics(connection=conn, id=METRIC_ID)
list_of_metrics_in_folder = list_metrics(connection=conn, root=FOLDER_ID)

# Get specific metric by id or name
metr = Metric(connection=conn, id=METRIC_ID)
metr = Metric(connection=conn, name=METRIC_NAME)

# Listing properties
properties = metr.list_properties()

# Create metric
metr = Metric.create(
    connection=conn,
    name=METRIC_DATA['name'],
    sub_type=METRIC_DATA['sub_type'],
    destination_folder=METRIC_DATA['destination_folder'],
    expression=METRIC_DATA['expression'],
    metric_format_type=METRIC_DATA['metric_format_type'],
    metric_subtotals=METRIC_DATA['metric_subtotals'],
    format=METRIC_DATA['format'],
)

# or do it with one-liner unpacking `METRIC_DATA` dictionary
# (delete metric first, as it would have the same name and cause error)
metr.delete(True)
metr = Metric.create(connection=conn, **METRIC_DATA)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])

# MetricSubtotals
# During creation of `Metric` you can either use custom subtotals:
custom_subtotal = Metric.MetricSubtotal(
    definition=SchemaObjectReference(ObjectSubType.METRIC_SUBTOTAL, object_id='<object_id>')
)
# or default subtotals using `DefaultSubtotals`.:
default_subtotal = Metric.MetricSubtotal(definition=DefaultSubtotals.AVERAGE)

# Subtotals are also used to set the Dynamic Aggregation function and to set
# the Function for default subtotal (Total).

# To set the Dynamic Aggregation function we need to include a special subtotal
# in the metric_subtotals list. The definition has to be the default Aggregation
# subtotal, while the implementation needs to be set to the subtotal we want to
# set as the default dynamic aggregation function.
dynamic_aggregation = Metric.MetricSubtotal(
    definition=DefaultSubtotals.AGGREGATION, implementation=DefaultSubtotals.MODE
)

# To set the Function for default subtotal (Total) we do a similar approach, but
# instead of setting the definition to Aggregation, we set it to Total.
total_aggregation = Metric.MetricSubtotal(
    definition=DefaultSubtotals.TOTAL, implementation=DefaultSubtotals.MAXIMUM
)

# Now if we want to change the metrics subtotals we need to send the list of
# the totals we prepared as an alteration to metric_subtotals:
metr.alter(metric_subtotals=[default_subtotal, dynamic_aggregation, total_aggregation])

# Metric Format
# During creation of `Metric` and providing format in `MetricFormat`
# representation, `FormatProperty` class have to be used.
# The list of values with explanations for each Format Type is available in the
# docstrings of the class
new_format = MetricFormat(
    values=[FormatProperty(type=FormatProperty.FormatType.NUMBER_CATEGORY, value=0)],
    header=[
        FormatProperty(type=FormatProperty.FormatType.NUMBER_CATEGORY, value=4),
        FormatProperty(type=FormatProperty.FormatType.NUMBER_DECIMAL_PLACES, value=1),
    ],
)

# Setting every formatting available in Workstation is possible through Python.
# Below you can see a snippet on how to change the currency symbol to Euro and
# the currency symbol position to behind the number (10€).
currency_symbol_format = FormatProperty(
    type=FormatProperty.FormatType.NUMBER_CURRENCY_SYMBOL, value='€'
)
currency_symbol_position = FormatProperty(
    type=FormatProperty.FormatType.NUMBER_CURRENCY_POSITION, value='1'
)

new_format.values.append(currency_symbol_format)
new_format.values.append(currency_symbol_position)

# Depending on the `FormatProperty`s type, the value will be of different
# type (str, int, etc.). If it is related to color, use FormatProperty.Color
# with one of the three types of initialization: RGB, hex value or
# server readable form
rgb_color = FormatProperty(
    type=FormatProperty.FormatType.FONT_COLOR,
    value=FormatProperty.Color(red=255, green=102, blue=51)
)
hex_color = FormatProperty(
    type=FormatProperty.FormatType.FONT_COLOR, value=FormatProperty.Color(hex_value='#ff6633')
)
server_color = FormatProperty(
    type=FormatProperty.FormatType.FONT_COLOR, value=FormatProperty.Color(server_value='16737843')
)

new_format.values.append(rgb_color)

# Define variables which can be later used in a script
METRIC_NEW_NAME = $metric_new_name  # Insert new name of edited metric here
METRIC_NEW_DESCRIPTION = $metric_new_description  # Insert new description of edited metric here

# Alter metric using newly defined format
metr.alter(name=METRIC_NEW_NAME, description=METRIC_NEW_DESCRIPTION, format=new_format)

# Altering the Dimensionality and Conditionality of the Metric

# Altering Dimensionality and Conditionality can be done in two ways. They can
# be altered either through altering the Expression or their respective class,
# which is only possible when the metric is simple, as for compound metrics,
# both the classes are disabled and all the changes on them can only be done
# through altering the Expression.
# When both ways are used at once, the content of the Dimensionality and
# Conditionality classes has priority over Expression.

# Important thing to remember is when altering the Expression with new content,
# if the Metric already has a defined Dimensionality, Conditionality or both,
# they need to be included in the Expression tokens or they will be erased
# while altering the Expression.
# Alternatively when altering the Expression, providing the Dimensionality,
# Conditionality or both of them into the alter function will also preserve
# their respective contents in the metric without the necessity of including
# them into the contents of the Expression.

# Let us say that we want to change the Dimensionality to only work for the
# Item attribute, with the rules to ignore the report filter and to aggregate
# based on the first value of the lookup table and let us also say we want to
# change the Conditionality to be based around the East Region filter, with
# merging of the metric filter into the report filter and ignoring related report
# filter elements. The Dimensionality and Conditionality classes would then
# look like this:

dimensionality_example = Dimensionality(
    dimensionality_units=[
        DimensionalityUnit(
            dimensionality_unit_type=DimensionalityUnit.DimensionalityUnitType.ATTRIBUTE,
            aggregation=DimensionalityUnit.Aggregation.FIRST_IN_RELATIONSHIP,
            filtering=DimensionalityUnit.Filtering.IGNORE,
            group_by=True,
            relative_position=None,
            target=SchemaObjectReference(
                sub_type=ObjectSubType.ATTRIBUTE, name='<attribute_name>', object_id='<object_id>'
            ),
            axis_collection=None
        )
    ]
)

conditionality_example = Metric.Conditionality(
    filter=SchemaObjectReference(
        sub_type=ObjectSubType.FILTER, name='<filter_name>', object_id='<object_id>'
    ),
    embed_method=Metric.Conditionality.EmbedMethod.METRIC_INTO_REPORT_FILTER,
    remove_elements=True
)

# To achieve the same result with Expression, it would need to look like this:
expression_example = Expression(
    text='Sum(Cost)',
    tokens=[
        Token(
            value='<token_value>',
            type=Token.Type.FUNCTION,
            target=SchemaObjectReference(sub_type=ObjectSubType.FUNCTION, object_id='<object_id>')
        ),
        Token(value='(', type=Token.Type.CHARACTER),
        Token(
            value='<token_value>',
            type=Token.Type.OBJECT_REFERENCE,
            target=SchemaObjectReference(sub_type=ObjectSubType.FACT, object_id='<object_id>')
        ),
        Token(value=')', type=Token.Type.CHARACTER),
        # Here the dimensionality part begins:
        # Changes to dimensionality in the Expression need to be in {} brackets
        Token(value='{', type=Token.Type.CHARACTER),
        # The < symbolises aggregation by first value of the lookup table
        Token(value='<', type=Token.Type.CHARACTER),
        Token(
            value='<token_value>',
            type=Token.Type.OBJECT_REFERENCE,
            target=SchemaObjectReference(sub_type=ObjectSubType.ATTRIBUTE, object_id='<object_id>')
        ),
        # The % symbolises ignoring the report filter
        Token(value='%', type=Token.Type.CHARACTER),
        Token(value='}', type=Token.Type.CHARACTER),
        # Here the conditionality part begins:
        # Changes to conditionality in the Expression need to be in <> brackets
        Token(value='<', type=Token.Type.CHARACTER),
        Token(
            value='<token_value>',
            type=Token.Type.OBJECT_REFERENCE,
            target=SchemaObjectReference(sub_type=ObjectSubType.FILTER, object_id='<object_id>')
        ),
        # The @3 symbols represent merging the metric filter into the report filter
        Token(value=';', type=Token.Type.CHARACTER),
        Token(value='@', type=Token.Type.CHARACTER),
        Token(value='3', type=Token.Type.CHARACTER),
        # The ;- symbols represent setting the Ignore related filter elements to True
        Token(value=';', type=Token.Type.CHARACTER),
        Token(value='-', type=Token.Type.CHARACTER),
        Token(value='>', type=Token.Type.CHARACTER),
        Token(value='', type=Token.Type.END_OF_TEXT)
    ]
)

# Apply the change
metr.alter(expression=expression_example)

# Deleting metrics
metr.delete(force=True)
