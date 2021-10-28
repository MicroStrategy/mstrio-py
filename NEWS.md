# Changelog

## 11.3.3.102 - 2021/10/29

### Major changes
- added `CacheUpdateSubscription` class to `subscription` module

### Minor changes
- return specific type of subscription object when using `list_subscriptions`
- inner structure of `mstrio.distribution_services.subscription` was changed.
  Please make sure to import from `mstrio.distribution_services` or
  `mstrio.distribution_services.subscription` at most, since anything deeper is
  considered internal implementation details and not guaranteed to remain
  stable
- added arguments `user` and `user_group` to function `list_security_filters` to
  allow filtering results by user or user group
- added method `list_security_filter` and property `security_filters` to
  `UserGroup` class
- added method `list_security_filter` and property `security_filters` to
  `User` class

## 11.3.3.101 - 2021/09/24

### Major changes

- added `job_monitor` module with `list_jobs`, `kill jobs`, `kill_all_jobs`
  functions and `Job` class
- added `Object` class in `mstrio.object_management` subpackage to allow
  object management
- added `list_objects` function to allow listing objects by type
- added `Folder` class in `mstrio.object_management` subpackage to allow
  folder management
- added `list_folders`, `get_my_personal_objects_contents`,
  `get_predefined_folder_contents` functions to allow listing folders and
  getting contents of particular folders
- added enum `PredefinedFolders` with all available values of pre-defined
  folders
- added `quick_search`, `quick_search_from_object`, `get_search_suggestions`
  functions that use the stored results of the Quick Search engine to return
  search results and suggestions
- added `full_search` which uses `start_full_search` and `get_search_results`,
  that can be used to search the metadata for objects in a specific project that
  match specific search criteria
- added `list_dependencies` and `list_dependents` methods to most of the classes
  that provide information about dependence of an object
- added `Shortcut`class in `mstrio.object_management` subpackage

### Minor changes

- changed `Subscription` class to now use `Content` and `Delivery` objects
  instead of dicts
- changed owner field of `Subscription` to `User` objects
- changed all date fields to `datetime` objects
- improved filtering performance in listing objects functions
- Term `application` deprecated (see section 'Deprecated'), and renamed in
method names, method arguments, file names, class names to `project` (see
notebooks in 'examples', and demo scripts in 'demos' for details). Examples:
  - `list_applications()` renamed to `list_projects()`
  - `application`, `application_name`, `application_id` renamed to
  `project`, `project_name`, `project_id`
  - `mstrio.server.application` renamed to `mstrio.server.project`
  - `Application` renamed to `Project`
- Updated notebook examples and demo scripts in 'examples' and 'demos' folders
- changed `certified_info` field of `Report` and `Document` from dict to
  `CertifiedInfo` object
- added parameter `propagate_to_children` to methods in `ACLMixin` class
- `acg` property of an object now use a `Rights` enum
- `acl` property of an object now use a new class `ACE`
- `extended_type` property of an object now use a `ExtendedType` enum

### Bug fixes

- fixed server memory settings issues when converting
- fixed server settings configuration for I-Server version prior to 11.3.0
- fixed bug where list_subscription is limiting data to 1000 results only
- fixed `Styler` object being returned instead of `DataFrame` in
  `nodes_topology` and `services_topology` methods in `Cluster` class

### Deprecated
- `application`, `application_name`, `application_id` parameters/attributes
- functions having a term 'application' in their definition
- modules having a term 'application' in their name
- class names having a term 'application' in their definition
**In all of above-mentioned changes, a new term is 'project'**
- `mstrio.browsing` is deprecated and is superceded
  with `mstrio.object_management.search_operations` subpackage,
- `SearchType` enum is now `SearchPattern`

## 11.3.2.101 - 2021/06/30

### Major changes

- added `Schedule` class in `mstrio.distribution_services.schedule` subpackage
- added `ScheduleTime` class in `mstrio.distribution_services.schedule`
  subpackage, local object used for specifying time related properties of
  schedule
- added `Event` class in `mstrio.distribution_services.event` subpackage
- changed `Subscription` class to now use `Schedule` objects
- added datasources subpackage with `Dbms`, `DatabaseConnections`,
  `DatasourceInstance`, `DatasourceLogin`, `DatasourceMap` classes covering
  database management functionality
