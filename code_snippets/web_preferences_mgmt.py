"""This is the demo script to show how an administrator can manage
Web Preferences for users and projects.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server import WebPreferences
from mstrio.users_and_groups import User

conn = get_connection(connectionData, project_name='MicroStrategy Tutorial')

# Define variables which can be later used in a script
PROJECT_ID = $project_id  # Insert ID of the project
USER_ID = $user_id  # Insert ID of the user

# --- Current user, all projects ---

# Initialize web preferences for the current authenticated user
# across all projects
web_prefs = WebPreferences(connection=conn, use_current_user=True)

# Fetch preferences from the server
web_prefs.fetch()

# List all preferences as objects
all_prefs = web_prefs.list()

# List all preferences as a list of dicts
all_prefs_dict = web_prefs.list(to_dictionary=True)

# List preferences organized by group
prefs_by_group = web_prefs.list_groups()

# --- Current user, specific project ---

# Initialize web preferences for the current user scoped to one project
web_prefs_project = WebPreferences(
    connection=conn,
    use_current_user=True,
    project_id=PROJECT_ID,
)
web_prefs_project.fetch()

# --- Specific user, all projects ---

# Initialize web preferences for a specific user across all projects
user = User(connection=conn, id=USER_ID)
web_prefs_user = WebPreferences(connection=conn, user_or_group=user)
web_prefs_user.fetch()

# --- Specific user, specific project ---

# Initialize web preferences for a specific user in a specific project
web_prefs_user_project = WebPreferences(
    connection=conn,
    user_or_group=user,
    project_id=PROJECT_ID,
)
web_prefs_user_project.fetch()

# --- Project-level defaults (all users in a project) ---

# Initialize web preferences at the project level (all users)
web_prefs_proj_default = WebPreferences(
    connection=conn,
    project_id=PROJECT_ID,
)
web_prefs_proj_default.fetch()

# --- Reading preferences ---

# Get a single preference by name
pref = web_prefs.get("graphWidth")

# Get a single preference as a dict
pref_dict = web_prefs.get("graphWidth", to_dictionary=True)

# Access a preference using subscript syntax
pref = web_prefs["graphWidth"]

# Get all preferences in a group
group_prefs = web_prefs.get_group("graph")

# --- Altering preferences ---

# Alter one or more preferences by name
web_prefs.alter(**{"graphWidth": "800"})

# Use subscript syntax to alter a single preference
web_prefs["graphWidth"] = "800"

# For preferences with simple names (valid Python identifiers), you can pass them as keyword arguments
web_prefs.alter(colorTheme="Blue")

# Alter multiple preferences at once
web_prefs.alter(
    **{
        "fontSize": "12",
        "fontSizeOption": "1"
    }
)

# --- Resetting preferences ---

# Reset a single preference to its default value
web_prefs.reset("graphWidth")

# Reset multiple preferences to their default values
web_prefs.reset(
    [
        "fontSize",
        "fontSizeOption"
    ]
)

# Reset ALL preferences without confirmation prompt
web_prefs.reset_all(force=True)
