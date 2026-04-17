# This script deletes all selected users by their usernames.
# It uses three files:
# - USERS_IN (read-only) lists usernames selected for deletion.
# - USER_IDS (read-only) stores username-ID pairs.
# - USERS_REMAINING (write-only) lists usernames that remain
#       after the script is run.

from mstrio.connection import get_connection
from mstrio.object_management.object import bulk_delete_objects
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import list_users


PROJECT_NAME = 'MicroStrategy Tutorial'  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# These files should reside on the machine local to Python runtime, that is:
# - if run with PyExec - on the machine with Workstation,
# - if run with server-side execution runtime - on the server.
USERS_IN = "C:\\Temp\\to_delete.txt"
USER_IDS = "C:\\Temp\\user_ids.txt"

# This file will be overwritten with each run.
USERS_REMAINING = "C:\\Temp\\users_remaining.txt"


# Read username-ID mappings
# The file should have the IDs listed in the format: `username,user_id`.
map_user_ids = {}
with open(USER_IDS, "r") as f:
    for line in f:
        line = line.strip()
        if "," not in line:
            continue
        username, u_id = line.split(",", 1)
        map_user_ids[username] = u_id
print(f"Found {len(map_user_ids)} usernames.")

# Read users to delete
with open(USERS_IN, "r") as f:
    usernames_to_delete = [line.strip() for line in f if line.strip()]
print(f"{len(usernames_to_delete)} listed for deletion.")

user_ids_selected = [map_user_ids[u] for u in usernames_to_delete if u in map_user_ids]
print(f"{len(user_ids_selected)} users selected to process.")

result: bool = bulk_delete_objects(
    conn, objects=user_ids_selected, objects_type=ObjectTypes.USER, force=True
)
# If deleting all users succeeded, `result` will be set to True

if result:
    print("All users deleted successfully.")
else:
    # List remaining users that failed to delete and print to file
    all_users = list_users(conn)
    remaining_users = [u for u in all_users if u.id in user_ids_selected]
    print(f"{len(remaining_users)} users failed to delete.")

    # Open the output file for write
    with open(USERS_REMAINING, "w") as f_remaining:
        for u in remaining_users:
            f_remaining.write(f"{u.username},{u.id}\n")

print("Done")
