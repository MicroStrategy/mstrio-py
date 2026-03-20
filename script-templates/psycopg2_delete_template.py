"""
    This example is for a dashboard user to modify data in a PostgreSQL DB table using
    a modern grid configured with transaction functions. The workflow will rely on this
    script to make actual modifications (delete) in the table.
"""

"""
    The table named USERS has 5 columns USER_ID(Int), USER_LOGIN(Varchar),
    HIRED_DATE(Date), EMAIL(VarChar) and MODIFIED_BY(VarChar), with USER_ID as
    the primary. Data changes for HIRED_DATE(Date), EMAIL(VarChar)
    and MODIFIED_BY(VarChar) are optional.

    In this template we use the library 'psycopg2' (installed in runtime as
    'psycopg2-binary') to connect with the PostgreSQL database, submit atomic requests
    and execute operations. For using other types of database, make sure to use
    their methods correctly.

    Python libraries to handle SQL connections are not installed on the environment by
    default so it is necessary to choose runtime which have such library installed in
    the settings of the script. Additionally it is necessary to specify correct `Network
    Access` to allow script to communicate with some other IP then IP of the
    environment.
"""

import psycopg2
import datetime


try:
    # create connection to database. If you want to use other way then providing
    # user and password please check documentation of this method. When providing
    # passwords or any other sensitive data it is good to use variable of type `secret`.
    connection = None
    connection = psycopg2.connect(
        host=$host,
        port=$port,
        database=$database,
        user=$user_name,
        password=$user_password
    )

    # Prepare parameterized query for select the existing row to delete
    sql_delete_query = """DELETE FROM USERS WHERE USER_ID = %s"""

    # create cursor to execute operations on database
    cursor = connection.cursor()

    # deal with the every row data via prepared statements
    # we assume that the logic of passing data from dashboard works correctly and each
    # transactional column is either the array of length which is equal to number
    # of rows passed from dashboard
    for index in range(len($user_id)):
        # case with DELETE query is the easiest one because we are deleting
        # just based on `USER_ID`
        cursor.execute(sql_delete_query, tuple([int($user_id[index])]))

    # commit all changes when there weren't any errors
    connection.commit()

# error handling
except psycopg2.Error as e:
    # in case of any error we have to rollback all of the changes which
    # has been made on database
    if connection:
        connection.rollback()
    print("Error:", e)

finally:
    # close the database connection
    if connection:
        connection.close()
