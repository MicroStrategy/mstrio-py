"""
Export selected information about users and user groups to a CSV file.

1. Provide name of the project to connect to.
2. Connect to the environment using data from workstation.
3. Define filename where exported data will be saved.
4. Open the file and write the header row.
5. List all user groups and write their information to the file.
6. List all users and write their information to the file.
"""

from mstrio.connection import get_connection
from mstrio.users_and_groups import (
    list_user_groups,
    list_users,
)
import csv

# Define project to connect with
PROJECT_NAME = 'MicroStrategy Tutorial'  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define filename where exported data will be saved. In Workstation you need to
# provide absolute path to the file remembering about double backslashes on WIN
# for example: 'C:\\Users\\admin\\Documents\\data\\users_and_user_groups.csv'
FILE_PATH = '<PATH_TO_FILE>'
with open(FILE_PATH, mode='w', newline='') as file:
    file_writer = csv.writer(
        file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    file_writer.writerow(
        [
            'Full Name',
            'User ID',
            'Username (Login)',
            'Enabled',
            'Date Created',
            'Date Modified',
            'Description',
        ]
    )

    user_groups = list_user_groups(connection=conn)
    for user_group in user_groups:
        file_writer.writerow(
            [
                user_group.name,
                user_group.id,
                user_group.name,
                'N/A',
                user_group.date_created,
                user_group.date_modified,
                user_group.description,
            ]
        )

    users = list_users(connection=conn)
    for user in users:
        file_writer.writerow(
            [
                user.full_name,
                user.id,
                user.username,
                user.enabled,
                user.date_created,
                user.date_modified,
                user.description,
            ]
        )
