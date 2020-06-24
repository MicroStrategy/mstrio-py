## mstrio-py 11.2.2
### Major changes
* improved performance for downloading Reports / Cubes with view filter
* automatically remove the `Row Count` column from the imported datasets
* extend `Connection` class with the `identity_token` param to allow for delegated authentication
* added support for operator `NotIn` in view filter
* added `instance_id` parameter in the `Report` / `Cube` constructors to utilize existing instance on I-Server
* limited HTTP sessions by reusing the underlying TCP/IP connection
* added new methods to `Cube` class: `update` and `save_as`
* improved overall user experience in the GUI

### Bug fixes
* various UI fixes


## mstrio-py 11.2.1
### Major changes
* introduced functionality for updating existing Cubes
* improved fetching performance by up to 50%
* added support for cross-tabbed Reports
* added support for Reports with subtotals
* added basic support for Reports with attribute forms
* extended `Dataset` class with the `certify()` method
* implemented asynchronous download of Cubes and Reports
* applied revamped MicroStrategy REST API import-related endpoints
* reworked GUI’s data modeling functionality

### Bug fixes
* fixed issues with Cube / Report filtering during import
* improved user experience for the GUI's login page
* added handling of various forms of environment's base URL
* resolved issues with importing / exporting Datasets containing special characters


## mstrio-py 11.2.0
* optimized downloading speed for filtered Reports
* improved performance when downloading unfiltered Cubes / Reports
* improved performance when filtering by attributes and metrics


## mstrio-py 11.1.4
### Major changes
* added `Cube` and `Report` classes to provide more flexibility when interacting with Cubes and Reports. These new classes provide the ability to select attributes, metrics, and attribute elements before importing them to Python as `pandas` DataFrames
* added `Dataset` class that allows defining and creating multi-table cubes from multiple DataFrames, with improved data upload scalability, and the ability to define the Dataset within a specific folder
* introduced graphical user interface to access the MicroStrategy environment using interactive Jupyter Notebook add-in

### Bug fixes
* ensured session cookies are passed when closing the connection


## mstrio-py 10.11.1
* minor bug fixes


## mstrio-py 10.11.0
* initial PyPI release (25 July 2018)
