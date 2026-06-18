"""This is a template for a script to remove all unused managed objects on all
provided projects. As long as all the variables are properly set and either
configured as prompted or hardcoded with multiple text values (being either
projects' ID or names), this script will work OOTB.

This script can only be run via Workstation (and then scheduled as Task)
currently. Modify how the `conn` Connection is set if you wish to run it
outside Workstation context.
"""

from mstrio.connection import get_connection


# connect to the environment inside Workstation
conn = get_connection(connectionData)


# define Garbage Cleanup
# this will remove all managed objects that do not have any dependents on them
def remove_unused_managed_objects_from_project(project, tries=3):
    """
    Removes all unused managed objects from a project.

    If the operation failed for any reason for some or all objects, retries
    `tries` amount of times.

    `project` can be an instance of a `Project` class or a Project ID or name.
    """

    with conn.temporary_project_change(project=project):
        while tries:
            succeeded = conn.project.delete_unused_managed_objects(
                try_force_delete=True
            )

            if succeeded:
                break

            tries -= 1


SELECTED_PROJECTS = $selected_projects  # variable: TEXT + MULTIPLE

# if the list above is empty, defaults to ALL LOADED PROJECTS
relevant_projects = SELECTED_PROJECTS or conn.environment.list_loaded_projects()

for project in relevant_projects:
    try:
        # you can modify a line below by providing a `tries` parameter if you
        # wish to change the amount of retries the method will have
        remove_unused_managed_objects_from_project(project)
    except Exception as err:
        print(f"Error was raised during working on '{project}' project: {err}")
