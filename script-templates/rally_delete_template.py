"""
    This example is for a dashboard user to modify data in a Rally workspace using
    a modern grid configured with transaction functions. The workflow will rely on this
    script to make actual modifications (delete) in the defect.
"""

"""
    The properties available for modification in the defect are `Name`, `Description`,
    `Priority`, `Owner`, `Iteration`, `TargetDate`, `State` and `PlanEstimate`. Only
    the `Name` property is required. Property  `FormattedID` cannot be modified.

    To connect with Rally API we use the library 'pyral'. Python library to handle Rally
    connection is not installed on the environment by default so it is necessary
    to choose runtime which have such library installed in the settings of the script.
    Additionally it is necessary to specify correct 'Network Access' to allow script
    to communicate with some other IP then IP of the environment.
"""

from pyral import Rally, restapi
from datetime import datetime

# Helper method to return datetime object in correct format for Rally operations
def parse_date_time_value(dateValue):
    # somehow it will be converted to this datetime format
    #   "%Y-%m-%d %H:%M:%S.%f" -> 2023-04-01 00:00:00.000
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S.%f",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    parsed_datetime = None
    for date_format in date_formats:
        try:
            parsed_datetime = datetime.strptime(dateValue, date_format)
            break
        except Exception:
            pass

    if parsed_datetime is None:
        raise Exception("Wrong Type of the datetime input value conversion!!!!")
    else:
        print(parsed_datetime)
        return parsed_datetime

try:
    # create connection to Rally. If you want to use other way then providing
    # api key please check documentation of this method. When providing secret keys like
    # `api_key` or any other sensitive data it is good to use variable of type `secret`.
    rally = Rally(
        server=$rally_server,
        apikey=$api_key,
        workspace=$workspace,
        project=$project,
    )

    # deal with the every row data via prepared statements
    # we assume that the logic of passing data from dashboard works correctly and each
    # transactional column is either the array of length which is equal to number
    # of rows passed from dashboard or `None`.
    for index in range(len($formatted_id)):
        # DELETE RALLY DEFECT
        tmp_formatted_id = $formatted_id[index]
        # first it is necessary to find object which will be deleted
        defect = rally.get(
            "Defect",
            fetch=True,
            query=f"FormattedID = {tmp_formatted_id}",
            projectScopeDown=True,
        ).next()

        rally.delete('Defect', defect.ObjectID)

except restapi.RallyRESTAPIError as error:
    raise Exception(f"Error has occurred: {error}")
# this error is raised from `rally.get` when the object was not found and we are trying
# to iterate with `next` method
except StopIteration as error:
    raise Exception(f"Error while iterating has occurred: {error}")
