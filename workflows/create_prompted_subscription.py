"""Create an email subscription with prompts.
1. Connect to the environment using data from workstation
2. Create a list of prompts for the report
3. Answer the prompts
4. Create an email subscription with the answered prompts
5. Execute the subscription with defined prompt answers
"""

from mstrio.connection import get_connection
from mstrio.distribution_services import Content, EmailSubscription, Schedule
from mstrio.project_objects import Prompt, Report

PROJECT_NAME = 'MicroStrategy Tutorial'  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Prepare a list of answers for the prompts in the report
prompts = [
    Prompt(
        type='OBJECTS',
        answers=[
            {"name": "Cost", "id": "7FD5B69611D5AC76C000D98A4CC5F24F", "type": "metric"}
        ],
        key='8891A8AF4A747A3EA8506DBB6189F252@0@10',
        id='8891A8AF4A747A3EA8506DBB6189F252',
        name='Predefined list of objects',
        use_default=False,
    ),
    Prompt(
        type='EXPRESSION',
        answers={
            "content": "Item (ID) = 23",
            "expression": {
                "operator": "And",
                "operands": [
                    {
                        "operator": "Equals",
                        "operands": [
                            {
                                "type": "form",
                                "attribute": {
                                    "id": "8D679D4211D3E4981000E787EC6DE8A4",
                                    "name": "Item",
                                },
                                "form": {
                                    "id": "45C11FA478E745FEA08D781CEA190FE5",
                                    "name": "ID",
                                },
                            },
                            {
                                "type": "constant",
                                "dataType": "Integer",
                                "value": "23",
                            },
                        ],
                    }
                ],
            },
        },
        key='742FE7A7486EE982FC006C98D4048A1B@0@10',
        id='742FE7A7486EE982FC006C98D4048A1B',
        name='Attributes of the Products hierarchy',
        use_default=False,
    ),
    Prompt(
        type='ELEMENTS',
        answers=[{"id": "h11;8D679D4B11D3E4981000E787EC6DE8A4", "name": "Canada"}],
        key='0CF9922747C3C94DAA18F489C36532D2@0@10',
        id='0CF9922747C3C94DAA18F489C36532D2',
        name='Elements of Region',
        use_default=False,
    ),
    Prompt(
        type='ELEMENTS',
        answers=[
            {"id": "h1;8D679D3711D3E4981000E787EC6DE8A4", "name": "Books"},
            {"id": "h3;8D679D3711D3E4981000E787EC6DE8A4", "name": "Movies"},
        ],
        key='094AF11F4164B417491024AE00C2A122@0@10',
        id='094AF11F4164B417491024AE00C2A122',
        name='Elements of Category',
        use_default=False,
    ),
    Prompt(
        type='ELEMENTS',
        answers=[{"id": "h12;8D679D4F11D3E4981000E787EC6DE8A4", "name": "Business"}],
        key='17E83147401F9CEDAA07CF826DE4CFB4@0@10',
        id='17E83147401F9CEDAA07CF826DE4CFB4',
        name='Elements of Subcategory filtered by Elements of Category',
        use_default=False,
    ),
]

# Report with nested prompts
report = Report(connection=conn, name='6- Prompted Profit Trend')

report.answer_prompts(prompts)

# After answering the prompts, the report object will have the instance_id
# property set, which is required for creating a subscription with prompts
print(report.instance_id)

email_sub = EmailSubscription.create(
    connection=conn,
    name='<Name of the subscription>',
    project_name=PROJECT_NAME,
    contents=[
        Content(
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
    ],
    schedules=Schedule(conn, name='Monday Morning'),
    recipients=['54F3D26011D2896560009A8E67019608'],
    email_subject='<Email subject>',
)

# Execute the subscription with defined prompt answers
email_sub.execute()
