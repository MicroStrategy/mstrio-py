"""This is the sample script to show how to manage filters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import Connection, get_connection
from mstrio.modeling import (
    ExpressionFormat, Filter, list_filters, SchemaManagement, SchemaUpdateType
)

# Following variables are defining basic filters
PROJECT_NAME = "<Project_name>"  # Insert name of project here
SEARCH_NAME = "<Search_name>"  # Insert part of the filter name to be searched for
FILTER_ID1 = "<Filter_ID>"  # Insert ID of existing filter here
FILTER_ID2 = "<Filter_ID>"  # Insert ID of existing filter here
FILTER_ID3 = "<Filter_ID>"  # Insert ID of existing filter here
FILTER_NAME = "<Filter_name>"  # Insert name of a new filter to be created
FILTER_NEW_NAME = "<Filter_name_alter>"  # Insert new name of edited Filter here
FILTER_NEW_DESC1 = "<Filter_desc>"  # Insert new description of edited filter here
FILTER_NEW_DESC2 = "<Filter_desc>"  # Insert new description of edited filter here
FOLDER_ID = "<Folder_ID>"  # Insert folder ID here

conn: Connection = get_connection(workstationData, PROJECT_NAME)

# Example filter qualification data with expression specified as tree
FILTER_QUALIFICATION_AS_TREE = {
    "tree": {
        "type": "predicate_metric_qualification",
        "predicateTree": {
            "function": "greater",
            "parameters": [
                {
                    "parameterType": "constant",
                    "constant": {
                        "type": "int64", "value": "1"
                    },
                }
            ],
            "levelType": "none",
            "metric": {
                "objectId": "CE8DAE7048998FFECF77418BDF2343B8",
                "subType": "metric",
                "name": "Item Count",
            },
            "metricFunction": "value",
            "isIndependent": 0,
            "nullInclude": 0,
        },
    },
}

# Example filter qualification data with expression specified as tokens
FILTER_QUALIFICATION_AS_TOKENS = {
    "tokens": [
        {
            "level": "resolved",
            "state": "initial",
            "value": "%",
            "type": "character",
        },
        {
            "level": "resolved",
            "state": "initial",
            "value": "[Item Count]",
            "type": "object_reference",
        },
        {
            "level": "resolved",
            "state": "initial",
            "value": ">",
            "type": "character",
        },
        {
            "level": "resolved", "state": "initial", "value": "1", "type": "unknown"
        },
        {
            "level": "resolved",
            "state": "initial",
            "value": "",
            "type": "end_of_text",
        },
    ],
}

# Filters management
# Get list of filters, with examples of different conditions
list_of_all_filters = list_filters(connection=conn)
list_of_limited_filters = list_filters(connection=conn, limit=10)
list_of_limited_filters_to_dict = list_filters(connection=conn, limit=10, to_dictionary=True)
list_of_filters_by_name = list_filters(connection=conn, name=SEARCH_NAME)

# list of filters with expressions represented as tree
list_of_filters_as_trees = list_filters(connection=conn, show_expression_as=ExpressionFormat.TREE)
# list of filters with expressions represented as tokens
list_of_filters_as_tokens = list_filters(
    connection=conn, show_expression_as=ExpressionFormat.TOKENS
)

# list of filters with qualification represented also in tokens format
list_of_filters_with_qualification_as_tokens = list_filters(
    connection=conn, show_filter_tokens=True
)

# create new empty filter
test_filter = Filter.create(
    connection=conn,
    name=FILTER_NAME,
    destination_folder=FOLDER_ID,
)

# create new filter using qualification as tree and
# specify to return qualification also in tokens format
test_filter_tree = Filter.create(
    connection=conn,
    name=(FILTER_NAME + "_tree"),
    destination_folder=FOLDER_ID,
    show_filter_tokens=True,
    qualification=FILTER_QUALIFICATION_AS_TREE,
)

# create new filter using qualification as tokens
test_filter_tokens = Filter.create(
    connection=conn,
    name=(FILTER_NAME + "_tokens"),
    destination_folder=FOLDER_ID,
    qualification=FILTER_QUALIFICATION_AS_TOKENS,
)

# Any changes to schema object must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])

# Alter filter
test_filter.alter(name=FILTER_NEW_NAME, description=FILTER_NEW_DESC1)

# Alter filter description
test_filter_tokens.alter(description=FILTER_NEW_DESC2)

# Delete newly created filter
test_filter.delete(force=True)

# Get specific filter by id with expressions represented as trees
filter_ = Filter(connection=conn, id=FILTER_ID1)

# Get specified filter by id with expressions represented as tokens
filter_tokens_expression = Filter(
    connection=conn, id=FILTER_ID2, show_expression_as=ExpressionFormat.TOKENS
)

# Get specified filter by id with qualification also in tokens format
filter_tokens_qualification = Filter(connection=conn, id=FILTER_ID2, show_filter_tokens=True)

# List filter properties
properties = filter_.list_properties()
