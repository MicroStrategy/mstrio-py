"""
Flow Step Template: PostgreSQL SQL query execution with DSN-less connection
Script Result Type: text

This workflow template requires:
- Custom Runtime with `psycopg2-binary` (min version 2.4.3) library preinstalled and
    network access to the target IP whitelisted
- Providing values for all required Variables

It represents PostgreSQL SQL query execution action.

The Script will return stringified affected rows from DB after SQL execution
if the requested query resulted in any, empty list otherwise.

Those are connection parameters:
`$dbname`: the database name
`$user`: user name used to authenticate
`$password`: password used to authenticate
`$host`: database host address
`$port`: connection port number (defaults to 5432 if not provided)

`$sql_query` can be any SQL statement. If `%s` is present in it (aka: parameter)
It can be provided via an entry in `$params`, which is a list of answers to all
`%s` parameters in `$sql_query`.

Examples:

>>> `$sql_query`=="SELECT * FROM Users"
>>> ---
>>> `$sql_query`=="UPDATE USERS SET USER_LOGIN = %s WHERE USER_ID = %s"
>>> `$params`==["New Login", "QWER1234"]

The workflow currently assumes:
- That the DB connection will be established via user + password
"""

import psycopg2


connection = None
results = None

try:
    connection = psycopg2.connect(
        host=$host,
        port=int($port) or 5432,
        dbname=$dbname,
        user=$user,
        password=$password,
    )

    cursor = connection.cursor()

    SQL = $sql_query
    PARAMS = $params or None

    if PARAMS and not isinstance(PARAMS, list):
        raise ValueError("PARAMS must be a list of strings.")

    cursor.execute(SQL, PARAMS)
    results = cursor.fetchall()
    connection.commit()

except psycopg2.Error as err:
    if connection:
        connection.rollback()

    raise RuntimeError("Could not perform requested query.") from err

finally:
    if connection:
        connection.close()


def get_results():
    return results or []
