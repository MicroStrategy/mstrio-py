"""
    This example is for a dashboard user to modify data in a Rally workspace using
    a modern grid configured with transaction functions. The workflow will rely on this
    script to make actual modifications (update) in the defect.
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
        # UPDATE RALLY DEFECT
        tmp_formatted_id = $formatted_id[index]
        # first it is necessary to find object which will be modified
        defect = response_de = rally.get(
            "Defect",
            fetch=True,
            query=f"FormattedID = {tmp_formatted_id}",
            projectScopeDown=True,
        ).next()
        update_data = {"ObjectID": defect.ObjectID}
        if $defect_name and $defect_name[index]:
            update_data["Name"] = $defect_name[index]
        if $description:  # Value for description can be None
            update_data["Description"] = $description[index]
        # Valid 'Priority' values are [ Low, Normal, High Attention,
        # Resolve Immediately, None ]
        if $priority:
            update_data["Priority"] = $priority[index]
        # Value for owner can be None or existing owner username
        if $owner:
            owner = None
            # inside defect owner has to be stored as a reference to the actual user
            # value passed from dashboard is used to find this reference
            if $owner[index]:
                owner_username = $owner[index]
                owner = rally.get(
                    "User", fetch=True, query=f"UserName = {owner_username}"
                ).next().ref
            update_data["Owner"] = owner
        # Value for iteration can be None or existing iteration name
        if $iteration:
            iteration = None
            if $iteration[index]:
                tmp_iteration_name = $iteration[index]
                iteration = rally.get(
                    "Iteration", fetch=True, query=f'Name = "{tmp_iteration_name}"'
                ).next().ref
            update_data["Iteration"] = iteration
        if $target_date:
            target_date = (
                None
                if $target_date[index] is None
                else parse_date_time_value($target_date[index]).isoformat()
            )
            update_data["TargetDate"] = target_date
        # Valid 'State' values are: [ Submitted, Closed, Deferred, Open ]
        if $state and $state[index]:
            update_data["State"] = $state[index]
        if $plan_estimate:  # Value for 'Plan Estimate' can be None
            update_data["PlanEstimate"] = $plan_estimate[index]

        rally.update("Defect", update_data)
        
except restapi.RallyRESTAPIError as error:
    raise Exception(f"Error has occurred: {error}")
# this error is raised from `rally.get` when the object was not found and we are trying
# to iterate with `next` method
except StopIteration as error:
    raise Exception(f"Error while iterating has occurred: {error}")
