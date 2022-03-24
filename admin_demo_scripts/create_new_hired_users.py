from typing import List

from mstrio.connection import Connection
from mstrio.users_and_groups import User
from mstrio.utils.helper import exception_handler

from .scripts_helper import get_result_from_db, get_user_group


def _create_new_user_account(connection: "Connection", emp_username: str, emp_fullname: str,
                             add_to_user_groups: str) -> None:
    # when user is created it is automatically added to user group "Everyone"
    # and is granted rights to Browse and Read this user group
    new_user = User.create(connection=connection, username=emp_username, full_name=emp_fullname,
                           trust_id=emp_username)

    # add user to user groups with provided names (during creation it is added to "Everyone"  # noqa
    for user_group_name in add_to_user_groups:
        user_group_ = get_user_group(connection=connection, name=user_group_name)
        if user_group_:
            user_group_.add_users(users=new_user)


def create_new_hired_users(connection: "Connection", driver: str, server: str, database: str,
                           uid: str, pwd: str, query: str, db_lib: str, emp_username_col: str,
                           emp_fullname_col: str, emp_title_col: str, emp_id_col: str,
                           add_to_user_groups: List[str] = []) -> List[dict]:
    """Create user account for each new hired employee. It is necessary to
    provide all parameters to connect to database and proper query to retrieve
    information about new hired employees.

    Args:
        connection: MicroStrategy connection object returned by
                `connection.Connection()`
        driver (str): name of driver used to connect with database
        server (str): name of the server on which database is running
        database (str): name of the database
        uid (str): username of the user in the database
        pwd (str): password of the user in the database
        query (str): SELECT query to execute in database
        db_lib (str): name of the Python library which will be used to connect
            with database
        emp_username_col (str): Name of the column with employee's username
            in database query
        emp_fullname_col (str): Name of the column with employee's fullname
            in database query
        emp_title_col (str): Name of the column with employee's title
            in database query
        emp_id_col (str): Name of the column with employee's id
            in database query
        add_to_user_groups (list of str): Names of user groups to which each
            newly created user will be added. Default value is an empty list.
            It is worth to that during creation of user it is added to
            user group "Everyone".

        Returns:
            table with information of each new employee's creation status
            and its basic details.
    """
    try:
        # connect to database and execute query to retrieve required
        # information about employees
        new_employees = get_result_from_db(driver=driver, server=server, database=database,
                                           uid=uid, pwd=pwd, query=query, db_lib=db_lib)
    except Exception as e:
        msg = f"There was an error while retrieving new employees from database: {e}"
        exception_handler(msg, UserWarning)

    # check if names of columns with data needed to create user were retrieved
    # from database
    if not all(x in new_employees.columns
               for x in [emp_username_col, emp_fullname_col, emp_title_col, emp_id_col]):
        msg = f"Not all of columns {emp_username_col}, {emp_fullname_col}, {emp_title_col}"
        msg += f" and {emp_id_col} are in data retrieved from database."
        exception_handler(msg, UserWarning)

    # iterate through each row retrieved from database
    # and try to create a new user
    results = []
    for _, row in new_employees.iterrows():
        emp_username = row[emp_username_col]
        emp_fullname = row[emp_fullname_col]
        emp_title = row[emp_title_col]
        emp_id = row[emp_id_col]
        result = {'emp_id': emp_id, 'emp_name': emp_fullname, 'emp_title': emp_title}
        try:
            _create_new_user_account(connection, emp_username, emp_fullname, add_to_user_groups)
            result['account_created'] = True
        except Exception as e:
            msg = f"User with username: {emp_username} and full name: {emp_fullname}"
            msg += f" was not fully created: {e}"
            exception_handler(msg, UserWarning)
            result['account_created'] = False
        finally:
            results.append(result)

    return results
