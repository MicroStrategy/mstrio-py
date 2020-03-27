[![image](https://img.shields.io/pypi/v/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/l/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/dm/mstrio-py.svg)](https://pypi.org/project/mstrio-py)


# mstrio: simple and secure access to MicroStrategy data
Current version: **11.2.1** (27 Mar 2020). Check out [Release Notes](https://github.com/MicroStrategy/mstrio-py/blob/master/NEWS.md) to see what's new.

**mstrio** provides a high-level interface for [Python][py_github] and [R][r_github] and is designed to give data scientists and developers simple and secure access to MicroStrategy data. It wraps [MicroStrategy REST APIs][mstr_rest_docs] into simple workflows, allowing users to connect to their MicroStrategy environment, fetch data from cubes and reports, create new datasets, and add new data to existing datasets. And, because it enforces MicroStrategy's user and object security model, you don't need to worry about setting up separate security rules.

With **mstrio**, it's easy to integrate cross-departmental, trustworthy business data in machine learning workflows and enable decision-makers to take action on predictive insights in MicroStrategy Reports, Dossiers, HyperIntelligence Cards, and customized, embedded analytical applications.

## Table of contents
<!--ts-->
   * [Installation](#installation)
      * [Installing Jupyter Notebook extension](#installing-jupyter-notebook-extension)
   * [Versioning](#versioning)
   * [Usage](#usage)
      * [Connect to MicroStrategy](#connect-to-microStrategy)
      * [Import data from Cubes and Reports](#import-data-from-cubes-and-reports)
      * [Export data into MicroStrategy with Datasets](#export-data-into-microStrategy-with-datasets)
        * [Create a new dataset](#create-a-new-dataset)
        * [Update a dataset](#update-a-dataset)
        * [Certify a dataset](#certify-a-dataset)
   * [More resources](#more-resources)
<!--te-->

## Installation
Installation is easy when using [pip](https://pypi.org/project/mstrio-py). Read more about installation on MicroStrategy's [product documentation][mstr_help_docs].

### Install the `mstrio-py` package
```
pip3 install mstrio-py
```
### Enable the Jupyter Notebook extension
```
jupyter nbextension install connector-jupyter --py --sys-prefix
jupyter nbextension enable connector-jupyter --py --sys-prefix
```

## Versioning
Functionalities may be added to mstrio either in combination with annual MicroStrategy platform releases or through updates to platform releases. To ensure compatibility with APIs supported by your MicroStrategy environment, it is recommended to install a version of mstrio that corresponds to the version number of your MicroStrategy environment.

The current version of mstrio-py is 11.2.1 and is supported on MicroStrategy 2019 Update 4 (11.1.4) and later. To leverage MicroStrategy for Jupyter, mstrio-py (11.2.1), Jupyter Notebook (6.0.2 or higher), ipywidgets (7.5.1 or higher) and MicroStrategy 2019 Update 4 (11.1.4) or higher are required.

If you intend to use mstrio with MicroStrategy version older than 11.1.4, refer to the Pypi package archive to download mstrio 10.11.1, which is supported on:
 * MicroStrategy 2019 (11.1)
 * MicroStrategy 2019 Update 1 (11.1.1)
 * MicroStrategy 2019 Update 2 (11.1.2)
 * MicroStrategy 2019 Update 3 (11.1.3)
 
Refer to the [PyPi package archive][pypi_archive] for a list of available versions. 

To install a specific, archived version of mstrio, [package archive on PyPi][pypi_archive], do so by specifying the desired version number when installing the package with `pip`, as follows:

```python
pip install mstrio-py==10.11.1
```


## Main Features
Read the following tutorials to become more familiar with **mstrio**
- Connect to your MicroStrategy environment
- Import data from a Report into a Pandas DataFrame
- Import data from a Cube into a Pandas DataFrame
- Export data into MicroStrategy by creating datasets
- Update, replace, or append new data to an existing dataset

## Usage
### Connect to MicroStrategy
The connection object manages your connection to MicroStrategy. Connect to your MicroStrategy environment by providing the URL to the MicroStrategy REST API server, your username, password, and the project id (case-sensistive) to connect to. By default, the `connect()` function expects your MicroStrategy username and password. 
```python
from mstrio.microstrategy import Connection
import getpass

base_url = "https://mycompany.microstrategy.com/MicroStrategyLibrary/api"
mstr_username = "username"
mstr_password = getpass.getpass('password: ')
project_id = "id"
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id)
conn.connect()
```

The URL for the REST API server typically follows this format: _https://mycompany.microstrategy.com/MicroStrategyLibrary/api_. Validate that the REST API server is running by accessing _https://mycompany.microstrategy.com/MicroStrategyLibrary/api-docs_ in your web browser.

Currently, supported authentication modes are Standard (the default) and LDAP. To use LDAP, add `login_mode` when creating your Connection object:
```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id,
                 login_mode=16)
conn.connect()
```

By default, SSL certificates are validated with each API request. To turn this off, use:
```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, 
                ssl_verify=False)
conn.connect()
```

### Import data from Cubes and Reports
In **mstrio-py**, Reports and Cubes have the same API, so you can use these examples for importing Report data to a DataFrame, too. To import the contents of a published cube into a DataFrame for analysis in Python, use the `Cube` class:
```python
from mstrio.cube import Cube
my_cube = Cube(connection=conn, cube_id="...")
df = my_cube.to_dataframe()
```
To import Reports into a DataFrame for analysis in Python use the optimized `Report` class:
```python
from mstrio.report import Report
my_report = Report(connection=conn, report_id="...")
df = my_report.to_dataframe()
```
By default, all rows are imported when `my_cube.to_dataframe()` or `my_report.to_dataframe()` are called. Filter the contents of a cube/report by passing the object IDs for the metrics, attributes, and attribute elements you need. First, get the object IDs of the metrics, attributes that are available within the Cube/Report object instance:
```python
my_cube.metrics
my_cube.attributes
```
If you need to filter by attribute elements, call `my_cube.get_attr_elements()` or `my_report.get_attr_elements()` which will fetch all unique attribute elements per attribute. The attribute elements are available within the Cube/Report object instance:
```python
my_cube.attr_elements
```
Then, choose those elements by passing their IDs to the `my_cube.apply_filters()` method. To see the chosen elements, call `my_cube.filters` and to clear any active filters, call `my_cube.clear_filters()`.
```python
my_cube.apply_filters(
   attributes=["A598372E11E9910D1CBF0080EFD54D63", "A59855D811E9910D1CC50080EFD54D63"],
   metrics=["B4054F5411E9910D672E0080EFC5AE5B"],
   attr_elements=["A598372E11E9910D1CBF0080EFD54D63:Los Angeles", "A598372E11E9910D1CBF0080EFD54D63:Seattle"])
df = my_cube.to_dataframe()
```

### Export data into MicroStrategy with Datasets
##### Create a new dataset
With **mstrio** you can create and publish single or multi-table datasets. This is done by passing Pandas DataFrames to a dataset constructor which translates the data into the format needed by MicroStrategy.
```python
import pandas as pd
stores = {"store_id": [1, 2, 3],
          "location": ["New York", "Seattle", "Los Angeles"]}
stores_df = pd.DataFrame(stores, columns=["store_id", "location"])

sales = {"store_id": [1, 2, 3],
         "category": ["TV", "Books", "Accessories"],
         "sales": [400, 200, 100],
         "sales_fmt": ["$400", "$200", "$100"]}
sales_df = pd.DataFrame(sales, columns=["store_id", "category", "sales", "sales_fmt"])

from mstrio.dataset import Dataset
ds = Dataset(connection=conn, name="Store Analysis")
ds.add_table(name="Stores", data_frame=stores_df, update_policy="add")
ds.add_table(name="Sales", data_frame=sales_df, update_policy="add")
ds.create()
```
By default `Dataset.create()` will upload the data to the Intelligence Server and publish the dataset. If you just want to _create_ the dataset but not upload the row-level data, use `Dataset.create(auto_upload=False)`.

When using `Dataset.add_table()`, Pandas data types are mapped to MicroStrategy data types. By default, numeric data (integers and floats) are modeled as MicroStrategy Metrics and non-numeric data are modeled as MicroStrategy Attributes. This can be problematic if your data contains columns with integers that should behave as Attributes (e.g. a row ID), or if your data contains string-based, numeric _looking_ data which should be Metrics (e.g. formatted sales data, ["$450", "$325"]). To control this behavior, provide a list of columns that you want to convert from one type to another.
```python
ds.add_table(name="Stores", data_frame=stores_df, update_policy="add",
             to_attribute=["store_id"])

ds.add_table(name="Sales", data_frame=sales_df, update_policy="add",
             to_attribute=["store_id"],
             to_metric=["sales_fmt"])
```
 It is also possible to specify where the dataset should be created by providing a folder ID in `Dataset.create(folder_id="...")`.
 
After creating the dataset, you can obtain its ID using `Datasets.dataset_id`. This ID is needed for updating the data later.

##### Update a dataset
When the source data changes and users need the latest data for analysis and reporting in MicroStrategy, **mstrio** allows you to update the previously created dataset.
```python
from mstrio.dataset import Dataset
ds = Dataset(connection=conn, dataset_id="...")
ds.add_table(name="Stores", data_frame=stores_df, update_policy='update')
ds.add_table(name="Sales", data_frame=sales_df, update_policy='upsert')
ds.update()
ds.publish()
```
The `update_policy` parameter controls how the data in the dataset gets updated. Currently supported update operations are `add` (inserts entirely new data), `update` (updates existing data), `upsert` (simultaneously updates existing data and inserts new data), and `replace` (truncates and replaces the data).

By default, the raw data is transmitted to the server in increments of 100,000 rows. On very large datasets (>1 GB), it is beneficial to increase the number of rows transmitted to the Intelligence Server with each request. Do this with the `chunksize` parameter:
```python
ds.update(chunksize=500000)
```

Finally, note that updating datasets that were _not_ created using the REST API is not supported.

##### Certify a dataset
Use `Dataset.certify()` to certify / decertify an existing dataset. Note that this will only work for datasets created using mstrio or any other client leveraging MicroStrategy REST API.

## More resources
- [Tutorials for mstrio][mstr_datasci_comm]
- [mstrio-py online documentation][mstrio_py_doc]
- [Check out mstrio for R][r_github]
- [Learn more about the MicroStrategy REST API][mstr_rest_docs]
- [MicroStrategy REST API Demo environment][mstr_rest_demo]

## Other
"Jupyter" and the Jupyter logos are trademarks or registered trademarks of NumFOCUS.

[pypi_archive]: <https://pypi.org/project/mstrio-py/#history>
[py_github]: <https://github.com/MicroStrategy/mstrio-py>
[r_github]: <https://github.com/MicroStrategy/mstrio>
[mstr_datasci_comm]: <https://community.microstrategy.com/s/topic/0TO44000000AJ2dGAG/python-r-u108>
[mstrio_py_doc]: <http://www2.microstrategy.com/producthelp/Current/mstrio-py/>
[mstr_rest_demo]: <https://demo.microstrategy.com/MicroStrategyLibrary/api-docs/index.html>
[mstr_rest_docs]: <https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API.htm>
[mstr_help_docs]: <https://www2.microstrategy.com/producthelp/current/MSTR-for-Jupyter/Content/mstr_for_jupyter.htm>