- added functions `list_available_dbms`, `list_datasource_connections`,
  `list_datasource_instances`, `list_datasource_logins`,
  `list_datasource_mappings` to list all datasource related objects
- added `database_connections` module allowing to browse and manage database
  connections on the environment
- added ACL management functionality for all supporting objects by adding
  `list_acl`, `acl_add`, `acl_remove`, `acl_alter` methods
- added `SecurityFilter` class and function `list_security_filters` in
  `mstrio.access_and_security.security_filter` subpackage
- added `Qualification` class in `mstrio.access_and_security.security_filter`
  subpackage which is an object used to represent qualification of security
  filter
- added classes `PredicateBase`, `PredicateForm`, `PredicateElementList`,
  `PredicateFilter`, `PredicateJointElementList` and `LogicOperator` in
  `mstrio.access_and_security.security_filter` subpackage to represent
  predicates which can be used in creation of qualification for security filter
- added classes `ParameterBase`, `ConstantParameter`,
  `ObjectReferenceParameter`, `ExpressionParameter`, `PromptParameter`,
  `DynamicDateTimeParameter` and `ConstantArrayParameter` in
  `mstrio.access_and_security.security_filter` subpackage to represent
  parameters used in `AttributeForm`

### Bug fixes

- fixed urllib3 dependency installing incompatible version
- fixed GUI login to be case-insensitive

### Deprecated

- `mstrio.admin.schedule` is deprecated and superceded with
  `mstrio.distribution_services.schedule` subpackage
- `schedules` replace argument `schedules_id` in `create` and `alter`, methods
  of `Schedule` class
- `mstrio.distribution_services.schedule.ScheduleManager` is now deprecated,
  use `mstrio.distribution_services.schedule.list_schedules()` instead
- removed features deprecated in release 11.3.1.101 and aliases allowing for
  backward compatibility

## 11.3.1.102 - 2021/05/28

### Major changes

- changed files structure to organize the modules in clean and readable way
- added or improved type hints across the codebase
- added Enums: `PrivilegeMode`, `IdleMode`, `GroupBy`, `ServiceAction`,
  `Rights` and `Permissions`
- implemented `Node` class to be used for node management in place of a raw dict
- added `CubeCache` class in `mstrio.application_objects.datasets` subpackage
- updated method `load_cube` to load cube by name
- added functions `list_cube_caches` , `delete_cube_caches` and
  `delete_cube_cache`
- added methods `create`, `update`, `get_sql_view` and `publish` for class
  OlapCube
- added method `unpublish` available for classes `OlapCube` and `SuperCube`
- added `list_reports` function to `Report` module
- added `alter` and `list_properties` methods to `Report` class

### Bug fixes

- fixed custom cell colapsing at re-run at certain conditions
- fixed wrong object type for `Entity.__init__()` method
- fixed `KeyError:'body'` when executing `update_properties` on an object
- fixed `TypeError: unhashable type:'dict'` after accessing `attr_elements` of
  `Cube`
- fixed `mstrio.dataset` module `publish` method sending requests too frequently
  to the REST API

### Deprecated

- `id` replaces field `report_id` in `Report` class

## 11.3.1.101 - 2021/04/30

### Major changes

- added `SuperCube` and `OlapCube` classes in
  `mstrio.application_objects.datasets` subpackage
- added `list_all_cubes`, `load_cube`, `list_super_cubes`, `list_olap_cubes`
  functions that allow searching available cubes by name and construct precise
  objects
- added possibility to alter `name`, `description`, `abbreviation` properties of
  cubes
- added more `Cube` object attributes similar to other MSTR objects
- added `user_id`, `user_full_name`, `user_initials` attributes to `Connection`
  class
- added missing parameters `trust_id` and `database_auth_login` in
  `user.alter()` method

### Bug fixes

- fixed `KeyError` when trying to connect on certain environments #49
- fixed initializing `Cube` object when cube Server available #46
- fixed `instance_id` attribute not being filled in `Cube` class #39

### Deprecated

- `mstrio.admin` subpackage is deprecated and its modules are moved according to
  new structure
- `mstrio.cube` and `mstrio.dataset` are deprecated and are superceded by
  `OlapCube` and `SuperCube` from `application_objects.datasets` subpackage
