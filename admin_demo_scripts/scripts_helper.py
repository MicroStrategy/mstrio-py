import pandas as pd

from mstrio.users_and_groups import UserGroup


def get_result_from_db(driver: str, server: str, database: str, uid: str, pwd: str, query: str,
                       db_lib: str) -> pd.DataFrame:
    """Connect to database and execute the SELECT query. You need to have
    installed on your machine the library to connect with database as well as
    driver to connect with database.

    Args:
        driver (str): name of driver used to connect with database
        server (str): name of the server on which database is running
        database (str): name of the database
        uid (str): username of the user in the database
        pwd (str): password of the user in the database
        query (str): SELECT query to execute in database
        db_lib (str): name of the Python library which will be used
            to connect with database

    Returns:
        Pandas dataframe with the data retrieved from database.

    Raise:
        ValueError when query doesn't start with `SELECT` statement
    """

    # import library to get connection with database
    eval("exec('import " + db_lib + "')")

    # prepare string which is used to connect to database
    driver = 'DRIVER=' + driver
    server = 'SERVER=' + server
    database = 'DATABASE=' + database
    uid = 'UID=' + uid
    pwd = 'PWD=' + pwd
    connection_string = ';'.join([driver, server, database, uid, pwd])

    if not query[0:6].lower() == 'select':
        msg = 'When getting result from database the query should start with `SELECT` statement'
        raise ValueError(msg)

    # connect to database, execute query and return result as dataframe
    with eval(db_lib).connect(connection_string) as db_conn:
        return pd.read_sql(query, db_conn)


def get_user_group(connection, name):
    try:
        user_group_ = UserGroup(connection=connection, name=name)
    except Exception:
        user_group_ = None
    return user_group_
