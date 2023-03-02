"""This is the demo script to show how administrator can monitor and manage jobs

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.

Note: Some functionality is missing when working with 11.3.2 I-Server
    versions. To use all functionality 11.3.3 and up will be required.
    There are also some differences between 11.3.2 and 11.3.3+ Job
    attributes values.
"""

from mstrio.server import (
    Job, JobStatus, JobType, kill_all_jobs, kill_jobs, list_jobs, ObjectType, PUName
)
from mstrio.server import Project
from mstrio.users_and_groups import User

from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# get project by name
project = Project(connection=conn, name=PROJECT_NAME)

# get list of `Job` objects for all jobs on the environment
jobs = list_jobs(conn)
print(jobs)

# get list of dicts representing job information for all jobs on the environment
jobs = list_jobs(conn, to_dictionary=True)
print(jobs)

# Define variables which can be later used in a script
JOB_ID = $job_id  # id for Job object lookup

# instantiate an existing job using constructor
job = Job(conn, id=JOB_ID)

# get properties for the first job on the list
job.list_properties()

# kill the job
job.kill()

# get a list of `Job` objects filtered by job status, project and object type
list_jobs(conn, status=JobStatus.LOADING_PROMPT, project=project, object_type=ObjectType.CUBE)
# see server/job_monitor.py for JobStatus and ObjectType values

# Define variables which can be later used in a script
USERNAME = $username  # name for User object lookup

# get user by name
john = User(connection=conn, name=USERNAME)

# get a list of `Job` objects filtered by job type and job owner
list_jobs(
    conn, type=JobType.INTERACTIVE, user=john
)  # see server/job_monitor.py for JobType values

# Define variables which can be later used in a script
LIST_JOBS_FILTER_TIME = $list_jobs_filter_time # for example 'gt:10000'
LIST_JOBS_FILTER_MEM = $list_jobs_filter_mem # for example 'gt:500'

# get a list of `Job` objects filtered by elapsed time and memory usage
# NOTE: memory_usage filter works for 11.3.3+ I-Server versions
slow_jobs = list_jobs(conn, elapsed_time=LIST_JOBS_FILTER_TIME, memory_usage=LIST_JOBS_FILTER_MEM)

# kill jobs by passing either Job objects or ids
result = kill_jobs(conn, slow_jobs)

# kill_jobs return Success, PartialSuccess or MSTRException, you can check which
# jobs were killed and which were not, and why in case of PartialSuccess
print(result.succeeded)
print(result.failed)

# you can easily evaluate if all passed jobs were killed using bool() evaluation
# on result, which will return True if result is Success and False if result
# is PartialSuccess
successfully_killed_passed_jobs = bool(result)
if result:
    print('Successfully killed jobs.')
    # perform other automation actions

# Define a variable which can be later used in a script
KILL_JOBS_FILTER_TIME = $kill_jobs_filter_time  # should be converted to seconds

# kill jobs running over a certain time
elapsed_t = KILL_JOBS_FILTER_TIME  # time in seconds (for 11.3.2 I-Server version)
if conn.iserver_version >= '11.3.0300':
    elapsed_t = 1000 * elapsed_t  # convert to milliseconds (for 11.3.3+ I-Server versions)
elapsed_t = f'gt:{elapsed_t}'  # correct form filter (valid operators: 'gt:' and 'lt:')
kill_all_jobs(conn, elapsed_time=elapsed_t, force=True)

# kill filtered jobs similarly to list_jobs() using single function
result = kill_all_jobs(conn, pu_name=PUName.SQL_ENGINE, memory_usage='gt:800')
# see server/job_monitor.py for PUName values

# like kill_jobs, kill_all_jobs return Success, PartialSuccess or MSTRException
print(result.succeeded)
