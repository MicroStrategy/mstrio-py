"""
    This is a template for creation of Transaction Script.

    Specifically, if the Transaction Dashboard is based on Python Script Datasource
    built from `data_source_script_all_users.py` template, those two will work
    out of the box end-to-end.

    It will work out of the box as is, as long as the Transaction Dashboard
    is configured correctly and all variables are set up.
"""

"""
    This example will allow a dashboard user to modify users in the environment.
    The workflow will rely on this script to make actual modifications
    (insert, update or delete) in the users.

    The data is modified using the mstrio-py library, which is installed in the default runtime.

    No additional external libraries are required for this script to work.
"""

import sys
from mstrio.connection import Connection
from mstrio.users_and_groups.user import User

# Those are three variables required for the script to work,
# none of which can be prompted: they need to be saved and will not be edited
# after saving the script
URL = $base_url
USER = $username
PASS = $password


conn = Connection(base_url=URL, username=USER, password=PASS)


# It is a good practice to `zip` all transaction columns like this, so that
# the script can handle them in a single loop, instead of having to
# handle each column separately.
#
# But this is not a requirement.
#
# Also, this set of variables are only an example. Transaction Scripts can decide
# any number and any type of columns to handle, as long as they are set up
# correctly in the Transaction Dashboard.
#
# In this example, we assume that the Transaction Dashboard consumer will pass
# the following columns:
# - txn_action: a list of actions to perform (insert, update, or select)
#       (this is a built-in type of column and is always provided from Transaction Dashboard)
# - user_id: a list of user IDs to read or modify
# - user_name: a list of user names to read or modify
# - user_enabled: a list of user enabled status ('1' for enabled, '0' for disabled)
rows = zip($txn_action, $user_id, $user_name, $user_enabled)


for action, uid, uname, uenabled in rows:
    enabled = uenabled == '1'  # we're converting a string '1' or '0' to a boolean value

    try:
        # `try` here is a good practice - we should always assume something can go wrong,
        # but the script should not crash, so we need to handle it

        if action == 'select':
            # if Transaction Dashboard consumer just selected a row in Dashboard without changes in it:
            # it should be deleted
            user = User(conn, id=uid)
            if user:
                user.delete(force=True)

        elif action == 'insert':
            # Transaction Dashboard consumer wants to create a new user.

            # for this example specifically we build username from full name so we
            # remove spaces from it
            username = uname.replace(' ', '_')
            User.create(conn,
                username=username, full_name=uname,
                enabled=enabled,
                password='qwer1234!', require_new_password=True)

        elif action == 'update':
            # Transaction Dashboard consumer wants to alter the properties of existing user
            user = User(conn, id=uid)
            if user:
                user.alter(full_name=uname, enabled=enabled)

        else:
            # unexpected and unreachable - ignore and move to next row of data
            continue
    except Exception as err:
        # log the output of the error, if any happened, and proceed to next row of data
        print(f"Failed '{action}' for user '{uname}' (id={uid}): {str(err)}", file=sys.stderr)
        continue
