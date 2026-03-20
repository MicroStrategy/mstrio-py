"""
    This is a template for creation of Datasource Script.

    Note:
        Also, if you use this template to create a datasource for Transaction Dashboard,
        which will be based on `transaction_edit_users.py` script template,
        those two will work out of the box end-to-end.

    It will work out of the box as is, when all variables are filled in.

    Three methods need to be created for the workflow to work:
        browse(): retrieves the catalog information
        preview(): gets partial data for preview, data refine and schema change
        publish(): gets the data published and stores the data into a cube
    All three methods have to return data in the format of Pandas DataFrame.
"""

"""
    This example will create two tables of data:
    - all_users: contains all users in the environment
    - admin_users: contains all users with names starting with "admin" or "Admin"

    The data is retrieved using the mstrio-py library, which is installed in the default runtime.
"""

import pandas as pd
from mstrio.connection import Connection
from mstrio.users_and_groups.user import User, list_users

# Those are three variables required for the script to work,
# none of which can be prompted: they need to be saved and will not be edited
# after saving the script
URL = $base_url
USER = $username
PASS = $password


conn = Connection(base_url=URL, username=USER, password=PASS)


# This is just a helper method which converts raw data gathered by this script
# into a Pandas DataFrame, which is required by the datasource script workflow
def users2dataframe(users: list[User]) -> pd.DataFrame:
    """Convert a list of User objects to a Pandas DataFrame."""
    data = [
        {
            "id": str(user.id),
            "name": str(user.name),
            "enabled": '1' if user.enabled else '0'
        } for user in users
    ]
    return pd.DataFrame(data)


def get_admin_users(max_count = None) -> pd.DataFrame:
    """Retrieve admin users from the environment."""
    users = (
        list_users(conn, name_begins="admin", limit=max_count)
        + list_users(conn, name_begins="Admin", limit=max_count)
    )
    return users2dataframe(users)


def get_all_users(max_count = None) -> pd.DataFrame:
    """Retrieve all users from the environment."""
    users = list_users(conn, limit=max_count)
    return users2dataframe(users)


# Everything above are only helper methods and actions to retrieve data.
# Below are methods required specifically by the datasource script workflow.
def browse():
    """Retrieve the catalog information.

    Returns:
        a python dictionary where:
        - keys are the names of the tables in final datasource
        - values are the Pandas DataFrame objects with data for each table.

    Note:
        The values should retrieve as little amount of data as possible,
        just enough to show the structure of the data, in order to work performantly.
    """
    return { 'all_users': get_all_users(1), 'admin_users': get_admin_users(1) }


def preview(table_name, row_count):
    """Get partial data for preview, data refine and schema change.

    Args:
        table_name: name of the selected table. This will be provided to this script
            by UI when DataSource Script will be used in for example Report or Transaction Dashboard.
        row_count: number of rows to be retrieved. This will be provided to this script
            by UI when DataSource Script will be used in for example Report or Transaction Dashboard.

    Returns:
        a Pandas DataFrame object with `row_count` amount of rows.
    """
    if table_name == 'admin_users':
        return get_admin_users(row_count)
    if table_name == 'all_users':
        return get_all_users(row_count)
    return None


def publish(table_name):
    """Get the data published and store the data into the cube.

    Args:
        table_name: name of the selected table. This will be provided to this script
            by UI when DataSource Script will be used in for example Report or Transaction Dashboard.

    Returns:
        a Pandas DataFrame object with all data.
    """
    if table_name == 'admin_users':
        return get_admin_users()
    if table_name == 'all_users':
        return get_all_users()
    return None
