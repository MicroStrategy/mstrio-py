"""This is the demo script to show how administrator can manage security
filters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.access_and_security.security_filter import (
    AttributeFormSystemRef, AttributeRef, ConstantParameter, ConstantType, list_security_filters,
    LogicFunction, LogicOperator, PredicateForm, PredicateFormFunction, Qualification,
    SecurityFilter
)
from mstrio.object_management import full_search
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import list_user_groups, list_users

from mstrio.connection import get_connection

PROJECT_NAME = '<project_name>'  # Project to connect to

SECURITY_FILTER_ID = '<sec_filter_id>'
SECURITY_FILTER_NAME = '<sec_filter_name>'
SECURITY_FILTER_NAME_NEW = '<new_sec_filter_name>'
SECURITY_FILTER_NAME_2 = '<sec_filter_name_2>'
SECURITY_FILTER_DESCRIPTION = '<sec_filter_description>'
QUALIFICATION = Qualification(tree=PredicateForm(
    # see access_and_security/security_filter/predicates.py
    # for PredicateFormFunction values
    function=PredicateFormFunction.GREATER,
    # see access_and_security/security_filter/predicate_parameters.py
    # for ConstantType values
    parameters=[ConstantParameter(ConstantType.DOUBLE, '<value>')],
    # insert object id and its attribute name to which you want to refer to
    attribute=AttributeRef('<object_id>', '<attribute_name>'),
    # insert object id and its attribute form system name
    # to which you want to refer to
    form=AttributeFormSystemRef('<object_id>', '<attribute_form_system_name>')))
CUSTOMER_ATTRIBUTE_ID = '<object_with_attribute_id>'  # id of an object that uses the attribute
PROJECT_ID = '<project_id>'  # project in which a security filter will be searched for
FOLDER_ID = '<folder_id>'  # folder in which new security filter will be created
FOLDER_ID_NEW = '<new_folder_id>'  # folder to which a security filter will be moved

# see ObjectTypes enum in types.py for available values
OBJECT_TYPES = ObjectTypes.ATTRIBUTE_FORM
USED_BY_OBJECT_TYPE = ObjectTypes.ATTRIBUTE

# see access_and_security/security_filter/predicates.py
# for PredicateFormFunction values
PREDICATE_FORM_FUNCTION = PredicateFormFunction.EQUALS
# see access_and_security/security_filter/predicate_parameters.py
# for ConstantType values
PREDICATE_FORM_PARAM = ConstantParameter(ConstantType.STRING, '<value>')
# insert object id and its attribute name to which you want to refer to
PREDICATE_FORM_ATTRIBUTE = AttributeRef('<object_id>', '<attribute_name>')
# insert object id and its attribute form system name
# to which you want to refer to
PREDICATE_FORM_ATTRIBUTE_FORM = AttributeFormSystemRef('<object_id>',
                                                       '<attribute_form_system_name>')
# insert data locale used to select value of the form
PREDICATE_FORM_DATA_LOCALE = '<locale>'

# see access_and_security/security_filter/predicates.py
# for PredicateFormFunction values
PREDICATE_FORM_FUNCTION_2 = PredicateFormFunction.EQUALS
# see access_and_security/security_filter/predicate_parameters.py
# for ConstantType values
PREDICATE_FORM_PARAM_2 = ConstantParameter(ConstantType.STRING, '<value>')
# insert object id and its attribute name to which you want to refer to
PREDICATE_FORM_ATTRIBUTE_2 = AttributeRef('<object_id>', '<attribute_name>')
# insert object id and its attribute form system name
# to which you want to refer to
PREDICATE_FORM_ATTRIBUTE_FORM_2 = AttributeFormSystemRef('<object_id>',
                                                         '<attribute_form_system_name>')
# insert data locale used to select value of the form
PREDICATE_FORM_DATA_LOCALE_2 = '<locale>'

PARAMETER_CHANGED_VALUE = '<value>'  # value of paramater to change to
USER_NAME_BEGINS = '<username_begins>'  # beginning of username to look for
USER_GROUP_NAME_BEGINS = '<usergroup_name_begins>'  # beginning of usergroup to look for

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# list all security filters
list_security_filters(conn)

# initialize security filter by its id
sec_fil = SecurityFilter(conn, id=SECURITY_FILTER_ID)

# show information, qualification and members of the security filter
sec_fil.information.to_dict()
sec_fil.qualification.to_dict()
sec_fil.members

# create new security filter
name = SECURITY_FILTER_NAME
folder_id = FOLDER_ID
qualification = QUALIFICATION

new_sec_fil = SecurityFilter.create(conn, qualification, name, folder_id)

# Create new security filter with more than one attribute form.

# 1. Find attribute forms for the particular attribute
# You have to look for objects with type ObjectTypes.ATTRIBUTE_FORM which are
# used by object with type ObjectTypes.ATTRIBUTE and ID of particular attribute.
attr_forms_of_customer_attr = full_search(
    conn,
    project_id=PROJECT_ID,
    object_types=OBJECT_TYPES,
    to_dictionary=False,
    used_by_object_id=CUSTOMER_ATTRIBUTE_ID,
    used_by_object_type=USED_BY_OBJECT_TYPE,
)
# just a simple example of extracting just `name` and `id` from each dict of
# attribute form which was returned
tmp_dict = [{'id': a.id, 'name': a.name} for a in attr_forms_of_customer_attr]

# 2. To build security filter qualification where there are two attribute
# forms you have to create two separate `PredicateForm`s and connect them with
# `LogicOperator`. You cannot set values for two attribute forms in a single
# `PredicateForm`.
pf1 = PredicateForm(
    function=PREDICATE_FORM_FUNCTION,
    parameters=[PREDICATE_FORM_PARAM],
    attribute=PREDICATE_FORM_ATTRIBUTE,
    form=PREDICATE_FORM_ATTRIBUTE_FORM,
    data_locale=PREDICATE_FORM_DATA_LOCALE,
)
pf2 = PredicateForm(
    function=PREDICATE_FORM_FUNCTION_2,
    parameters=[PREDICATE_FORM_PARAM_2],
    attribute=PREDICATE_FORM_ATTRIBUTE_2,
    form=PREDICATE_FORM_ATTRIBUTE_FORM_2,
    data_locale=PREDICATE_FORM_DATA_LOCALE_2,
)
# see access_and_security/security_filter/predicates.py for LogicFunction values
logic_operator = LogicOperator(function=LogicFunction.AND, children=[pf1, pf2])
qualification2 = Qualification(tree=logic_operator)
name2 = SECURITY_FILTER_NAME_2
new_sec_fil2 = SecurityFilter.create(conn, qualification2, name2, folder_id)

# alter security filter - its name, description, qualification and folder
new_name = SECURITY_FILTER_NAME_NEW
new_description = SECURITY_FILTER_DESCRIPTION
# copy old qualification and change year
new_qualification = Qualification.from_dict(new_sec_fil.qualification.to_dict())
new_qualification.tree.parameters[0].constant['value'] = PARAMETER_CHANGED_VALUE
new_folder_id = FOLDER_ID_NEW
sec_fil.alter(qualification=new_qualification, name=new_name, description=new_description)

# prepare users and user groups for applying and revoking security filter
mstr_user = list_users(conn, name_begins=USER_NAME_BEGINS)[0]
system_monitors = list_user_groups(conn, name_begins=USER_GROUP_NAME_BEGINS)[0]

# apply user(s) and/or user group(s) to security filter
sec_fil.apply([mstr_user, system_monitors.id])

# revoke user(s) and/or user group(s) from security filter
sec_fil.revoke([mstr_user.id, system_monitors])
sec_fil.revoke(sec_fil.members)  # revoke all members of security filter

# apply security filter directly to user or user group
mstr_user.apply_security_filter(sec_fil)

# revoke security filter directly from user or user group
system_monitors.apply_security_filter(sec_fil.id)

# fetch the latest security filter state
sec_fil.fetch(fetch_definition=False, fetch_members=True)

# delete security filter. When `force` argument is set
# to `False` (default value) then deletion must be approved.
sec_fil.delete(force=True)
