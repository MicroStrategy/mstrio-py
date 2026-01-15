"""This is the demo script to show how to set access permissions on objects so that users and user groups have control
over individual objects in the system.

Code snippets shown here can be applied to almost every object, however as example three different objects will be presented - attribute, schedule, and folder.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
from mstrio.object_management import Folder
from mstrio.modeling.schema import Attribute
from mstrio.distribution_services import Schedule
from mstrio.users_and_groups import User
from mstrio.helpers import Rights
from mstrio.utils.acl import PropagationBehavior
from mstrio.connection import get_connection


# Define a variable which can be later used in a script
USER_NAME = $user_name
PROJECT_NAME = $project_name
ATTRIBUTE_ID = $attribute_id
ATTRIBUTE_NAME = $attribute_name
TRUSTED_USER_NAME = $trusted_user_name
TRUSTED_USER_ID = $trusted_user_id
TRUSTED_USER_ID_1 = $trusted_user_id_1
FOLDER_ID = $folder_id  # ID for Folder object lookup
FOLDER_NAME = $folder_name
SCHEDULE_ID = $schedule_id
SCHEDULE_NAME = $schedule_name


# Create connection based on workstation data
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# First example - attribute
# Get specific object attribute by id
attr = Attribute(connection=conn, id=ATTRIBUTE_ID)

# List ACL for object attribute
attr = Attribute(connection=conn, name=ATTRIBUTE_NAME)
print(attr.acl)

# also you can list ACL and select filters
attr.list_acl(
    to_dataframe=False, # If True, return datasets as pandas DataFrame.
    to_dictionary=False, # If True, return datasets as dicts.
    deny=False, # If True, indicates denied access to the attribute.
    trustee_name=TRUSTED_USER_NAME # Selected user of the attribute.
)

# Add ACL for object attribute
attr.acl_add(
    Rights.EXECUTE, # The degree to which the user or user group is granted or denied access to the object.
    trustees=[TRUSTED_USER_ID, TRUSTED_USER_ID_1], # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=False # Indicates if access is granted or denied to the object
) # see mstrio/utils/acl.py for Rights values

# Alter ACL for object attribute
attr.acl_alter(
    Rights.READ, # The degree to which the user or user group is granted or denied access to the object.
    trustees=User(connection=conn, name=USER_NAME), # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=True # Indicates if access is granted or denied to the object
)

# Second example - schedule

# Get schedule with a given ID
schedule = Schedule(connection=conn, id=SCHEDULE_ID)

# List ACL for schedule object
schedule = Schedule(connection=conn, id=SCHEDULE_NAME)
print(schedule.acl)

# Add ACL right to the schedule object
schedule.acl_add(
    Rights.EXECUTE, # The degree to which the user or user group is granted or denied access to the object.
    trustees=TRUSTED_USER_ID, # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=False # Indicates if access is granted or denied to the object
)
# Alter ACL for schedule object
schedule.acl_alter(
    Rights.READ, # The degree to which the user or user group is granted or denied access to the object.
    trustees=TRUSTED_USER_ID, # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=True # Indicates if access is granted or denied to the object
)

# Third example - folder

# Get folder with a given ID
folder = Folder(conn, id=FOLDER_ID)

# List ACL for folder object
folder = Folder(connection=conn, id=FOLDER_NAME)
print(folder.acl)

# Add ACL right to the folder for the user and propagate to children of folder
folder.acl_add(
    Rights.EXECUTE, # The degree to which the user or user group is granted or denied access to the object.
    trustees=TRUSTED_USER_ID, # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=False, # Indicates if access is granted or denied to the object
    inheritable=True, # If True any objects placed in the folder inherit the folder's entry in the ACL.
    propagate_to_children=True, # If True propagates the access rule to subfolders.
    propagation_behavior=PropagationBehavior.PRECISE_RECURSIVE # Add recursively for all children.
)  # see mstrio/utils/acl.py for PropagationBehavior values

# Alter ACL for folder object
folder.acl_alter(
    Rights.READ, # The degree to which the user or user group is granted or denied access to the object.
    trustees=TRUSTED_USER_ID, # User or user groups IDs to update the ACE for. It can be a single entry or list of entries.
    denied=True, # Indicates if access is granted or denied to the object
    inheritable=False, # If True any objects placed in the folder inherit the folder's entry in the ACL.
    propagate_to_children=False, # If True propagates the access rule to subfolders.
    propagation_behavior=PropagationBehavior.PRECISE_RECURSIVE # Add recursively for all children.
)
