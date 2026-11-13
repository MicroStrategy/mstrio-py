"""This is the demo script to show how administrator can manage LDAP settings
of Intelligence Server using mstrio.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server import LDAPSettings

# Define variables which can be later used in a script
USER_FILTER = $user_filter  # LDAP search filter for users
GROUP_FILTER = $group_filter  # LDAP search filter for groups

# Create connection based on connection data
# Project selection is obsolete for working with LDAP settings
conn = get_connection(connectionData)

# get LDAP settings of the I-Server
ldap = LDAPSettings(connection=conn)
# LDAP settings are available also via the Environment object
ldap = conn.environment.ldap_settings

# list all LDAP settings and their values
print(ldap.list_properties())

# set the search filters and the options of the LDAP batch import
ldap.user_import_filter = USER_FILTER
ldap.group_import_filter = GROUP_FILTER
ldap.import_user = True
ldap.import_group = True

# apply the changes; only the modified settings are sent to the I-Server
ldap.update()

# clear a search filter by setting it to an empty string
ldap.group_import_filter = ""
ldap.update()

# start the LDAP batch import with the new settings
# (see `ldap_batch_import.py` code snippet for more details)
conn.environment.ldap_batch_import.start()
