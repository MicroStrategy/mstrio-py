from mstrio.connection import get_connection
from mstrio.object_management.folder import Folder
from mstrio.helpers import AggregatedRights
from mstrio.users_and_groups.user import User
from mstrio.users_and_groups.user_group import list_user_groups

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# assign ACL AggregatedRights.VIEW to UserGroup
user_group = list_user_groups(conn, name='Mobile')[0]
user_group.acl_add(
    rights=AggregatedRights.VIEW,
    trustees=[User(conn, name='Administrator')],
    denied=False,
)

# assign ACL AggregatedRights.VIEW to UserGroup and propagate it to children
user_group = list_user_groups(conn, name='Mobile')[0]
user_group.acl_add(
    rights=AggregatedRights.VIEW,
    trustees=[User(conn, name='Administrator')],
    denied=False,
    propagate_to_children=True,
)

# assign ACLs for folder
folder = Folder(conn, id='945A968E40E4EA2C9114BBBE885DBC24')
folder.acl_add(rights=127, trustees=[User(conn, name='Administrator')], denied=False)

# assign ACLs for folder and propagate to children
folder = Folder(conn, id='945A968E40E4EA2C9114BBBE885DBC24')
folder.acl_add(
    rights=127,
    trustees=[User(conn, name='Administrator')],
    denied=False,
    propagate_to_children=True,
)
