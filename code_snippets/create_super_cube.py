"""This is the demo script to show how to export data from MicroStrategy with
SuperCube. It is possible to create and publish single or multi-table SuperCube.

You can update super cube with different policies when adding table:
 - add      -> insert entirely new data
 - update   -> update existing data
 - upsert   -> simultaneously updates existing data and inserts new data
 - replace  -> truncates and replaces the data

You can set in how big increments data is transmitted to the server with the
`chunksize` parameter.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

import pandas as pd

from mstrio.project_objects.datasets import SuperCube
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# prepare Pandas DataFrames to add it into tables of super cube
stores = {"store_id": [1, 2, 3], "location": ["New York", "Seattle", "Los Angeles"]}
stores_df = pd.DataFrame(stores, columns=["store_id", "location"])

sales = {
    "store_id": [1, 2, 3],
    "category": ["TV", "Books", "Accessories"],
    "sales": [400, 200, 100],
    "sales_fmt": ["$400", "$200", "$100"]
}
sales_df = pd.DataFrame(sales, columns=["store_id", "category", "sales", "sales_fmt"])

# Define a variable which can be later used in a script
SUPER_CUBE_NAME = $super_cube_name  # Insert name of created suber cube here

# Add tables to the super cube and create it. By default 'create()' will
# additionally upload data to the I-Server and publish it. You can manipulate it
# by setting parameters `auto_upload` and `auto_publish`
ds = SuperCube(connection=conn, name=SUPER_CUBE_NAME)
ds.add_table(name="Stores", data_frame=stores_df, update_policy="add")
ds.add_table(name="Sales", data_frame=sales_df, update_policy="add")
ds.create()

# When using `SuperCube.add_table()`, Pandas data types are mapped to
# MicroStrategy data types. By default, numeric data is modeled as MSTR metrics
# and non-numeric as attributes. You can set manually which columns treat as
# attributes and which as metrics.
ds.add_table(name="Stores", data_frame=stores_df, update_policy="add", to_attribute=["store_id"])

ds.add_table(
    name="Sales",
    data_frame=sales_df,
    update_policy="add",
    to_attribute=["store_id"],
    to_metric=["sales_fmt"]
)

# Define a variable which can be later used in a script
SUPER_CUBE_ID = $super_cube_id  # insert ID of edited super cube here

# It is possible to update previously created super cubes what looks really
# similar to creation. You can use different update policies which are explained
# in the description of this script at the top. By default, `update()`
# is publishing data automatically, if you don't want to publish data,
# you have to set argument 'auto_publish` to False. It is also possible to set
# chunksize for the update.
ds = SuperCube(connection=conn, id=SUPER_CUBE_ID)
ds.add_table(name="Stores", data_frame=stores_df, update_policy="update")
ds.add_table(name="Sales", data_frame=sales_df, update_policy="upsert")
ds.update()

# Finally, it is possible to certify an existing super cube
ds.certify()

# Limitations
# Updating SuperCubes that were not created using the MicroStrategy REST API is
# not possible. This applies for example to Cubes created via MicroStrategy Web
# client.
