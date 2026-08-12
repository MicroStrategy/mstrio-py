"""This is the demo script to show how to work with Planned Tasks module
in Strategy.

This script showcases Task listing, creation, property access,
alteration, execution, and deletion. It will not work without
replacing parameters with real values. Its goal is to present what
can be done with this module and to ease its usage.

This file is a collection of examples and is not intended to be run as a single
end-to-end script without adjustments. Some snippets require existing objects,
and multiple Task.create() examples may conflict if they use the same project,
schedule, script, user, and variable answers.

"""

from datetime import date

from mstrio.connection import get_connection
from mstrio.distribution_services.schedule.schedule_time import UnixTimeZone
from mstrio.python_execution.script import (
    Script,
    ScriptExecutionError,
    VariableAnswer,
)
from mstrio.python_execution.task import (
    ActiveState,
    LastRunData,
    Task,
    list_tasks,
)

# Define variables used by the snippets below:
# - PROJECT_NAME is required for connection and all task operations.
# - SCHEDULE_ID is required for schedule filtering, task creation, and
#   schedule-specific lookup.
# - SCHEDULE_NAME is required only for lookup by task name and schedule name.
# - SCRIPT_ID is required for script filtering, task creation, and task script
#   alteration.
# - SCRIPT_NAME is an optional reference if adapting snippets to resolve scripts
#   by name.
# - TASK_ID is required only for snippets that load an existing task by ID.
# - TASK_NAME is required for name filtering and lookup by task name.
# The required variables are those present in the snippets you plan to run.
PROJECT_NAME = $project_name
SCHEDULE_ID = $schedule_id
SCHEDULE_NAME = $schedule_name
SCRIPT_ID = $script_id
SCRIPT_NAME = $script_name
TASK_ID = $task_id
TASK_NAME = $task_name

# Create connection based on connection data
conn = get_connection(connectionData, project_name=PROJECT_NAME)

# --- Listing Tasks ---
# List all tasks for the current project
all_tasks = list_tasks(connection=conn)

# List tasks as dictionaries instead of objects
tasks_as_dicts = list_tasks(connection=conn, to_dictionary=True)

# List tasks filtered by a specific schedule
tasks_for_schedule = list_tasks(connection=conn, schedule=SCHEDULE_ID)

# List tasks with name filter
tasks_by_name = list_tasks(connection=conn, name=TASK_NAME)

# List tasks filtered by script
tasks_by_script = list_tasks(connection=conn, script=SCRIPT_ID)

# List tasks with a limit
limited_tasks = list_tasks(connection=conn, limit=10)

# --- Initializing a Task ---
# Get a task by ID and schedule
task = Task(connection=conn, schedule=SCHEDULE_ID, id=TASK_ID)

# Get a task by name and schedule
task = Task(connection=conn, schedule=SCHEDULE_NAME, name=TASK_NAME)

# Get a task by ID without specifying schedule (searches all schedules)
# [Note]: This only works if the task ID is unique across all schedules
task = Task(connection=conn, id=TASK_ID)

# Last run information
print(f"Last run: {task.last_run}")
if task.last_run:
    print(f"  Status: {task.last_run.status}")
    print(f"  Time triggered: {task.last_run.time_triggered}")
    print(f"  Time finished: {task.last_run.time_finished}")
    print(f"  Message: {task.last_run.message}")
    print(f"  Trigger user: {task.last_run.trigger_user}")
    print(f"  Node: {task.last_run.node}")

# List all properties
properties = task.list_properties()
print(properties)

# Convert to dictionary
task_dict = task.to_dict()
print(task_dict)

# --- Creating a Task ---
# Create a simple task
new_task = Task.create(
    connection=conn,
    name='MyPlannedTask',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
)

# Create a task that starts inactive
inactive_task = Task.create(
    connection=conn,
    name='InactiveTask',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
    active=False,
)

# Create a task with an expiration date
expiring_task = Task.create(
    connection=conn,
    name='ExpiringTask',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
    expiration=date(2027, 12, 31),  # or cia string: "2027-12-31"
    expiration_time_zone=UnixTimeZone.GMT,
)

# Create a task with variable answers for a prompted script
task_with_answers = Task.create(
    connection=conn,
    name='TaskWithAnswers',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
    variables_answers={
        'my_variable': 'answer_value',
    },
)

# Create a task with variable answers using VariableAnswer class
task_with_answers = Task.create(
    connection=conn,
    name='TaskWithAnswers',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
    variables_answers=[
        VariableAnswer.For('my_variable').should_be('answer_value'),
        VariableAnswer.For('other_var').should_be_global_default,
    ],
)

# Create a task and immediately trigger its execution
task_executed = Task.create(
    connection=conn,
    name='ImmediateTask',
    schedule=SCHEDULE_ID,
    script=SCRIPT_ID,
    execute_on_creation=True,
)

# --- Altering a Task ---
# Change the task name
task.alter(name='UpdatedTaskName')

# Change the active state
task.alter(active=ActiveState.INACTIVE)
task.alter(active=True)  # also accepts bool

# Change the script the task executes
task.alter(script=SCRIPT_ID)

# Change the script and provide new variable answers
task.alter(
    script=SCRIPT_ID,
    variables_answers={'my_variable': 'new_answer'},
)

# Change the schedule
task.alter(schedule=SCHEDULE_ID)

# Set an expiration date
task.alter(
    expiration=date(2027, 6, 30),
    expiration_time_zone=UnixTimeZone.EET,
)

# Remove expiration data
task.alter(remove_expiration_data=True)

# --- Activating and Deactivating ---
# Activate a task
task.activate()

# Activate a task and set expiration at the same time
task.activate(
    expiration=date(2027, 12, 31),
    expiration_time_zone=UnixTimeZone.GMT,
)

# Activate and remove expiration data
task.activate(remove_expiration_data=True)

# Deactivate a task
task.deactivate()

# Check active state
print(f"Is active: {task.is_active()}")

# --- Executing a Task ---
# Execute a task asynchronously (fire and forget)
task.execute()

# Execute a task and wait for completion
last_run = task.execute(block_until_done=True)
print(f"Execution status: {last_run.status}")
print(f"Output message / stdout: {last_run.message}")

# Execute and raise an exception on failure
try:
    last_run = task.execute(
        block_until_done=True,
        raise_on_execution_failure=True,
    )
except ScriptExecutionError as err:
    print(f"Task execution failed: {err}")

# --- Waiting for Execution ---
# Trigger execution and wait separately
task.execute()
last_run = task.wait_for_execution_finish()
print(f"Final status: {last_run.status}")

# Wait with a custom polling interval (in seconds)
task.execute(block_until_done=False)
last_run = task.wait_for_execution_finish(interval=20)

# --- Deleting a Task ---
# Delete with confirmation prompt
task.delete()

# Delete without confirmation prompt
task.delete(force=True)
