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

### Proxy

Optionally, proxy settings can be set for the MicroStrategy `Connection` object.

```python
proxies = {'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'}
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, proxies=proxies)
```

User can also specify username and password in `proxies` parameter to use HTTP Basic Auth:

```python
proxies = {'http': 'http://<username>:<password>@<ip_address>:<port>/'}
conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, proxies=proxies)
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

After creating the Dataset, you can obtain its ID using `Dataset.dataset_id`. This ID is needed for updating the data later.

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

## Using mstrio as a MicroStrategy Intelligence Server administration tool
- Application management module (see [examples](examples/application_mgmt.py))
- Server management module (see [examples](examples/server_mgmt.py))
- User and Usergroup management modules (see [examples](examples/user_mgmt.py))
- Subscription and Schedules management modules (see [examples](examples/subscription_mgmt.py))
- Document and Dossiers in User Library modules (see [examples](examples/user_library.py))
