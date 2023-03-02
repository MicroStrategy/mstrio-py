"""This is the demo script to show how administrator can manage security
filters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling import (
    Attribute,
    AttributeFormPredicate,
    ConstantParameter,
    Expression,
    Function,
    list_attributes,
    ObjectSubType,
    Operator,
    SchemaObjectReference,
    Variant,
    VariantType
)
from mstrio.modeling.security_filter import list_security_filters, SecurityFilter
from mstrio.users_and_groups import list_user_groups, list_users

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List all security filters
security_filters = list_security_filters(conn)
print(security_filters)

# Define variables which can be later used in a script
SECURITY_FILTER_ID = $security_filter_id
SECURITY_FILTER_NAME = $security_filter_name

# Get a security filter by id
security_filter = SecurityFilter(conn, id=SECURITY_FILTER_ID)
print(security_filter)

# Get a security filter by name
security_filter = SecurityFilter(conn, name=SECURITY_FILTER_NAME)
print(security_filter)

# List the properties of the security filter
print(security_filter.list_properties())

# Show the qualification of the security filter
print(security_filter.qualification)

# List the members of the security filter
print(security_filter.members)

# Define variables which can be later used in a script
NEW_SECURITY_FILTER_NAME = $new_security_filter_name
CONSTANT_VALUE_1 = $constant_value_1
ATTRIBUTE_ID = $attribute_id
ATTRIBUTE_NAME = $attribute_name
ATTRIBUTE_FORM_ID = $attribute_form_id
ATTRIBUTE_FORM_NAME = $attribute_form_name

# create new security filter
QUALIFICATION = Expression(
    tree=AttributeFormPredicate(
        # see access_and_security/security_filter/predicates.py
        # for PredicateFormFunction values
        function=Function.GREATER,
        # see access_and_security/security_filter/predicate_parameters.py
        # for ConstantType values
        parameters=[
            ConstantParameter(constant=Variant(type=VariantType.STRING, value=CONSTANT_VALUE_1))
        ],
        # insert object id and its attribute name to which you want to refer to
        attribute=SchemaObjectReference(
            sub_type=ObjectSubType.ATTRIBUTE, object_id=ATTRIBUTE_ID, name=ATTRIBUTE_NAME
        ),
        # insert object id and its attribute form system name
        # to which you want to refer to
        form=SchemaObjectReference(
            sub_type=ObjectSubType.ATTRIBUTE_FORM_SYSTEM,
            object_id=ATTRIBUTE_FORM_ID,
            name=ATTRIBUTE_FORM_NAME
        )
    )
)

# Define a variable which can be later used in a script
FOLDER_ID = $folder_id  # folder in which new security filter will be created

new_security_filter = SecurityFilter.create(
    connection=conn,
    qualification=QUALIFICATION,
    name=NEW_SECURITY_FILTER_NAME,
    destination_folder=FOLDER_ID
)
print(new_security_filter)

# Create new security filter with more than one attribute form.

# 1. List attributes to get attribute IDs
attributes = list_attributes(conn)
print(attributes)

# Define variables which can be later used in a script
ATTRIBUTE_1_ID = $attribute_1_id
ATTRIBUTE_1_NAME = $attribute_1_name
ATTRIBUTE_2_ID = $attribute_2_id
ATTRIBUTE_2_NAME = $attribute_2_name

# 2. Find attribute forms for the particular attribute
attribute_1_forms = Attribute(conn, id=ATTRIBUTE_1_ID).forms
print(attribute_1_forms)

attribute_2_forms = Attribute(conn, id=ATTRIBUTE_2_ID).forms
print(attribute_2_forms)

# 3. To build security filter qualification where there are two attribute
# forms you have to create two separate `AttributeFormPredicate` objects
# and connect them with logic function using one value of `Function` enum.
# You cannot set values for two attribute forms in a single
# `AttributeFormPredicate`.

# Define variables which can be later used in a script
ATTRIBUTE_FORM_1_ID = $attribute_form_1_id
ATTRIBUTE_FORM_2_ID = $attribute_form_2_id
CONSTANT_VALUE_2 = $constant_value_2
CONSTANT_VALUE_3 = $constant_value_3
ATTRIBUTE_FORM_1_ID = $attribute_form_1_id
ATTRIBUTE_FORM_2_ID = $attribute_form_2_id

predicate1 = AttributeFormPredicate(
    function=Function.EQUALS,
    parameters=[
        ConstantParameter(constant=Variant(type=VariantType.STRING, value=CONSTANT_VALUE_2))
    ],
    attribute=SchemaObjectReference(
        sub_type=ObjectSubType.ATTRIBUTE, object_id=ATTRIBUTE_1_ID, name=ATTRIBUTE_1_NAME
    ),
    form=SchemaObjectReference(
        sub_type=ObjectSubType.ATTRIBUTE_FORM_SYSTEM,
        object_id=ATTRIBUTE_FORM_1_ID,
    ),
)
predicate2 = AttributeFormPredicate(
    function=Function.EQUALS,
    parameters=[
        ConstantParameter(constant=Variant(type=VariantType.STRING, value=CONSTANT_VALUE_2))
    ],
    attribute=SchemaObjectReference(
        sub_type=ObjectSubType.ATTRIBUTE, object_id=ATTRIBUTE_2_ID, name=ATTRIBUTE_2_NAME
    ),
    form=SchemaObjectReference(
        sub_type=ObjectSubType.ATTRIBUTE_FORM_SYSTEM,
        object_id=ATTRIBUTE_FORM_2_ID,
    ),
)

# Define variables which can be later used in a script
NEW_SECURITY_FILTER_NAME_2 = $new_security_filter_name_2
NEW_SECURITY_FILTER_DESCRIPTION = $new_security_filter_description

new_security_filter2 = SecurityFilter.create(
    connection=conn,
    qualification=Expression(
        tree=Operator(function=Function.AND, children=[predicate1, predicate2])
    ),
    name=NEW_SECURITY_FILTER_NAME_2,
    destination_folder=FOLDER_ID
)
print(new_security_filter2)

# alter security filter - its name, description, qualification and folder
security_filter.alter(name=NEW_SECURITY_FILTER_NAME, description=NEW_SECURITY_FILTER_DESCRIPTION)
print(security_filter)

# Define a variable which can be later used in a script
PARAMETER_CHANGED_VALUE = $parameter_changed_value  # value of parameter to change to

# copy old qualification and change value of parameter
new_qualification = security_filter.qualification
new_qualification.tree.parameters[0].constant.value = PARAMETER_CHANGED_VALUE

security_filter.alter(qualification=new_qualification)
print(security_filter)

# Define variables which can be later used in a script
USERNAME_BEGINS = $username_begins  # beginning of username to look for
USER_GROUP_NAME_BEGINS = $user_group_name_begins  # beginning of user group to look for

# prepare users and user groups for applying and revoking security filter
user = list_users(conn, name_begins=USERNAME_BEGINS)[0]
group = list_user_groups(conn, name_begins=USER_GROUP_NAME_BEGINS)[0]

# apply user(s) and/or user group(s) to security filter
security_filter.apply([user, group.id])

# revoke user(s) and/or user group(s) from security filter
security_filter.revoke([user.id, group])

# revoke all members of security filter
security_filter.revoke(security_filter.members)

# apply security filter directly to user or user group
user.apply_security_filter(security_filter)

# revoke security filter directly from user or user group
group.apply_security_filter(security_filter.id)

# fetch the latest security filter state
security_filter.fetch()

# delete security filter. When `force` argument is set
# to `False` (default value) then deletion must be approved.
security_filter.delete(force=True)
