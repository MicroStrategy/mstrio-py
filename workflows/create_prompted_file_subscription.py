"""Create and execute a prompted file subscription.

1. Connect to the environment using data from Workstation.
2. Define and submit the report prompt answer.
3. Create a file subscription from the prompted report instance.
4. Update the subscription prompt answers and execute it.
"""

from mstrio.connection import get_connection
from mstrio.distribution_services import Content, FileSubscription, Schedule
from mstrio.modeling import Prompt
from mstrio.project_objects import Report

PROJECT_NAME = '<Project name>'
REPORT_ID = '<Report ID>'
RECIPIENT_ID = '<Recipient ID with a file delivery address>'

conn = get_connection(connectionData, PROJECT_NAME)

prompt_answers = [
    Prompt(
        key='<Prompt key>',
        type='ELEMENTS',
        answers=[{'id': '<Element ID>', 'name': '<Element name>'}],
    ),
]

report = Report(connection=conn, id=REPORT_ID)
report.answer_prompts(prompt_answers, force=True)

file_sub = FileSubscription.create(
    connection=conn,
    name='<File subscription name>',
    filename='<Output filename>.pdf',
    project_name=PROJECT_NAME,
    contents=Content(
        id=report.id,
        type=Content.Type.REPORT,
        personalization=Content.Properties(
            format_type=Content.Properties.FormatType.PDF,
            prompt=Content.Properties.Prompt(
                enabled=True,
                instance_id=report.instance_id,
            ),
        ),
    ),
    schedules=Schedule(conn, name='<Schedule name>'),
    recipients=[RECIPIENT_ID],
)

# Update the subscription with a new prompted report instance.
file_sub.answer_prompts(prompt_answers, force=True)
file_sub.execute()
