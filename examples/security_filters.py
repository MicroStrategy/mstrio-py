"""This is the demo script to show how administrator can manage security
filters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection

from mstrio.access_and_security.security_filter import (AttributeFormSystemRef, AttributeRef,
                                                        ConstantParameter, ConstantType,
                                                        LogicFunction, LogicOperator,
                                                        list_security_filters, PredicateForm,
                                                        PredicateFormFunction, Qualification,
                                                        SecurityFilter)
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import list_users, list_user_groups

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# list all security filters
list_security_filters(conn)

# initialize security filter by its id
sec_fil = SecurityFilter(conn, id='12345678123456781234567812345678')

# show information, qualification and members of the security filter
sec_fil.information.to_dict()
sec_fil.qualification.to_dict()
sec_fil.members

# create new security filter
name = "Year > 2015"
folder_id = "E28806A611E5B55F088C0080EF555BA1"
qualification = Qualification(
    tree=PredicateForm(function=PredicateFormFunction.GREATER, parameters=[
        ConstantParameter(ConstantType.DOUBLE, "2015.0")
    ], attribute=AttributeRef("8D679D5111D3E4981000E787EC6DE8A4", "Year"),
                       form=AttributeFormSystemRef("45C11FA478E745FEA08D781CEA190FE5", "ID")))

new_sec_fil = SecurityFilter.create(conn, qualification, name, folder_id)

# Create new security filter with more than one attribute form.

# 1. Find attribute forms for the particular attribute
# You have to look for objects with type ObjectTypes.ATTRIBUTE_FORM which are
# used by object with type ObjectTypes.ATTRIBUTE and ID of particular attribute.
customer_attr_id = '8D679D3C11D3E4981000E787EC6DE8A4'
attr_forms_of_customer_attr = full_search(
    conn,
    project_id="B7CA92F04B9FAE8D941C3E9B7E0CD754",
    object_types=ObjectTypes.ATTRIBUTE_FORM,
    to_dictionary=False,
    used_by_object_id=customer_attr_id,
    used_by_object_type=ObjectTypes.ATTRIBUTE,
)
# just a simple example of extracting just `name` and `id` from each dict of
# attribute form which was returned
tmp_dict = [{'id': a.id, 'name': a.name} for a in attr_forms_of_customer_attr]

# 2. To build security filter qualification where there are two attribute
# forms you have to create two separate `PredicateForm`s and connect them with
# `LogicOperator`. You cannot set values for two attribute forms in a single
# `PredicateForm`.
pf1 = PredicateForm(
    function=PredicateFormFunction.EQUALS,
    parameters=[ConstantParameter(ConstantType.STRING, "Smith")],
    attribute=AttributeRef("8D679D3C11D3E4981000E787EC6DE8A4", "Customer"),
    form=AttributeFormSystemRef("CCFBE2A5EADB4F50941FB879CCF1721C", "Customer DESC 1"),
    data_locale="en-US",
)
pf2 = PredicateForm(
    function=PredicateFormFunction.EQUALS,
    parameters=[ConstantParameter(ConstantType.STRING, "John")],
    attribute=AttributeRef("8D679D3C11D3E4981000E787EC6DE8A4", "Customer"),
    form=AttributeFormSystemRef("8D67A35F11D3E4981000E787EC6DE8A4", "Customer DESC 2"),
    data_locale="en-US",
)
logic_operator = LogicOperator(function=LogicFunction.AND, children=[pf1, pf2])
qualification2 = Qualification(tree=logic_operator)
name2 = 'Customer John Smith'
new_sec_fil2 = SecurityFilter(conn, qualification2, name2, folder_id)

# alter security filter - its name, description, qualification and folder
new_name = "Year > 2020"
new_description = "Year in this security filter was altered from 2015 to 2020"
# copy old qualification and change year
new_qualification = Qualification.from_dict(new_sec_fil.qualification.to_dict())
new_qualification.tree.parameters[0].constant['value'] = "2020.0"
new_folder_id = "E287FE0E11E5B55F03C70080EF555BA1"
sec_fil.alter(qualification=new_qualification, name=new_name, description=new_description)

# prepare users and user groups for applying and revoking security filter
mstr_user = list_users(conn, name_begins='MSTR U')[0]
system_monitors = list_user_groups(conn, name_begins='System Moni')[0]

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
