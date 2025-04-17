"""
Facilitate the migration of user data from one user to another such as
addresses or contacts.

1. Connect to the environment using data from the workstation
2. Get first user object based on provided name ('User Korean')
3. Get second user object based on provided name ('Tilda Austin')
4. Add addresses of the first user to the second user and remove them from
   the first user. Print each address before the operation
5. Get list of contacts for the first user
6. For each contact in the list alter the linked user to the second user
"""

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
    user_2.add_address(contact_address=address)
    user_1.remove_address(id=address['id'])

# migrate User contacts to another User
list_contacts = list_contacts(conn, linked_user=user_1)
for contact in list_contacts:
    contact.alter(linked_user=user_2)
