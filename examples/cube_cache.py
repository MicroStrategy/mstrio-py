"""This is the demo script to show how to manage cube caches.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.project_objects import (OlapCube, CubeCache, list_cube_caches, delete_cube_caches,
                                    delete_cube_cache)

CUBE_ID = '<cube id>'
NODE_NAME = '<node name>'

# get connection to an environment
base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
connection = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                        login_mode=1)

# get caches from an OLAP Cube
oc_caches = OlapCube(connection, id=CUBE_ID).get_caches()

# list all caches
list_cube_caches(connection=connection)
# list all caches on a given node
list_cube_caches(connection=connection, nodes=NODE_NAME)
# list all loaded caches on a given node
list_cube_caches(connection=connection, nodes=NODE_NAME, loaded=True)
# list all cache on a given node for given cube
list_cube_caches(connection=connection, nodes=NODE_NAME, cube_id=CUBE_ID)
# list all cache on a given node for given database connection
list_cube_caches(connection=connection, nodes=NODE_NAME,
                 db_connection_id='<database connection id>')

# get a single cube cache by its id
cube_cache_ = CubeCache(connection=connection, cache_id='<cube cache id>')

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
delete_cube_cache(connection=connection, id=cube_cache_.id, force=True)

# delete all cube caches (the same rule with `force` as above)
delete_cube_caches(connection=connection, force=True)
# delete all cube caches on a given node (the same rule with `force` as above)
delete_cube_caches(connection=connection, nodes=NODE_NAME, force=True)
# delete all loaded cube caches on a given node (the same rule with `force` as
# above)
delete_cube_caches(connection=connection, nodes=NODE_NAME, loaded=True, force=True)
# delete all cube caches on a given node for a given cube (the same rule with
# `force` as above)
delete_cube_caches(connection=connection, nodes=NODE_NAME, cube_id=CUBE_ID, force=True)
# delete all cube caches on a given node for a given database connection (the
# same rule with `force` as above)
delete_cube_caches(connection=connection, nodes=NODE_NAME,
                   db_connection_id='<database connection id>', force=True)
