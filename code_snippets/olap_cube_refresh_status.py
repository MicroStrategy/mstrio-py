"""This is the demo script meant to show how to control the refresh status of
OLAP cube.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from pprint import pprint
from time import sleep

from mstrio.connection import get_connection
from mstrio.helpers import IServerError
from mstrio.project_objects import OlapCube, list_olap_cubes
from mstrio.server import Job, JobStatus


def inform_when_job_done(job: Job, interval: int = 10):
    """Helper function to check the status of the job every `interval` seconds
    until it is completed. It will print the error message if the job is
    completed with error. This works only when called in short time max 20
    minutes after triggering the refresh."""
    stable_states = [JobStatus.COMPLETED, JobStatus.ERROR, JobStatus.STOPPED]
    try:
        while job.status not in stable_states:
            sleep(interval)
            job.fetch()
        print(f"Job is finished with error: {job.error_message}")
    except IServerError:
        print("Job is finished with success.")

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, project_name=PROJECT_NAME)


# List available OLAP cubes
cubes = list_olap_cubes(connection=conn)
# Print the list of available OLAP cubes
pprint(cubes)

# To get existing OLAP cube you need to know its ID
SELECTED_CUBE_ID = $selected_cube_id  # Insert ID of cube on which you want to perform actions
selected_cube = OlapCube(connection=conn, id=SELECTED_CUBE_ID)
# Print the last update time of the selected OLAP cube
before_last_update_time = selected_cube.last_update_time
print(before_last_update_time)
# Print the status of the selected OLAP cube
before_status = selected_cube.status
print(selected_cube.show_status())
# Refresh the selected OLAP cube
job = selected_cube.refresh()

# Now request for refresh was sent to the I-Server. It may take some time to
# complete the refresh. You can check the status of the job to see if it is
# completed or see if last update time has changed.

# Job can be taken from the job object or initialized with the job ID
JOB_ID = job.id
my_job = Job(connection=conn, id=JOB_ID)

# Here we will check the status of the job every 10 seconds until it is
# completed. You can adjust the time interval to your needs.

inform_when_job_done(job=my_job, interval=10)

# Another way to check job status is by calling refresh_status method on the job
# If the job can not be found on server when refreshing, the status will be
# updated to JobStatus.COMPLETED
my_job.refresh_status()

# Now you can check the last update time of the selected OLAP cube to see if
# the refresh was successful.
selected_cube.fetch()
after_last_update_time = selected_cube.last_update_time
print(after_last_update_time)
# Print the status of the selected OLAP cube
after_status = selected_cube.status
print(selected_cube.show_status())

# Other way to check if refresh is done is comparing last update time before
# and after refresh. If they are different, the refresh was successful.
if before_last_update_time != after_last_update_time:
    print("Refresh was successful.")
