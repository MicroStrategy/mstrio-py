"""This is the demo script to show how administrator can manage LDAP batch
import on Intelligence Server using mstrio.

Its basic goal is to present what can be done with this module and to
ease its usage.
"""

import time

from mstrio.connection import get_connection
from mstrio.server.environment import Environment


# Create connection based on workstation data
# Project selection is obsolete for working with LDAP batch import
conn = get_connection(workstationData)

# Environment object is already available to us via connection object,
# and LDAP controller is a property of Environment object
env = conn.environment
# You can also grab the Environment object directly
env = Environment(connection=conn)

ldap = env.ldap_batch_import
# you can grab the controller directly as well
ldap = conn.environment.ldap_batch_import
# or
ldap = Environment(connection=conn).ldap_batch_import

# start LDAP batch import
# (returns True in case of success, False otherwise)
ldap.start()

# check status
# you can get the cached status based on last action you performed locally,
# but this will not validate the status with I-Server
print(ldap.status)
# or you can grab the status directly from I-Server
# (this will also cache it for reference via `ldap.status` property, above)
print(ldap.check_status())

# All possible statuses are available via the ldap.ImportStatus enum
print(list(ldap.ImportStatus))

# Stop LDAP batch import (request will be successful even if import already
# finished, was already canceled, or there was no import running)
# (returns True in case of success, False otherwise)
ldap.stop()

# you can access all the details about last import
print(ldap.get_status_data())


# If you wish to wait for the import to finish before proceeding,
# you can do the logic below:
while ldap.check_status() == ldap.ImportStatus.IN_PROGRESS:
    time.sleep(1)  # wait a second before checking again

if ldap.status == ldap.ImportStatus.FINISHED:
    print("Import finished successfully")
else:
    print(f"Import finished with status: {ldap.status.value}")
