"""This is the demo script to show how to manage content cache. Its basic goal
is to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.content_cache import ContentCache

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Content cache management
# Listing caches with different conditions
list_of_all_caches = ContentCache.list_caches(connection=conn)

# Define a variable which can be later used in a script
CACHE_ID = $cache_id  # Insert ID of cache on which you want to perform actions
WH_TABLE_USED_ID = $wh_table_used_id  # Insert ID of WH table used by cache

list_of_one_cache = ContentCache.list_caches(connection=conn, id=CACHE_ID)
list_of_caches_as_dicts = ContentCache.list_caches(connection=conn, to_dictionary=True)
list_of_caches_wh_table = ContentCache.list_caches(
    connection=conn, wh_tables=WH_TABLE_ID
)

# Get single content cache by its id
content_cache = ContentCache(connection=conn, cache_id=CACHE_ID)

# Unload content cache
content_cache.unload()

# Load content cache
content_cache.load()

# Refresh content cache instance data
content_cache.fetch()

# Listing properties of content cache
properties = content_cache.list_properties()

# Invalidate content cache
content_cache.invalidate()

# Delete content cache
content_cache.delete(force=True)

# Invalidating specific caches
ContentCache.invalidate_caches(connection=conn, ids=[CACHE_ID])

# Deleting all caches
ContentCache.delete_all_caches(connection=conn, force=True)


# Define a variable which can be later used in a script
OTHER_CACHE_ID = $other_cache_id  # Insert ID of cache on which you want to perform actions

# Unload multiple content caches
ContentCache.unload_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])

# Load multiple content caches
ContentCache.load_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])

# Invalidate multiple content caches, we need to provide a list of cache ids
# to be invalidated. Listing function returns a list of ContentCache objects
to_be_invalid = [elem.id for elem in list_of_caches_wh_table]
ContentCache.invalidate_caches(connection=conn, cache_ids=to_be_invalid)

# Delete multiple content caches
ContentCache.delete_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
