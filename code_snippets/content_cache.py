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

list_of_one_cache = ContentCache.list_caches(connection=conn, id=CACHE_ID)
list_of_caches_as_dicts = ContentCache.list_caches(connection=conn, to_dictionary=True)

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

# Delete content cache
content_cache.delete(force=True)

# Define a variable which can be later used in a script
OTHER_CACHE_ID = $other_cache_id  # Insert ID of cache on which you want to perform actions

# Unload multiple content caches
ContentCache.unload_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])

# Load multiple content caches
ContentCache.load_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])

# Delete multiple content caches
ContentCache.delete_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
