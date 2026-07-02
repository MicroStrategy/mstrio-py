"""This is the demo script to show how to manage smart attributes.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling.schema.attribute.attribute import Attribute
from mstrio.modeling.schema.attribute.smart_attribute import (
    SmartAttribute,
    list_smart_attributes,
    list_smart_attribute_templates,
    update_smart_attributes,
)

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert ID of project here

conn = get_connection(connectionData, project_id=PROJECT_ID)

# Define variables which can be later used in a script
ATTRIBUTE_ID = $attribute_id  # Insert ID of the base attribute here

# List smart attributes derived from a base attribute
# The base attribute can be provided as an `Attribute` object or an ID
smart_attrs = list_smart_attributes(connection=conn, attribute=ATTRIBUTE_ID)
print(smart_attrs)
smart_attrs_as_dicts = list_smart_attributes(
    connection=conn, attribute=ATTRIBUTE_ID, to_dictionary=True
)
print(smart_attrs_as_dicts)

# The same can be done with an `Attribute` object
attribute = Attribute(connection=conn, id=ATTRIBUTE_ID)
smart_attrs = list_smart_attributes(connection=conn, attribute=attribute)

# List smart attribute templates that can be created for the base attribute
templates = list_smart_attribute_templates(connection=conn, attribute=ATTRIBUTE_ID)
print(templates)

# Reconcile smart attributes for the base attribute
# When no smart attributes are provided, the service regenerates
# the service-managed set based on the attribute's key form
regenerated = update_smart_attributes(connection=conn, attribute=ATTRIBUTE_ID)
print(regenerated)

# Define variables which can be later used in a script
SMART_ATTRIBUTE_ID = $smart_attribute_id
SMART_ATTRIBUTE_NAME = $smart_attribute_name

# When smart attributes are provided, applicable entries are merged into
# the service-managed set so fields such as `object_id` and `name` are
# respected. Omitted existing applicable entries are kept as-is; omitted
# missing applicable entries are auto-created, and existing non-applicable
# smart attributes may be removed.
reconciled = update_smart_attributes(
    connection=conn,
    attribute=ATTRIBUTE_ID,
    smart_attributes=[
        SmartAttribute(object_id=SMART_ATTRIBUTE_ID, name=SMART_ATTRIBUTE_NAME),
    ],
)
print(reconciled)

# Smart attributes scoped to a Mosaic data model are available through
# `DataModelAttribute.list_smart_attributes`,
# `DataModelAttribute.list_smart_attribute_templates` and
# `DataModelAttribute.update_smart_attributes`
# (see code_snippets/data_models.py)
