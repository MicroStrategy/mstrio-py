"""This is the demo script to show how administrator can manage security
filters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection

from mstrio.access_and_security.security_filter import \
    list_security_filters, SecurityFilter, Qualification,\
    PredicateForm, PredicateFormFunction,\
    ConstantParameter, ConstantType,\
    AttributeRef, AttributeFormSystemRef

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
