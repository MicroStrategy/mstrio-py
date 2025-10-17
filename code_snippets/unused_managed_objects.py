"""This is the demo script to show how administrator can delete unused managed
objects in a specific project.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
from mstrio.connection import get_connection
from mstrio.server import Project

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project to interact with

# get project with a given name and a connection
conn = get_connection(workstationData)
project = Project(connection=conn, name=PROJECT_NAME)
conn.select_project(project=project)

# you can delete unused managed objects in a specific project by simply calling
# the method below on a Project instance
#
# [DISCLAIMER]
#
# This is a very long and resource intensive operation and should be run with
# caution and only if necessary.
project.delete_unused_managed_objects()

# By default only objects with no dependents are deleted. You can change this
# behavior by enabling `try_force_delete` flag on a method. Then if the method
# was not able to deduce whether a managed object is unused, it will try to
# remove it.
project.delete_unused_managed_objects(try_force_delete=True)

# script logs will by default show how many managed objects were found and
# how many were deleted. If any were not deleted, it will log their IDs.

# you can also integrate the result of this operation in your script's logic by
# providing a flag to return all failed items instead of plain `boolean` value
FAILED_ITEMS = project.delete_unused_managed_objects(return_failed_items=True)

# The method returns boolean representing whether the operation removed all
# unused managed objects found by default. With a flag mentioned above set to
# True, it will return a list of dicts containing information about the
# objects that were not removed.
#
# You can gather them and try the below snippet to see what might have happened
from mstrio.object_management.object import Object

FAILED_ITEMS = project.delete_unused_managed_objects(return_failed_items=True)

for item in FAILED_ITEMS:
    try:
        obj = Object.from_dict(item, connection=conn)
        has_deps = obj.has_dependents()
        print(has_deps)  # will print `True/False` or will fail and be caught
        if not has_deps:
            obj.delete(force=True)  # will delete the object or fail and be caught
    except Exception as err:
        print(err)