- `mstrio.report` and `mstrio.library` modules are deprecated and are moved to
  `application_objects` subpackage
- `date_modified` and `id` replace parameters/attributes `cube_id` and
  `last_modified` in new `SuperCube` and `OlapCube` classes
- `project_id` and `project_name` parameters/attributes are deprecated accross
  the package in favor of `application_id` and `application_name`

## 11.3.0.2 - 2021/01/11

- updated example links in readme.md file

## 11.3.0.1 - 2020/12/18

### Major changes

#### Python Code

- added `admin` subpackage with `user`, `usergroup`, `application`,
  `security_role`, `privilege`, `schedule`, `subscription`,
  `subscription_manager` modules allowing to administer those objects on the
  MicroStrategy environment, notably:
  - browse and view
  - modify
  - create and delete
  - manage privileges and object permissions
- added `server` module allowing to administer the cluster, change node
  settings, manage services and more
- added support for viewing, comparing, modifying, exporting/importing
  application and I-Server settings via the `application` module
- added `user_connections` module allowing to manage active user sessions
- added `library` module allowing to view and manage users' libraries
- added `dossier` and `document` modules
- added support for **proxy** configuration in `Connection` class
- added `Connection.select_project()` method allowing to change current project
- changed `Connection` object constructor to not require setting `project_id` or
  `project_name`

#### GUI

- added UI-generated **Custom Jupyter Cells** which allow for Python
  Code edition and use mainly via UI, Buttons and Interactive Button-like
  Elements

### Bug fixes

- improved GUI stability in Data Modelling
- improved Safari compatibility
- resolved import issues with OLAP cubes
- resolved edge case general issues in import and export

### Deprecated

- `add`, `update`, `upsert` update methods are not supported anymore when
  overwriting cube and will throw `ValueError` exception

## 11.2.2.1 - 2020/08/04

### Major changes

- improved performance for downloading Reports / Cubes with view filter
- automatically remove the `Row Count` column from the imported datasets
- extend `Connection` class with the `identity_token` param to allow for
  delegated authentication
- added support for operator `NotIn` in view filter
- added `instance_id` parameter in the `Report` / `Cube` constructors to utilize
  existing instance on I-Server
- limited HTTP sessions by reusing the underlying TCP/IP connection
- added new methods to `Cube` class: `update` and `save_as`
- improved overall user experience in the GUI

### Bug fixes

- fixed critical compatibility issue with 11.1.x environments
- various UI fixes

## 11.2.2 - 2020/06/24 [YANKED]

- Release has been yanked due to compatibility issue with 11.1.x environments

## 11.2.1 - 2020/03/27

### Major changes

- introduced functionality for updating existing Cubes
- improved fetching performance by up to 50%
- added support for cross-tabbed Reports
- added support for Reports with subtotals
- added basic support for Reports with attribute forms
- extended `Dataset` class with the `certify()` method
- implemented asynchronous download of Cubes and Reports
- applied revamped MicroStrategy REST API import-related endpoints
- reworked GUI’s data modeling functionality

### Bug fixes

- fixed issues with Cube / Report filtering during import
- improved user experience for the GUI's login page
- added handling of various forms of environment's base URL
- resolved issues with importing / exporting Datasets containing special
  characters

## 11.2.0 - 2019/12/10

- optimized downloading speed for filtered Reports
- improved performance when downloading unfiltered Cubes / Reports
- improved performance when filtering by attributes and metrics

## 11.1.4 - 2019/10/29

### Major changes

- added `Cube` and `Report` classes to provide more flexibility when interacting
  with Cubes and Reports. These new classes provide the ability to select
  attributes, metrics, and attribute elements before importing them to Python as
  `pandas` DataFrames
- added `Dataset` class that allows defining and creating multi-table cubes from
  multiple DataFrames, with improved data upload scalability, and the ability to
  define the Dataset within a specific folder
- introduced graphical user interface to access the MicroStrategy environment
  using interactive Jupyter Notebook add-in

### Bug fixes

- ensured session cookies are passed when closing the connection

## 10.11.1 - 2019/09/27

- minor bug fixes

## 10.11.0 - 2018/07/25

- initial PyPI release (25 July 2018)
