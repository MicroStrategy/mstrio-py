"""This is the demo script to show how to work with Scripts and execute
Python code server-side in Strategy One.

This script showcases basic Code and Script management, execution, and
variable handling. It will not work without replacing parameters with
real values. Its goal is to present what can be done with this module
and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.python_execution.script import (
    Code,
    Script,
    ScriptEnvironmentError,
    ScriptError,
    ScriptExecutionError,
    ScriptSetupError,
    VariableType,
    list_scripts,
    VariableStandardScript,
    VariableDatasourceScript,
    VariableTransactionScript,
    VariableAnswer,
    ExecutionStatus,
    ScriptResultType,
    ScriptUsageType,
)
from pathlib import Path

# Define variables which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here
PROJECT_ID = $project_id  # Insert project ID here
SCRIPT_NAME = $script_name  # Insert name of the Script here
SCRIPT_ID = $script_id  # Insert ID of Script here
RUNTIME_ID = $runtime_id  # Insert ID of runtime here
FOLDER_ID = $folder_id  # Insert folder ID here

# Create connection based on workstation data
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# --- Code Execution ---
# Create a Code instance from a string
code = Code(conn, code="print('Hello from Strategy One')")  # will not validate the code
code = Code(conn, code="print('Hello from Strategy One')", validate_code=True)

# Load code from a file (with or without validation)
code = Code.get_from_file(conn, Path('./my_script.py'))  # will not validate the code
code = Code.get_from_file(conn, Path('./my_script.py'), validate_code=True)
# or path as string
code = Code.get_from_file(conn, './my_script.py', validate_code=True)

# Execute code synchronously and wait for completion
status = code.execute()
print(f"Execution status: {status}")

# Get execution console output
output = code.stdout
print(f"Output: {output}")

# Execute code asynchronously
code.execute(block_until_done=False)
print("Execution initiated.")

# Wait for asynchronous execution to finish
final_status = code.wait_for_execution_finish()
print(f"Final status: {final_status}")

# Get execution details
details = code.get_execution_details()
print(f"Execution details: {details}")

# Stop running code execution
code.execute(block_until_done=False)
code.stop_execution()
status = code.status
print(f"Code execution stopped: {status}")

# --- Code with Variables ---
# Create code that uses variables (denoted with $variable_name)
code_with_var = Code(
    conn,
    code="result = $input_value * 2\nprint(result)",
    validate_code=True,
)

# Execute code with variable values
status = code_with_var.execute(
    variables=[
        VariableStandardScript(
            'input_value', value=21, type=VariableType.NUMERICAL, prompt=False
        )
    ]
)

# Execute with interactive prompting for variables
status = code_with_var.execute(
    variables=[
        VariableStandardScript(
            'input_value', value=21, type=VariableType.NUMERICAL, prompt=True
        )
    ],
    answers={'input_value': '42'},
)

# Pipe logs to see execution output
status = code_with_var.execute(pipe_logs=True)

# Raise exception if code execution fails
try:
    code_which_errors = Code(conn, code="raise Exception('Error!')")
    status = code_which_errors.execute(raise_on_execution_failure=True)
except ScriptError as err:
    print(f"Code execution failed: {err}")

# Read properties of last execution status
print(code.stdout)  # When Code is successful, STDOUT of the Code
print(code.stderr)  # When Code is successful, STDERR of the Code
print(code.executor_message)  # When Code errored out during runtime, error details of why

# --- Script Management ---
# List all scripts in a project
all_scripts = list_scripts(
    connection=conn,
    project=PROJECT_ID,
    to_dictionary=False,
)

# List scripts with filtering
filtered_scripts = list_scripts(
    connection=conn,
    project=PROJECT_ID,
    name=SCRIPT_NAME,
    to_dictionary=False,
)

# Get script as dictionaries instead of objects
scripts_as_dicts = list_scripts(
    connection=conn,
    project=PROJECT_ID,
    to_dictionary=True,
)

# Get single script by ID
script = Script(connection=conn, id=SCRIPT_ID)

# Get single script by name
script = Script(connection=conn, name=SCRIPT_NAME)

# List script properties
properties = script.list_properties()
print(properties)

# --- Script Creation ---
# Create a simple script
new_script = Script.create(
    connection=conn,
    name='MyScript',
    runtime_id=RUNTIME_ID,
    code='print("Hello")',  # will not be validated
    destination_folder=FOLDER_ID,
)

# Create script with validation
new_script = Script.create(
    connection=conn,
    name='ValidatedScript',
    runtime_id=RUNTIME_ID,
    code='x = 42\nprint(x)',
    destination_folder=FOLDER_ID,
    validate_code=True,  # will validate code before creation
)

# Create script with variables
new_script_with_vars = Script.create(
    connection=conn,
    name='ScriptWithVariables',
    runtime_id=RUNTIME_ID,
    code='print($name)\nprint($age)',
    destination_folder=FOLDER_ID,
    variables=[
        # `VariableStandardScript` is by default prompted unless set otherwise
        VariableStandardScript('name', value='John'),
        VariableStandardScript('age', value=30, type=VariableType.NUMERICAL),
        VariableStandardScript('email'),
        VariableStandardScript('title', value='Junior', prompt=False),
        # [Note]: There are other variable-defining classes available, specific
        # to other script usage types. Please see their respective docstrings
        # for more details
    ],
    validate_code=True,
)

# Create script with result type
new_script_with_result = Script.create(
    connection=conn,
    name='ScriptWithResult',
    runtime_id=RUNTIME_ID,
    # see `script-templates` to check how to return from a returning script
    code='def get_results():\n    return 42',
    destination_folder=FOLDER_ID,
    script_result_type=ScriptResultType.NUMERICAL,  # requires `get_results` to be defined
    validate_code=True,
)

# Create Datasource script instead of a standard one
new_datasource_script = Script.create(
    connection=conn,
    name='MyDatasourceScript',
    runtime_id=RUNTIME_ID,
    code='data = [1, 2, 3]\n...',  # this is only mocked code, replace with a valid one
    destination_folder=FOLDER_ID,
    script_usage_type=ScriptUsageType.DATASOURCE,
    variables=[
        VariableDatasourceScript('filter_param', value='default'),
    ],
    validate_code=True,
)

# --- Script Execution ---
# Execute script synchronously
status = script.execute()
print(f"Script execution status: {status}")

# Get script execution console output
output = script.execution_stdout
print(f"Script output: {output}")

# Execute script asynchronously
script.execute(block_until_done=False)
# [Note]: no status check here as with this flag off, it is an asynchronous operation

# Wait for script execution
final_status = script.wait_for_execution_finish()
print(f"Script execution status: {final_status}")

# Execute with variable answers
status = new_script_with_vars.execute(
    variables_answers={
        'name': 'Charlie',
        # this flag allows to keep a default Variable value as an answer to its
        # prompt for this execution
        'age': VariableAnswer.KEEP_GLOBAL_DEFAULT,
        # OR
        # If previously set, this flag allows to keep a default Variable
        # personal answer as an answer to its prompt for this execution
        'email': VariableAnswer.KEEP_PERSONAL_DEFAULT,
    },
)

# Execute with variable answers using VariableAnswer class, for code readability
status = new_script_with_vars.execute(
    variables_answers=[
        VariableAnswer.For('name').should_be('Bob'),
        # this flag allows to keep a default Variable value as an answer to its
        # prompt for this execution
        VariableAnswer.For('age').should_be_global_default,
        # OR
        # If previously set, this flag allows to keep a default Variable
        # personal answer as an answer to its prompt for this execution
        VariableAnswer.For('email').should_be_personal_default,
    ],
)

# execute script synchronously allowing to answer variables on the fly
# [Disclaimer]: Does not work in Workstation, only standalone
status = new_script_with_vars.execute(
    allow_interactive_answering=True,
)
# [Note]: you will be prompted to provide answer to each prompted unanswered
# variable, one by one

print(f"Script execution status: {status}")

# Get script execution status
current_status = script.get_execution_status()

# Get detailed execution information
execution_details = script.get_execution_details()
print(execution_details)

# Get last execution run details
last_run_details = script.get_last_run_details()

# Stop running script execution
script.execute(block_until_done=False)
script.stop_execution()

status = script.execution_status
print(f"Script execution stopped: {status}")

# --- Script Variables Management ---
# Get script variables
variables = script.get_variables()

# Add variables to script
script.add_variables(
    VariableStandardScript('new_var', value='default'),  # using dedicated Variable class
    {'name': 'another_var', 'type': VariableType.TEXT},  # using dictionary of data
)

# Alter existing variables
script.alter_variables(
    changes={
        'new_var': VariableStandardScript('new_var', value='updated'),  # using Variable class
        'another_var': {'value': 'new_default'},  # using dictionary of data
    }
)

# Delete variables from script
script.delete_variables(
    'new_var',  # by name
    VariableStandardScript("another_var")  # by Variable object
)

# Save personal variable answers (for prompted variables)
script.save_personal_variable_answers(
    answers={'prompt_var': 'my_answer'}
)

# --- Script Modification ---
# Alter script properties
script.alter(
    name='UpdatedScriptName',
    description='Updated description',
    code='print("Updated code")',
    validate_code=True,
)

# Change script runtime
script.alter(runtime_id=RUNTIME_ID)

# Change script result type
script.alter(script_result_type=ScriptResultType.TEXT)

# Update all variables in script at once
script.alter(
    variables=[
        VariableStandardScript('var1', value='val1'),
        VariableStandardScript('var2', value='val2'),
    ]
)

# --- Script Code Access ---
# Get script code as text
code_text = script.code
print(code_text)

# Read properties of last execution status
print(script.execution_stdout)  # When Script is successful, STDOUT of the Script
print(script.execution_stderr)  # When Script is successful, STDERR of the Script
print(script.execution_pod_executor_message)  # When Script errored out during runtime, error details of why
print(script.execution_result)  # When Script is successful and with return type, the returned result

# --- Script Deletion ---
# Delete script with confirmation prompt
script.delete()

# Delete script without confirmation prompt
script.delete(force=True)

# --- Datasource and Transaction Scripts ---
# Create a datasource script
new_datasource_script = Script.create(
    connection=conn,
    name='DatasourceScript',
    runtime_id=RUNTIME_ID,
    code='data = [1, 2, 3]\nprint(data)',
    destination_folder=FOLDER_ID,
    script_usage_type=ScriptUsageType.DATASOURCE,
    validate_code=True,
)

# Create a transaction script with transaction column variable
transaction_script = Script.create(
    connection=conn,
    name='TransactionScript',
    runtime_id=RUNTIME_ID,
    code='print($txn_var)',
    destination_folder=FOLDER_ID,
    script_usage_type=ScriptUsageType.TRANSACTION,
    variables=[
        VariableTransactionScript(
            'txn_var',
            transaction_column=True,
            prompt=True,
            multiple=True,
        )
    ],
    validate_code=True,
)

# Execute datasource script
status = new_datasource_script.execute()

# Execute transaction script with answers
status = transaction_script.execute(
    variables_answers={'txn_var': ['value1', 'value2']},
)

# --- Error Handling ---
# Handle execution errors
try:
    code_with_error = Code(conn, code="1 / 0")
    status = code_with_error.execute(raise_on_execution_failure=True)
except ScriptError as err:
    print(f"Execution error: {err}")

# Read execution error when logs are not piped
code_with_error = Code(conn, code="1 / 0")
status = code_with_error.execute()
if status == ExecutionStatus.ERROR:
    error_message = code_with_error.stderr
    print(f"Execution failed with error: {error_message}")

# Check if code is valid
if code.is_valid():
    print("Code is valid")
else:
    print("Code has syntax errors")
