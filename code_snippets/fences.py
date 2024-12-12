"""This is the demo script to show how to manage fences.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.server.fence import Fence, FenceType, list_fences
from mstrio.server.project import Project
from mstrio.users_and_groups import User, UserGroup

# Define a variable which can be later used in a script
PROJECT_ID = $project_id

conn = get_connection(workstationData, project_id=PROJECT_ID)

# List fences
# Note: No Fences exist in a default environment
fences = list_fences(connection=conn)
fences_as_dicts = list_fences(connection=conn, to_dictionary=True)

# Define a variable which can be later used in a script
RANK = $rank
FENCE_NAME = $fence_name
NODE_NAME = $node_name
USER_ID = $user_id
USER_GROUP_ID = $user_group_id

# Create a Fence
fence = Fence.create(
    connection=conn,
    rank=RANK,
    name=FENCE_NAME,
    type=FenceType.USER_FENCE,
    nodes=[NODE_NAME],
    users=[User(connection=conn, id=USER_ID)],
    user_groups=[UserGroup(connection=conn, id=USER_GROUP_ID)],
    projects=[Project(connection=conn, id=PROJECT_ID)],
)

# Get a Fence by it's id or name
fence = Fence(connection=conn, id=fence.id)
fence = Fence(connection=conn, name=FENCE_NAME)

# Define variables which can be later used in a script
RANK_2 = $rank_2
USER_ID_2 = $user_id_2
USER_GROUP_ID_2 = $user_group_id_2
PROJECT_ID_2 = $project_id_2

# Alter a Fence
fence.alter(
    rank=RANK_2,
    users=[User(connection=conn, id=USER_ID_2)],
    user_groups=[UserGroup(connection=conn, id=USER_GROUP_ID_2)],
    projects=[Project(connection=conn, id=PROJECT_ID_2)],
)

# Delete a Fence
fence.delete(force=True)
