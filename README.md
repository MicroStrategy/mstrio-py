![MicroStrategy Logo][logo]

[![image](https://img.shields.io/pypi/v/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/l/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/dm/mstrio-py.svg)](https://pypi.org/project/mstrio-py)

# mstrio: Simple and Secure Access to MicroStrategy Data <!-- omit in toc -->

**mstrio** provides a high-level interface for [Python][py_github] and [R][r_github] and is designed to give data scientists and developers simple and secure access to MicroStrategy data. It wraps [MicroStrategy REST APIs][mstr_rest_docs] into simple workflows, allowing users to connect to their MicroStrategy environment, fetch data from cubes and reports, create new datasets, and add new data to existing datasets. And, because it enforces MicroStrategy's user and object security model, you don't need to worry about setting up separate security rules.

With **mstrio**, it's easy to integrate cross-departmental, trustworthy business data in machine learning workflows and enable decision-makers to take action on predictive insights in MicroStrategy reports, Dossiers, HyperIntelligence Cards, and customized, embedded analytical applications.

**MicroStrategy for Jupyter** is an extension for Jupyter Notebook which provides a graphical user interface for **mstrio-py** methods with the help of which user can perform all of the import and export actions without writing a single line of code manually. MicroStrategy for Jupyter is contained within **mstrio-py** package and is available after installation and enabling as Jupyter extension.

# Table of Contents <!-- omit in toc -->
<!--ts-->
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
    - [mstrio-py](#mstrio-py)
    - [MicroStrategy for Jupyter](#microstrategy-for-jupyter)
  - [Install the `mstrio-py` Package](#install-the-mstrio-py-package)
  - [Enable the Jupyter Notebook extension](#enable-the-jupyter-notebook-extension)
- [Versioning & Main Features](#versioning--main-features)
  - [Versioning](#versioning)
  - [Main Features](#main-features)
- [Usage](#usage)
  - [Connect to MicroStrategy](#connect-to-microstrategy)
    - [Authentication Methods](#authentication-methods)
    - [SSL Self-signed Certificate](#ssl-self-signed-certificate)
  - [Import Data from Cubes and Reports](#import-data-from-cubes-and-reports)
  - [Export Data into MicroStrategy with Datasets](#export-data-into-microstrategy-with-datasets)
    - [Create a New Dataset](#create-a-new-dataset)
    - [Update a Dataset](#update-a-dataset)
    - [Certify a dataset](#certify-a-dataset)
    - [Limitations](#limitations)
- [More Resources](#more-resources)
- [Other](#other)
<!--te-->

# Installation
## Prerequisites
### mstrio-py
* Python 3.6+
* MicroStrategy 2019 Update 4 (11.1.4)+
### MicroStrategy for Jupyter
* mstrio-py 11.1.4+
* Jupyter Notebook 6.0.2+
* ipywidgets 7.5.1+
* [CORS enabled on MicroStrategy Library server][cors_manual]
* [Cookies sent by MicroStrategy Library server have `SameSite` parameter set to `None`][same_site_manual]


## Install the `mstrio-py` Package
**Note**: it is not recommended to install mstrio-py in an Anaconda environment.
For a seamless experience, install and run it in Python's [virtual environment][python_venv] instead.

Installation is easy when using [pip](https://pypi.org/project/mstrio-py). Read more about installation on MicroStrategy's [product documentation][mstr_help_docs].

```
pip3 install mstrio-py
```

## Enable the Jupyter Notebook extension
Once mstrio-py is installed you can install and enable the Jupyter Notebook extension by using the commands below:
```
jupyter nbextension install connector-jupyter --py --sys-prefix
jupyter nbextension enable connector-jupyter --py --sys-prefix
```

# Versioning & Main Features
## Versioning
Current version: **11.2.2.1** (4 August 2020). Check out [Release Notes][release_notes] to see what's new.

Functionalities may be added to mstrio either in combination with annual MicroStrategy platform releases or through updates to platform releases. To ensure compatibility with APIs supported by your MicroStrategy environment, it is recommended to install a version of mstrio that corresponds to the version number of your MicroStrategy environment.

The current version of mstrio-py is 11.2.2.1 and is supported on MicroStrategy 2019 Update 4 (11.1.4) and later. To leverage MicroStrategy for Jupyter, mstrio-py (11.1.4), Jupyter Notebook (6.0.2), ipywidgets (7.5.1) and MicroStrategy 2019 Update 4 (11.1.4) or higher are required.

If you intend to use mstrio with MicroStrategy version older than 11.1.4, refer to the Pypi package archive to download mstrio 10.11.1, which is supported on:
 * MicroStrategy 2019 (11.1)
 * MicroStrategy 2019 Update 1 (11.1.1)
 * MicroStrategy 2019 Update 2 (11.1.2)
 * MicroStrategy 2019 Update 3 (11.1.3)

Refer to the [PyPi package archive][pypi_archive] for a list of available versions.

To install a specific, archived version of mstrio, choose the desired version available on [PyPi's package archive][pypi_archive] and install with `pip`, as follows:

```python
pip install mstrio-py==10.11.1
```

## Main Features
Read the following tutorials to become more familiar with **mstrio-py**
- Connect to your MicroStrategy environment
- Import data from a Report into a Pandas DataFrame
- Import data from a Cube into a Pandas DataFrame
- Filter Cubes and Reports by selecting Attributes and Metrics or specifying a view filter
- Export data into MicroStrategy by creating Datasets
- Update, replace, or append new data to an existing Dataset

# Usage
## Connect to MicroStrategy
The `Connection` object manages your connection to MicroStrategy. Connect to your MicroStrategy environment by providing the URL to the MicroStrategy REST API server, your username, password and the ID of the Project to connect to. When a `Connection` object is created the user will be automatically logged-in.

```python
from mstrio.connection import Connection
import getpass

base_url = "https://your-microstrategy-server.com/MicroStrategyLibrary/api"
mstr_username = "Username"
mstr_password = getpass.getpass("Password: ")
project_id = "PROJECT_ID"
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id)
```

The URL for the REST API server typically follows this format: _https://your-microstrategy-server.com/MicroStrategyLibrary/api_

Validate that the REST API server is running by accessing _https://your-microstrategy-server.com/MicroStrategyLibrary/api-docs_ in your web browser.

To manage the connection the following methods are made available:

```python
conn.connect()
conn.renew()
conn.close()
conn.status()
```

### Authentication Methods
Currently, supported authentication modes are **Standard** (the default) and **LDAP**. To use LDAP, add `login_mode=16` when creating your `Connection` object:
```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=16)
```

Optionally, the `Connection` object can be created by passing the `identity_token` parameter, which will create a delegated session. The identity token can be obtained by sending a request to MicroStrategy REST API `/auth/identityToken` endpoint.

```python
conn = Connection(base_url, identity_token=identity_token, project_id=project_id)
```


### SSL Self-signed Certificate
By default, SSL certificates are validated with each API request. To turn this off, use `ssl_verify` flag:

```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, ssl_verify=False)
```

If you are using a SSL with a self-signed certificate you will need to perform an additional step to configure your connection. There are 2 ways to set it up:

1. The easiest way to configure the SSL is to move your certificate file to your working directory. Just make sure the `ssl_verify` parameter is set to `True` when creating the `Connection` object in mstrio-py (it is `True` by default):

```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, ssl_verify=True)
```

2. The second way is to pass the `certificate_path` parameter to your connection object in mstrio. It has to be the absolute path to your certificate file:

```python
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, certificate_path="C:/path/to/your/certificate.pem")
```

## Import Data from Cubes and Reports
Better fetching performance can be achieved by utilizing the parallel download of data chunks. This feature is
controlled by the `parallel` flag and is enabled by default. Disabling this setting will lower the peak I-Server load.
To import the contents of a published Cube into a DataFrame for analysis in Python, use the `Cube` class:

```python
from mstrio.cube import Cube
my_cube = Cube(connection=conn, cube_id=cube_id)
df = my_cube.to_dataframe()
```

To import Reports into a DataFrame for analysis in Python use the appropriate `Report` class:

```python
from mstrio.report import Report
my_report = Report(connection=conn, report_id=report_id, parallel=False)
df = my_report.to_dataframe()
```
By default, all rows are imported when `my_cube.to_dataframe()` or `my_report.to_dataframe()` are called. Filter the contents of a `Cube` / `Report` by passing the selected object IDs for the metrics, attributes, and attribute elements to the `apply_filters()` method.

To get the list of object IDs of the metrics, attributes, or attribute elements that are available within the Cube / Report MicroStrategy objects, use the following `Cube` / `Report` class properties:

```python
my_cube.metrics
my_cube.attributes
my_cube.attr_elements
```

Then, choose those elements by passing their IDs to the `my_cube.apply_filters()` method. To see the chosen elements, call `my_cube.selected_attributes, my_cube.selected_metrics, my_cube.selected_attr_elements`. To clear any active filters, call `my_cube.clear_filters()`.

```python
my_cube.apply_filters(
    attributes=["A598372E11E9910D1CBF0080EFD54D63", "A59855D811E9910D1CC50080EFD54D63"],
    metrics=["B4054F5411E9910D672E0080EFC5AE5B"],
    attr_elements=["A598372E11E9910D1CBF0080EFD54D63:Los Angeles", "A598372E11E9910D1CBF0080EFD54D63:Seattle"])
my_cube.selected_attributes
my_cube.selected_metrics
my_cube.selected_attr_elements

df = my_cube.to_dataframe()
```

If you need to exclude specific attribute elements, pass the `operator="NotIn"` parameter to the `apply_filters()` method.

```python
my_cube.apply_filters(
    attributes=["A598372E11E9910D1CBF0080EFD54D63", "A59855D811E9910D1CC50080EFD54D63"],
    metrics=["B4054F5411E9910D672E0080EFC5AE5B"],
    attr_elements=["A598372E11E9910D1CBF0080EFD54D63:Los Angeles", "A598372E11E9910D1CBF0080EFD54D63:Seattle"],
    operator="NotIn")
df = my_cube.to_dataframe()
```

## Export Data into MicroStrategy with Datasets
### Create a New Dataset
With **mstrio-py** you can create and publish single or multi-table Datasets. This is done by passing Pandas DataFrames to the `Dataset` constructor which translates the data into the format needed by MicroStrategy.

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

By default `Dataset.create()` will create a Dataset, upload the data to the Intelligence Server and publish it. If you just want to _create_ the Dataset and upload the row-level data but leave it unpublished, use `Dataset.create(auto_publish=False)`. If you want to _create_ an empty Dataset, use `Dataset.create(auto_upload=False, auto_publish=False)`. Skipped actions can be performed later using `Dataset.update()` and `Dataset.publish()` methods.

When using `Dataset.add_table()`, Pandas data types are mapped to MicroStrategy data types. By default, numeric data (integers and floats) are modeled as MicroStrategy Metrics and non-numeric data are modeled as MicroStrategy Attributes. This can be problematic if your data contains columns with integers that should behave as Attributes (e.g. a row ID), or if your data contains string-based, numeric-_looking_ data which should be Metrics (e.g. formatted sales data: `["$450", "$325"]`). To control this behavior, provide a list of columns that you want to convert from one type to another.
```python
ds.add_table(name="Stores", data_frame=stores_df, update_policy="add",
             to_attribute=["store_id"])

ds.add_table(name="Sales", data_frame=sales_df, update_policy="add",
             to_attribute=["store_id"],
             to_metric=["sales_fmt"])
```
It is also possible to specify where the Dataset should be created by providing a folder ID in `Dataset.create(folder_id=folder_id)`.

After creating the Dataset, you can obtain its ID using `Datasets.dataset_id`. This ID is needed for updating the data later.

### Update a Dataset
When the source data changes and users need the latest data for analysis and reporting in MicroStrategy, **mstrio-py** allows you to update the previously created Dataset.
```python
from mstrio.dataset import Dataset
ds = Dataset(connection=conn, dataset_id=dataset_id)
ds.add_table(name="Stores", data_frame=stores_df, update_policy="update")
ds.add_table(name="Sales", data_frame=sales_df, update_policy="upsert")
ds.update()
```
The `update_policy` parameter controls how the data in the Dataset gets updated. Currently supported update operations are `add` (inserts entirely new data), `update` (updates existing data), `upsert` (simultaneously updates existing data and inserts new data), and `replace` (truncates and replaces the data).

By default `Dataset.update()` will upload the data to the Intelligence Server and publish the Dataset. If you just want
to update the Dataset but not publish the row-level data, use `Dataset.update(auto_publish=False)`. To publish it later, use `Dataset.publish()`.

By default, the raw data is transmitted to the server in increments of 100,000 rows. For very large datasets (>1 GB) it is beneficial to increase the number of rows transmitted to the Intelligence Server with each request. Do this with the `chunksize` parameter:
```python
ds.update(chunksize=500000)
```

### Certify a dataset
Use `Dataset.certify()` to certify / decertify an existing dataset.

### Limitations
Updating Datasets that were **not** created using the MicroStrategy REST API is not possible. This applies for example to Cubes created via MicroStrategy Web client.

# More Resources
- [Tutorials for mstrio][mstr_datasci_comm]
- [mstrio-py online documentation][mstrio_py_doc]
- [Check out mstrio for R][r_github]
- [Learn more about the MicroStrategy REST API][mstr_rest_docs]
- [MicroStrategy REST API demo documentation][mstr_rest_demo]

# Other
"Jupyter" and the Jupyter logos are trademarks or registered trademarks of NumFOCUS.


[pypi_archive]: <https://pypi.org/project/mstrio-py/#history>
[py_github]: <https://github.com/MicroStrategy/mstrio-py>
[r_github]: <https://github.com/MicroStrategy/mstrio>
[mstr_datasci_comm]: <https://community.microstrategy.com/s/topic/0TO44000000AJ2dGAG/python-r-u108>
[mstrio_py_doc]: <http://www2.microstrategy.com/producthelp/Current/mstrio-py/>
[mstr_rest_demo]: <https://demo.microstrategy.com/MicroStrategyLibrary/api-docs/index.html>
[mstr_rest_docs]: <https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API.htm>
[mstr_help_docs]: <https://www2.microstrategy.com/producthelp/current/MSTR-for-Jupyter/Content/mstr_for_jupyter.htm>
[cors_manual]: <https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/EmbeddingSDK/Content/topics/EnableCORS.htm>
[same_site_manual]: <https://community.microstrategy.com/s/article/Chrome-v80-Cookie-Behavior-and-the-impact-on-MicroStrategy-Deployments?language=undefined&t=1581355581289>
[python_venv]: <https://docs.python.org/3/tutorial/venv.html>
[release_notes]: <https://github.com/MicroStrategy/mstrio-py/blob/master/NEWS.md>
[logo]: <https://github.com/MicroStrategy/mstrio-py/blob/master/mstr-logo.png?raw=true>
