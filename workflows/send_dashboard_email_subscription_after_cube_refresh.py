"""
Manage email subscriptions after cube refresh.
Select a cube, refresh, find its subscriptions and run them.

1. Connect to the environment using data from the workstation
2. Get the intelligent cube object based on provided id
3. Publish retrieved cube and wait for its refresh to complete successfully
4. Get the list of dashboards dependent on the cube
5. Get the list of all subscriptions
6. For each found dashboard, find all subscriptions using it and store them
   in a list
7. Trigger each stored subscription
"""

import time
from mstrio.connection import get_connection
from mstrio.project_objects.datasets.cube import CubeStates
from mstrio.project_objects.datasets import OlapCube
from mstrio.distribution_services.subscription.subscription_manager import (
    list_subscriptions,
)


conn = get_connection(workstationData, 'MicroStrategy Tutorial')


# Select an intelligent cube and refresh it
example_cube = OlapCube(
    connection=conn, id="8CCD8D9D4051A4C533C719A6590DEED8"
)  # Intelligent Cube - Drilling
example_cube.publish()


# Wait for cube refresh to complete successfully.
example_cube.refresh_status()
while "Processing" in CubeStates.show_status(example_cube.status):
    time.sleep(1)
    example_cube.refresh_status()


# Search for subscriptions dependent on that cube
# (find dashboards dependent on cube, and then subscriptions
# dependent on those dashboards found)
dependent_dashboards = example_cube.list_dependents()
all_subscriptions = list_subscriptions(conn)
subscriptions_to_send = []
for d in dependent_dashboards:
    # For each found Dashboard, find all Subscriptions using it.
    # This step requires filtering a list of Subscriptions with Python
    # list operations, as Document/Dashboard query responses do not backlink
    # to Subscriptions.
    dashboard_id = d['id']

    subscriptions_to_send += [
        sub
        for sub in all_subscriptions
        if any(content.id == dashboard_id for content in sub.contents)
    ]

# Trigger (run) the subscriptions
for s in subscriptions_to_send:
    s.execute()
