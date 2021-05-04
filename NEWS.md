# Changelog

## 11.3.1.101 - 2021/04/30

### Major changes

* added `SuperCube` and `OlapCube` classes in `mstrio.application_objects.datasets` subpackage
* added `list_all_cubes`, `load_cube`, `list_super_cubes`, `list_olap_cubes` functions that allow searching available cubes by name and construct precise objects
* added possibility to alter `name`, `description`, `abbreviation` properties of cubes
* added more `Cube` object attributes similar to other MSTR objects
* added `user_id`, `user_full_name`, `user_initials` attributes to `Connection` class
* added missing parameters `trust_id` and `database_auth_login` in `user.alter()` method

### Bug fixes

* fixed `KeyError` when trying to connect on certain environments #49
* fixed initializing `Cube` object when cube Server available #46
* fixed `instance_id` attribute not being filled in `Cube` class #39

### Deprecated

* `mstrio.admin` subpackage is deprecated and its modules are moved according to new structure
* `mstrio.cube` and `mstrio.dataset` are deprecated and are superceded by `OlapCube` and `SuperCube` from `application_objects.datasets` subpackage
* `mstrio.report` and `mstrio.library` modules are deprecated and are moved to `application_objects` subpackage
* `date_modified` and `id` replace parameters/attributes `cube_id` and `last_modified` in new `SuperCube` and `OlapCube` classes
* `project_id` and `project_name` parameters/attributes are deprecated accross the package in favor of `application_id` and `application_name`


## 11.3.0.2 - 2021/01/11

* updated example links in readme.md file

## 11.3.0.1 - 2020/12/18

### Major changes

#### Python Code

* added `admin` subpackage with `user`, `usergroup`, `application`,
  `security_role`, `privilege`, `schedule`, `subscription`,
  `subscription_manager` modules allowing to administer those objects on the
  MicroStrategy environment, notably:
  * browse and view
  * modify
  * create and delete
  * manage privileges and object permissions
* added `server` module allowing to administer the cluster, change node
  settings, manage services and more
* added support for viewing, comparing, modifying, exporting/importing
  application and I-Server settings via the `application` module
* added `user_connections` module allowing to manage active user sessions
* added `library` module allowing to view and manage users' libraries
* added `dossier` and `document` modules
* added support for **proxy** configuration in `Connection` class
* added `Connection.select_project()` method allowing to change current project
* changed `Connection` object constructor to not require setting `project_id` or
  `project_name`

#### GUI

* added UI-generated **Custom Jupyter Cells** which allow for Python
  Code edition and use mainly via UI, Buttons and Interactive Button-like Elements

### Bug fixes

* improved GUI stability in Data Modelling
* improved Safari compatibility
* resolved import issues with OLAP cubes
* resolved edge case general issues in import and export

### Deprecated

* `add`, `update`, `upsert` update methods are not supported anymore when
  overwriting cube and will throw `ValueError` exception

## 11.2.2.1 - 2020/08/04

### Major changes

* improved performance for downloading Reports / Cubes with view filter
* automatically remove the `Row Count` column from the imported datasets
* extend `Connection` class with the `identity_token` param to allow for
  delegated authentication
* added support for operator `NotIn` in view filter
* added `instance_id` parameter in the `Report` / `Cube` constructors to utilize
  existing instance on I-Server
* limited HTTP sessions by reusing the underlying TCP/IP connection
* added new methods to `Cube` class: `update` and `save_as`
* improved overall user experience in the GUI

### Bug fixes

* fixed critical compatibility issue with 11.1.x environments
* various UI fixes

## 11.2.2 - 2020/06/24 [YANKED]

* Release has been yanked due to compatibility issue with 11.1.x environments

## 11.2.1 - 2020/03/27

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

## 11.2.0 - 2019/12/10

* optimized downloading speed for filtered Reports
* improved performance when downloading unfiltered Cubes / Reports
* improved performance when filtering by attributes and metrics

## 11.1.4 - 2019/10/29

### Major changes

* added `Cube` and `Report` classes to provide more flexibility when interacting
  with Cubes and Reports. These new classes provide the ability to select
  attributes, metrics, and attribute elements before importing them to Python as
  `pandas` DataFrames
* added `Dataset` class that allows defining and creating multi-table cubes from
  multiple DataFrames, with improved data upload scalability, and the ability to
  define the Dataset within a specific folder
* introduced graphical user interface to access the MicroStrategy environment
  using interactive Jupyter Notebook add-in

### Bug fixes

* ensured session cookies are passed when closing the connection

## 10.11.1 - 2019/09/27

* minor bug fixes

## 10.11.0 - 2018/07/25

* initial PyPI release (25 July 2018)
