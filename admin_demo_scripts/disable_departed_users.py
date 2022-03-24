from typing import List, Union

from mstrio.connection import Connection
from mstrio.users_and_groups import User
from mstrio.utils.helper import exception_handler

from .scripts_helper import get_result_from_db, get_user_group


def _disable_user_account(connection: "Connection", username: str) -> None:
    # find user with a given username
    u = User(connection=connection, username=username)
    # remove this user from all user groups (it will not be removed from
    # user group "Everyone" because of the implementation of I-Server
    u.remove_from_all_user_groups()
    # add this user to user groups 'Inactive Users' when such group exists
    inactive_users_ug = get_user_group(connection=connection, name="Inactive Users")
    if inactive_users_ug:
        u.add_to_user_groups(user_groups=inactive_users_ug)
    # disable user
    u.alter(enabled=False)


def disable_departed_users(connection: "Connection", driver: str, server: str, database: str,
                           uid: str, pwd: str, query: str, db_lib: str, emp_username_col: str,
                           emp_id_col: str) -> Union[List[dict], None]:
    """Disable user account for each departed employee. User will be removed
    from all user groups to which it belongs (except from "Everyone" because
    of the way I-Server works) and added to user group "Inactive Users" (only
    when it exists).

    It is necessary to provide all parameters to connect to database and proper
    query to retrieve information about departed employees.

    Args:
        connection: MicroStrategy connection object returned by
                `connection.Connection()`
        driver (str): name of driver used to connect with database
        server (str): name of the server on which database is running
        database (str): name of the database
        uid (str): username of the user in the database
        pwd (str): password of the user in the database
        query (str): SELECT query to execute in database
        db_lib (str): name of the Python library which will be used
            to connect with database
        emp_username_col (str): Name of the column with user's username
            in database query
        emp_id_col (str): Name of the column with user's id
            in database query

    Returns:
        table with information of each new employee's disabling status
        and its basic details or None in case of some problem with database
        operations.
    """

    try:
        # connect to database and execute query to retrieve required
        # information about employees
        departed_employees = get_result_from_db(driver=driver, server=server, database=database,
                                                uid=uid, pwd=pwd, query=query, db_lib=db_lib)
    except Exception as e:
        msg = f"There was an error while retrieving departed employees from database: {e}"
        exception_handler(msg, UserWarning)
        return

    # check if names of columns with data needed to create user
    # were retrieved from database
    if not all(x in departed_employees.columns for x in [emp_username_col, emp_id_col]):
        msg = f"Not all of columns {emp_username_col} and {emp_id_col}"
        msg += f" {emp_id_col} are in data retrieved from database."
        msg = f"Column {emp_username_col} not in data retrieved from database."
        exception_handler(msg, UserWarning)
        return

    results = []
    for _, row in departed_employees.iterrows():
        username = row[emp_username_col]
        emp_id = row[emp_id_col]
        result = {'emp_id': emp_id, 'emp_username': username}
        try:
            _disable_user_account(connection, username)
            result['disabled'] = True
        except Exception as e:
            msg = f"User with username: {username} was not fully disabled: {e}"
            exception_handler(msg, UserWarning)
            result['disabled'] = False
        finally:
            results.append(result)

    return results
