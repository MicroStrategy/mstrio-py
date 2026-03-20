"""
    This example is for a dashboard user to modify data in a PostgreSQL DB table using
    a modern grid configured with transaction functions. The workflow will rely on this
    script to make actual modifications (insert, update or delete) in the table.
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


# helper method to handle not adding None values to the query
def append_not_none_value(array, value):
    if value is not None:
        array.append(value)
        return True
    return False

# Helper method to return datetime object in correct format for SQL operations
def parseDateTimeValue(dateValue):
    # somehow it will be converted to this datetime format
    #   "%Y-%m-%d %H:%M:%S.%f" -> 2023-04-01 00:00:00.000,
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%d-%m %H:%M:%S",
        "%m/%d/%Y %H:%M:%S.%f",
        "%m-%d-%Y"
    ]
    parsed_datetime = None
    for date_format in date_formats:
        try:
            parsed_datetime = datetime.datetime.strptime(dateValue, date_format)
            break
        except:
            pass

    if (parsed_datetime == None):
        raise Exception("Wrong Type of the datetime input value conversion!!!!")
    else:
        return parsed_datetime


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

    # Prepare queries for database operations. Due to the fact that for some rows
    # we might want to pass `None` value we need some additional logic. This logic
    # require to create query during the time of reading passed properties.

    # Parameterized query for insert new row
    # We assume that we must pass `USER_ID` and `USER_LOGIN` when inserting
    # and the other properties are optional.
    tmp_sql_insert_query = """
        INSERT INTO USERS (
            USER_ID,
            USER_LOGIN
    """

    # Parameterized query for edit the existing row
    # We assume that when updating we must pass only `USER_LOGIN` and the other
    # properties are optional. Update is done based on `USER_ID` and `WHERE` clause
    # is added in the end of preparing query for each row
    tmp_sql_update_query = """
        UPDATE USERS SET USER_LOGIN = %s
    """

    # Parameterized query for select the existing row to delete
    sql_delete_query = """DELETE FROM USERS WHERE USER_ID = %s"""

    # create cursor to execute operations on database
    cursor = connection.cursor()

    # deal with the every row data via prepared statements
    # we assume that the logic of passing data from dashboard works correctly and each
    # transactional column is either the array of length which is equal to number
    # of rows passed from dashboard or `None`. Values for `txn_actions` are calculated
    # by dashboard logic and they are based on the action which was created on
    # particular row.
    for index in range(len($txn_actions)):
        if $txn_actions[index] == "insert":
            # when value is optional and not provided, then don't add it to insert query
            optional_values_array = []
            optional_values_in_insert_query = ''
            # this value depends on number of the properties in initial INSERT query
            # it is equal to the number of properties there
            i = 2
            # when array with values for each property is not `None` and the value
            # for particular row is not `None` then we add it
            if $hired_date and $hired_date[index]:
                optional_values_array.append(parseDateTimeValue($hired_date[index]))
                optional_values_in_insert_query += f",HIRED_DATE"
                i = i + 1
            if $email and append_not_none_value(optional_values_array, $email[index]):
                optional_values_in_insert_query += f",EMAIL"
                i = i + 1
            # `modified_by` is a standard variable of type `system_prompt` so its value
            # is calculated based on the chosen System Prompt
            if append_not_none_value(optional_values_array, $modified_by):
                optional_values_in_insert_query += f",MODIFIED_BY"
                i = i + 1

            # create list of parameters
            query_parameters = ",".join(list(map(lambda x: "%s", list(range(i)))))
            optional_values_in_insert_query += f") VALUES ({query_parameters})"

            sql_insert_tuple = (
                int($user_id[index]),
                $user_login[index],
            ) + tuple(optional_values_array)
            # final INSERT query is created based on initial INSERT query and the part
            # created for particular row based on properties passed for this row
            sql_insert_query = tmp_sql_insert_query + optional_values_in_insert_query

            # execute insert query
            cursor.execute(sql_insert_query, sql_insert_tuple)

        elif $txn_actions[index] == "update":
            optional_values_array = []
            optional_values_in_update_query = ''
            # when array with values for each property is not `None` and the value
            # for particular row is not `None` then we add it
            if $hired_date and $hired_date[index]:
                optional_values_array.append(parseDateTimeValue($hired_date[index]))
                optional_values_in_update_query += f",HIRED_DATE = %s"
            if $email and append_not_none_value(optional_values_array, $email[index]):
                optional_values_in_update_query += f",EMAIL = %s"
            # `modified_by` is a standard variable of type `system_prompt` so its value
            # is calculated based on the chosen System Prompt
            if append_not_none_value(optional_values_array, $modified_by):
                optional_values_in_update_query += f",MODIFIED_BY = %s"

            # final UPDATE query is created based on initial UPDATE query and the part
            # created for particular row based on properties passed for this row
            # after adding optional properties we need to add `WHERE` clause
            # which in this case is based on `USER_ID`
            optional_values_array.append(int($user_id[index]))
            optional_values_in_update_query += f" WHERE USER_ID = %s"

            sql_update_tuple = (
                $user_login[index],
            ) + tuple(optional_values_array)
            sql_update_query = tmp_sql_update_query + optional_values_in_update_query
            # execute update query
            cursor.execute(sql_update_query, sql_update_tuple)

        elif $txn_actions[index] == "select":
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
