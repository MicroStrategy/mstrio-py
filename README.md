# mstrio-py: data I/O for Python and MicroStrategy

[mstrio logo here]

## *mstrio?*
mstrio provides a high-level Python interface that's designed to give data scientists and developers access to MicroStrategy data using the [MicroStrategy REST API](https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API.htm). mstrio has a simple workflow to create and manage connections, fetch data from cubes and reports, create new cubes, and modify existing cubes.

With mstrio, it's easy to extract business data from MicroStrategy and use it to train machine learning models or do data science in the tool of your choice. When you're done, enable decision-makers to take action on your insights by pushing new data into the environment.

Prefer R? Check out mstrio for R.[link](www.google.com)


#### Installation
Install with pip
```
pip install mstrio-py
```

Create a connection object using `microstrategy.Connection()` and `connect()`.  Required arguments for the `microstrategy.Connection()` class are the URL for the MicroStrategy REST API server, username, password, and project name. By default, the `connect()` function expects your MicroStrategy username and password. LDAP authentication is supported, too. Use the optional argument `login_mode=16` to the `connect()` function.

```python
from mstrio import microstrategy
conn = microstrategy.Connection(base_url="https://acmeinc.mstr.com/MicroStrategyLibrary/api, username="myUsername", password="myPassword", project_name="Acme, Inc. Analytics")
conn.connect()
```
The URL for the REST API server typically follows this format: _https://mstrEnvironment.com/MicroStrategyLibrary/api_. Validate that the REST API server is running by accessing _https://mstrEnvironment.com/MicroStrategyLibrary/api-docs_ in your web browser.


#### Extract data from cubes and reports
Extract data from MicroStrategy cubes and reports using the `get_cube()` and `get_report()` functions. Just pass in your connection object and the ID for the cube or report that you are fetching. You can get the ID by navigating to the cube within MicroStrategy Web, right-clicking on the cube of interest, and selecting 'properties.' Alternatively, you can use MicroStrategy Developer in a similar manner. `get_cube()` and `get_report()` will return a Pandas DataFrame with the requested data.

```python
cube_dataframe = conn.get_cube(cube_id='E9C9D8BE11E85AD9BDBD0080EFF53CF8')
report_dataframe = conn.get_report(report_id='06D1F3A411E869C3DE670080EF259221')
```

#### Upload data to MicroStrategy
Creating a new in-memory dataset from a Pandas DataFrame is just as easy: `create_dataset()`. You'll need to provide a name for your cube and a name for the table that will contain the data. At this time, only one table per cube is supported. `create_cube()` will return the datasetID and tableIDs, in case you want to save these for later use.

```python
import pandas as pd
raw_data = {'name': ['Bill', 'Betsy', 'Bailey'],
            'age': [45, 23, 31]}
df = pd.DataFrame(raw_data, columns=['name', 'age'])
newDatasetId, newTableId = conn.create_dataset(data_frame=df, dataset_name='Employees', table_name='Ages')
```

#### Add or update a dataset with new data
Once a dataset has been created, you can update it, too. This is helpful if the source data changes and you want to make it available for analysis in MicroStrategy. To accomplish this, use the `update_dataset()` function. Note that you'll need to pass in both the datasetID and tableID for the target dataset and table within the dataset, respectively. These are returned by the `create_dataset()` function.

The `update_policy` parameter controls the update behavior. Currently supported update operations are `add` (inserts entirely new data), `update` (updates existing data), `upsert` (simultaneously updates existing data and inserts new data), and `replace` (truncates and replaces the data).

```python
raw_data = {'name': ['Brian', 'Bob, 'Blake'],
            'age': [41, 27, 34]}
df = pd.DataFrame(raw_data, columns=['name', 'age'])
conn.update_dataset(data_frame=df, dataset_id=newDatasetId, table_name='Ages', update_policy='add')
```

#### More resources
- [Check out mstrio for R](www.google.com)
- [Learn more about the MicroStrategy REST API](https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API.htm)
- [MicroStrategy REST API Demo environment](https://demo.microstrategy.com/MicroStrategyLibrary/api-docs/index.html)
#### License
