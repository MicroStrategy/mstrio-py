## mstrio-py 11.2.1
### Major changes
* introduced functionality for updating existing cubes
* improved fetching performance by up to 50%
* added support for cross-tabbed reports
* added support for reports with subtotals
* added basic support for reports with attribute forms
* extended `Dataset` class with the `certify()` method
* implemented asynchronous download of cubes and reports
* applied revamped MicroStrategy REST API import-related endpoints
* reworked GUI’s data modeling functionality

### Bug fixes
* fixed issues with cube / report filtering during import
* improved user experience for the GUI's login page
* added handling of various forms of environment's base URL
* resolved issues with importing / exporting datasets containing special characters


## mstrio-py 11.2.0
* optimized downloading speed for filtered reports
* improved performance when downloading unfiltered cubes / reports
* improved performance when filtering by attributes and metrics


## mstrio-py 11.1.4
### Major changes
* added `Cube` and `Report` classes to provide more flexibility when interacting with cubes and reports. These new classes provide the ability to select attributes, metrics, and attribute elements before importing them to Python as `pandas` data frames
* added `Dataset` class that allows defining and creating multi-table cubes from multiple data frames, with improved data upload scalability, and the ability to define the dataset within a specific folder
* introduced graphical user interface to access the MicroStrategy environment using interactive Jupyter Notebook add-in

### Bug fixes
* ensured session cookies are passed when closing the connection


## mstrio-py 10.11.1
* minor bug fixes


## mstrio-py 10.11.0
* initial PyPI release (25 July 2018)
