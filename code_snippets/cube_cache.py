"""This is the demo script to show how to manage cube caches.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import (
    CubeCache, delete_cube_cache, delete_cube_caches, list_cube_caches, OlapCube
)
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Define a variable which can be later used in a script
CUBE_ID = $cube_id  # Insert name of cube on which you want to perform actions

# get caches from an OLAP Cube
oc_caches = OlapCube(conn, id=CUBE_ID).get_caches()

# Define variables which can be later used in a script
NODE_NAME = $node_name  # Insert name of node on which you want to perform actions
DB_CONNECTION_ID = $db_connection_id  # insert ID of DB connection you want to include in your functions

# list all caches
list_cube_caches(connection=conn)
# list all caches on a given node
list_cube_caches(connection=conn, nodes=NODE_NAME)
# list all loaded caches on a given node
list_cube_caches(connection=conn, nodes=NODE_NAME, loaded=True)
# list all cache on a given node for given cube
list_cube_caches(connection=conn, nodes=NODE_NAME, cube_id=CUBE_ID)
# list all cache on a given node for given database connection
list_cube_caches(connection=conn, nodes=NODE_NAME, db_connection_id=DB_CONNECTION_ID)

# Define a variable which can be later used in a script
CUBE_CACHE_ID = $cube_cache_id  # Insert ID of cube cache that you want to perform your actions upon

# get a single cube cache by its id
cube_cache_ = CubeCache(connection=conn, cache_id=CUBE_CACHE_ID)

# unload a cube cache
cube_cache_.unload()
# load a cube cache
cube_cache_.load()
# deactivate a cube cache
cube_cache_.deactivate()
# activate a cube cache
cube_cache_.activate()

# refresh cube cache
cube_cache_.fetch()

# get state of cube cache
cc_state = cube_cache_.state

# get properties of cube cache
cc_properties = cube_cache_.list_properties()

# Delete a single cube cache (there are two ways). When `force` argument is set
# to `False` (default value) then deletion must be approved.
cube_cache_.delete(force=True)
delete_cube_cache(connection=conn, id=cube_cache_.id, force=True)

# delete all cube caches (the same rule with `force` as above)
delete_cube_caches(connection=conn, force=True)
# delete all cube caches on a given node (the same rule with `force` as above)
delete_cube_caches(connection=conn, nodes=NODE_NAME, force=True)
# delete all loaded cube caches on a given node (the same rule with `force` as
# above)
delete_cube_caches(connection=conn, nodes=NODE_NAME, loaded=True, force=True)
# delete all cube caches on a given node for a given cube (the same rule with
# `force` as above)
delete_cube_caches(connection=conn, nodes=NODE_NAME, cube_id=CUBE_ID, force=True)
# delete all cube caches on a given node for a given database connection (the
# same rule with `force` as above)
delete_cube_caches(connection=conn, nodes=NODE_NAME, db_connection_id=DB_CONNECTION_ID, force=True)
