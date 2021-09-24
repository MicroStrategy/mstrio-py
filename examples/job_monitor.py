"""This is the demo script to show how administrator can monitor and manage jobs

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.

Note: Some functionality is missing when working with 11.3.2 I-Server
    versions. To use all functionality 11.3.3 and up will be required.
    There are also some differences between 11.3.2 and 11.3.3+ Job
    attributes values.
"""

from mstrio import connection
from mstrio.connection import Connection
from mstrio.server.project import Project
from mstrio.server.job_monitor import (Job, JobStatus, JobType, kill_all_jobs, kill_jobs,
                                       list_jobs, ObjectType, PUName)
from mstrio.users_and_groups.user import User

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, login_mode=1)

# get project by name
project = Project(connection=conn, name="MicroStrategy Tutorial")
# get user by name
john = User(connection=conn, name="John Smith")

# instanstiate an existing job using constructor
job = Job(conn, id="55AA293811EAE2F2EC7D0080EF25A593")  # example job ID
# get properties for the first job on the list
job.list_properties()
# kill the job
job.kill()

# get list of `Job` objects for all jobs on the environment
jobs = list_jobs(conn)

# get list of dicts representing job information for all jobs on the environment
jobs = list_jobs(conn, to_dictionary=True)

# get a list of `Job` objects filtered by job status, project and object type
list_jobs(conn, status=JobStatus.LOADING_PROMPT, project=project, object_type=ObjectType.CUBE)

# get a list of `Job` objects filtered by job type and job owner
list_jobs(conn, type=JobType.INTERACTIVE, user=john)

# get a list of `Job` objects filtered by elapsed time and memory usage
# NOTE: memory_usage filter works for 11.3.3+ I-Server versions
slow_jobs = list_jobs(conn, elapsed_time="gt:10000", memory_usage="gt:500")

# kill jobs by passing either Job objects or ids
result = kill_jobs(conn, slow_jobs)
# kill_jobs return Success, PartialSuccess or MSTRException, you can check which
# jobs were killed and which were not, and why in case of PartialScucess
result.succeeded
result.failed
# you can easily evaluate if all passed jobs were killed using bool() evaluation
# on result, which will return True if result is Success and False if result
# is PartialSuccess
succesfully_killed_passed_jobs = bool(result)
if result:
    print("Successfuly killed jobs.")
    # perform other automation actions

# kill jobs running over 5 hours
time_hours = 5
elapsed_t = time_hours * 60**2  # convert to seconds (for 11.3.2 I-Server version)
if connection.iserver_version >= '11.3.0300':
    elapsed_t = 1000 * elapsed_t  # convert to milliseconds (for 11.3.3+ I-Server versions)
elapsed_t = f'gt:{elapsed_t}'  # correct form filter (valid operators: 'gt:' and 'lt:')
kill_all_jobs(conn, elapsed_time=elapsed_t, force=True)

# kill filtered jobs similarly to list_jobs() using single function
result = kill_all_jobs(conn, pu_name=PUName.SQL_ENGINE, memory_usage="gt:800")
# like kill_jobs, kill_all_jobs return Success, PartialSuccess or MSTRException
result.succeeded
