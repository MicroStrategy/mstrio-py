from mstrio.connection import get_connection
from mstrio.users_and_groups.contact import list_contacts
from mstrio.users_and_groups.user import User

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# migrate addresses from one User to another
user_1 = User(conn, name='User Korean')
user_2 = User(conn, name='Tilda Austin')
for address in user_1.addresses:
    print(address)
    user_2.add_address(address=address['id'])
    user_1.remove_address(id=address['id'])

# migrate User contacts to another User
list_contacts = list_contacts(conn, linked_user=user_1)
for contact in list_contacts:
    contact.alter(linked_user=user_2)
