"""This is a template for a script to perform a batch LDAP import.
This script will work OOTB.

This script can only be run via Workstation (and then scheduled as Task)
currently. Modify how the `conn` Connection is set if you wish to run it
outside Workstation context.
"""

import time

from mstrio import config
from mstrio.connection import get_connection

# connect to the environment inside Workstation
conn = get_connection(connectionData)
ldap = conn.environment.ldap_batch_import

# start async ldap import
ldap.start()

# wait for finish
while ldap.check_status() == ldap.ImportStatus.IN_PROGRESS:
    time.sleep(config.delay_between_polling)  # wait a moment before checking again

if ldap.status == ldap.ImportStatus.FINISHED:
    print("Import finished successfully")
else:
    print(f"Import finished with status: {ldap.status}")
