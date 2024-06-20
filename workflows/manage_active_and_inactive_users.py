"""
Manage active and inactive users.
Perform administrative tasks such as setting default language, listing
subscriptions.

1. Connect to environment using data from workstation
2. Get language object based on provided id
3. For each active user set up language which was retrieved in step 2
   as the default one
4. Get list of all inactive users
5. Print number of inactive users
6. For each inactive user get list of its subscriptions and print them with
   user name
"""

from mstrio.distribution_services.subscription.subscription_manager import (
    list_subscriptions,
)
from mstrio.server.language import Language
from mstrio.users_and_groups.user import list_users
from mstrio.connection import get_connection

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

ALTERED_LANGUAGE = Language(conn, id='000004124F95EF3956E52781700C1E7A')

# list active users
active_users = list_users(conn, enabled=True)

# set up default language for those users
for user in active_users:
    user.alter(language=ALTERED_LANGUAGE)

# list all inactive users and count them
inactive_users = list_users(conn, enabled=False)
inactive_users_count = len(inactive_users)
print('Number of inactive users:', inactive_users_count)

# list all related subscriptions for inactive users
for user in inactive_users:
    subscriptions = list_subscriptions(conn, project_id=conn.project_id, owner=user)
    print('Subscriptions for user', user.name, ':', subscriptions)
