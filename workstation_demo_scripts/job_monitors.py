from mstrio.connection import get_connection

from mstrio.server.job_monitor import (Job, JobStatus, JobType, kill_all_jobs, kill_jobs,
                                       list_jobs, ObjectType, PUName)
from mstrio.server.project import Project
from mstrio.users_and_groups.user import User

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData)

# get project by name
project = Project(connection=conn, name="MicroStrategy Tutorial")
# get user by name
admin = User(connection=conn, name="Administrator")

# get list of `Job` objects for all jobs on the environment
jobs = list_jobs(conn)
print('All jobs on the environment as objects')
print(jobs)

if jobs:
    # instanstiate an existing job using constructor
    job = Job(conn, id=jobs[0].id)  # example job ID
    # get properties for the first job on the list
    props = job.list_properties()
    print('Propertties of a given job')
    print(props)
    # kill the job
    job.kill()

# get list of dicts representing job information for all jobs on the environment
jobs = list_jobs(conn, to_dictionary=True)
print('All jobs on the environment as dictionaries')
print(jobs)

# get a list of `Job` objects filtered by job status, project and object type
jobs = list_jobs(conn, status=JobStatus.LOADING_PROMPT, project=project,
                 object_type=ObjectType.CUBE)
print("All jobs filtered by 'LOADINIG_PROMPT' status, project and 'CUBE' type")
print(jobs)

# get a list of `Job` objects filtered by job type and job owner
jobs = list_jobs(conn, type=JobType.INTERACTIVE, user=admin)
print("All jobs filtered by 'INTERACTIVE' type and 'Administrator' user")
print(jobs)

# get a list of `Job` objects filtered by elapsed time and memory usage
# NOTE: memory_usage filter works for 11.3.3+ I-Server versions
slow_jobs = list_jobs(conn, elapsed_time="gt:10000", memory_usage="gt:500")
print("List of job objects filtered by elapsed time and memory usage")
print(slow_jobs)

if slow_jobs:
    # kill jobs by passing either Job objects or ids
    result = kill_jobs(conn, slow_jobs)
    # kill_jobs return Success, PartialSuccess or MSTRException, you can check
    # which jobs were killed and which were not, and why in case of
    # PartialScucess
    print("killed jobs")
    print(result.succeeded)
    print("not killed jobs")
    print(result.failed)

# kill jobs running over 5 hours
time_hours = 5
elapsed_t = time_hours * 60**2  # convert to seconds (for 11.3.2 I-Server version)
if conn.iserver_version == '11.3.0200':
    elapsed_t = 1000 * elapsed_t  # convert to milliseconds (for 11.3.3+ I-Server versions)
elapsed_t = f'gt:{elapsed_t}'  # correct form filter (valid operators: 'gt:' and 'lt:')
try:
    kill_all_jobs(conn, elapsed_time=elapsed_t, force=True)
except ValueError as e:
    print(e)

# kill filtered jobs similarly to list_jobs() using single function
try:
    result = kill_all_jobs(conn, pu_name=PUName.SQL_ENGINE, memory_usage="gt:800")
    # you can easily evaluate if all passed jobs were killed using bool()
    # evaluation on result, which will return True if result is Success and
    # False if result is PartialSuccess
    print("Result of killing jobs:")
    print(bool(result))
except ValueError as e:
    print(e)
