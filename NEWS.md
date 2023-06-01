# Changelog

## 11.3.10.101 - 2023/06/02

### Major changes
- updated `create` method of `OlapCube` class to support new parameters:
  `template`, `filter`, `options`, `advanced_properties`, `time_based_settings`,
  `show_expression_as` and `show_filter_tokens`
- updated `alter` method of `OlapCube` class to allow altering new parameters:
  `template`, `filter`, `options` and `time_based_settings`
- added `set_partition_attribute`, `remove_partition_attribute` and `list_attribute_forms`
  methods to `OlapCube` class to allow managemenet of partition attribute and observing
  attributes forms
- added `list_vldb_settings`, `alter_vldb_settings` and `reset_vldb_settings`
  methods to `OlapCube` class to allow management of VLDB settings

### Deprecated
- `update` method of `OlapCube` class is no longer supported, is superseded by `alter`
  method, and will be removed in the future
- `attributes`, `metrics` and `overwrite` parameters in `create` method of `OlapCube` class
  are no longer supported, are superseded by `template` parameter, and will be removed
  in the future

## 11.3.9.103 - 2023/05/05

### Major changes
- added `list_vldb_settings`, `alter_vldb_settings` and `reset_vldb_settings`
  methods to `DatasourceInstance` class and `Project` class to allow management
  of VLDB settings
- added `Driver` class and `list_drivers` function in `mstrio.datasources.driver`
  module to allow driver management
- added `Gateway` class and `list_gateways` function in `mstrio.datasources.gateways`
  module and `GatewayType` and `DBType` enums in `mstrio.datasources.helpers` to
  allow gateway management

### Minor changes
- updated `ipython` dependency version to 8.10.0
- added a `project_id` property for `Metric` instances
- fixed `is_logical_size_locked` for `LogicalTable` to be working as boolean
- fixed `list_logical_tables` function to return all tables if called without
  specifying `project_id` or `project_name`, unless limit argument is provided
- fixed `Attribute`, `Document`, `Fact`, `Filter`, `Metric`, `Transformation`,
  `IncrementalRefreshReport` classes to be initialized by name with 
  `SearchPattern.EXACTLY` instead of `SearchPattern.CONTAINS`
- fixed `list_objects` function to accept integer as input for `object_type` argument
- fixed `User.security_filters` property to always return all user's security filters
  from all loaded projects
- added `delivery_expiration_timezone` argument for `Subscription` class and its subclasses
  (supported from Update 10 environments)
- fixed `Attribute` objects always returning `None` for `hidden` field and fixed
  `alter` method to allow updating it
- added `SuperCubeAttribute`, `SupperCubeAttributeForm`, `SuperCubeFormExpression`
  classes in `mstrio.project_objects.datasets.super_cube` module to support attribute
  forms for `SuperCube`

## 11.3.9.101 - 2023/03/03

### Major changes
- added `HistoryListSubscription`, `FTPSubscription` and `FileSubscription`
  classes in `mstrio.distribution_services.subscription` package to allow
  management of new subscription types
- added `DynamicRecipientList` class in `mstrio_distribution_services.subscription`
  package to allow management of Dynamic Recipient Lists
- added `list_dynamic_recipient_lists` to allow listing dynamic recipient lists

### Minor changes

- added verification, when initializing `Report` object, if object is supported,
  currently supported are objects with subtypes: 768 - grid, 769 - graph 769,
  770 - engine, 774 - grid and graph, 778 - transaction, 781 - hyper card
- changed `list_reports` function to return only object supported by `Report` class
- added methods to convert connection from DSN to DSN-less format in classes
  `DatasourceInstance` and `DatasourceConnection`
- improved error messages when calling `list_dependents` and `list_dependencies`
  on unsupported objects
- added support for `Time` type to `SuperCube` class
- added `with` statement compatibility for `Connection` object
- added function `find_objects_with_id` in `mstrio.object_management.search_operations`
  to allow searching for object when knowing only its ID
- fixed listing and initialising by name documents and dossiers
  when name was longer than 30 characters
- fixed not being able to create `SuperCube` with update policy other than `replace`
- added checking during creation if `SuperCube` with given name already exists in a folder,
  and display an error if it does
- added support for Python 3.11
- fixed `Dossier` class to work properly when being initialised by name
- fixed `Project.alter` method
- fixed managing `Subscriptions` recipients to work properly with existing recipients
- fixed circular import of the `Device` module for `Contact` and `distribution_services`
- altered `attributes.py` code snippet to use `list_table_columns`
  and `list_logical_tables` methods from `table` module
- updated dependencies in `requirements.txt`
- fixed `list_objects` method to work properly for different domains
- fixed and combined `_update_acl` and `_modify_rights` methods, added `modify_rights` method
- added `Service` and `ServiceWithNode` classes in `mstrio.server.node` module

## 11.3.7.103 - 2022/11/11

### Major changes

- added `ContentCache` class in `mstrio.project_objects.content_cache` module to allow Document,
  Dossier and Report cache management

### Minor changes

- added `list_properties` and `list_available_schedules` methods for
  `mstrio.project_objects.document` module
- added `list_properties` method for `mstrio.project_objects.dossier` module
- added `VisualizationSelector`, `PageSelector`, `PageVisualization`, `ChapterPage` and
  `DossierChapter` classes in `mstrio.project_objects.dossier` module
- added cache management methods for `mstrio.project_objects.document` module by inheriting from
  `ContentCache` class
- added cache management methods for `mstrio.project_objects.dossier` module by inheriting from
  `ContentCache` class
- fixed `list_documents_across_projects` function to work properly when `to_dataframe` or
  `to_dictionary` parameters are set to `True`, also to not return an error when user has no access
   to one of the projects but to skip that project instead
- fixed `list_dossiers_across_projects` function to work properly when `to_dataframe` or
  `to_dictionary` parameters are set to `True`, also to not return an error when user has no access
   to one of the projects but to skip that project instead
- added `export_sql_view` method to `SuperCubes` to allow extraction of sql statement
- increased chunk size for fetching projects
- fixed importing and exporting project settings from/to CSV file
- fixed `list_physical_tables` when logical table aliases are in the project
- fixed `project_id` parameter not being used in `list_logical_tables`
- added two methods to `User` class: `User.to_dataframe_from_list()` and `User.to_csv_from_list()`
- fixed altering `table_prefix` in `DatasourceInstance`
- fixed getting `Subscriptions` with `refresh_condition`

### Deprecated

- `mstrio.distribution_services.contact` module is no longer supported and is moved to
  `mstrio.users_and_groups` subpackage
- `mstrio.distribution_services.contact_group` module is no longer supported and is moved to
  `mstrio.users_and_groups` subpackage
- `mstrio.access_and_security.security_filter` module is no longer supported and is replaced by
  `mstrio.modeling.security_filter` and `mstrio.modeling.expression` subpackages

## 11.3.6.103 - 2022/08/12

### Major changes

- added `Transformation`, `TransformationAttribute` and `TransformationAttributeForm` classes in
  `mstrio.modeling.schema.transformation` subpackage to allow transformation management
- added `list_transformations` to allow listing for transformations
- added `DefaultSubtotals`, `Dimensionality`, `DimensionalityUnit`, `FormatProperty`, `Metric`,
  `MetricFormat` and `Threshold` classes in `mstrio.modeling.metric` subpackage to allow
  metric management
- added `list_metrics` to allow listing for metrics

### Minor changes

- added `list_locales` to `mstrio.datasource.datasource_map` module to allow listing locales
- added `DatasourceMap.alter()` method to allow altering user-defined connection mapping
- added `list_warehouse_tables()` method to `mstrio.modeling.schema.table.warehouse_table` module
  to allow listing all warehouse tables from all available datasources

### Deprecated

- `mstrio.distribution_services.contact` module is deprecated and is moved to
  `mstrio.users_and_groups` subpackage
- `mstrio.distribution_services.contact_group` module is deprecated and is moved to
  `mstrio.users_and_groups` subpackage
- `mstrio.access_and_security.security_filter` subpackage is deprecated and replaced by
  `mstrio.modeling.security_filter` and `mstrio.modeling.expression` subpackages

## 11.3.6.102 - 2022/07/15

### Major changes

- added `Filter` class in `mstrio.modeling.filter` subpackage to allow filter
  management
- added `list_filters` to allow listing of filters
- turned off certificate verification when using `get_connection`

### Minor changes

- added possibility for passing `project_name` instead of `project_id` in the functions that were allowing only `project_id` before.

## 11.3.6.101 - 2022/06/24

### Major changes

- added `LogicalTable`, `PhysicalTable` and `WarehouseTable` classes in
  `mstrio.modeling.schema.tables` module to allow table management.
- added `list_logical_tables()`, `list_physical_tables()` and
  `list_datasource_warehouse_tables()`, `list_namespaces()` to allow
  for listing of and searching the project for specific tables.

### Minor changes

- added `search_pattern` and `project_id` parameters in object listing functions
- added `move` methods to `Folder`, `Object`, `SecurityFilter`, `Attribute`, `Fact`, `UserHierarchy`, `Report`, `Shortcut`, `SearchObject`, `Document` and `Dossier` to allow moving objects between folders
- added `create_copy` method to `SecurityFilter`, `Attribute`, `Fact`, `UserHierarchy`, `Report`, `Shortcut`, `SearchObject`, `Document` and `Dossier`

### Deprecated

- `name_begins` parameter is deprecated in functions listing cubes and reports
  in favour of `name` parameter

## 11.3.5.103 - 2022/05/20

### Major changes

- added `Fact` class in `mstrio.modeling.schema.fact` subpackage to allow fact
  management
- added `list_facts` to allow listing of facts

## 11.3.5.102 - 2022/04/22

### Major changes

- added `Attribute` class in `mstrio.modeling.schema.attribute` subpackage
  to allow attribute management
- added `AttributeForm` class in `mstrio.modeling.schema.attribute_form` subpackage
  to allow attribute form management
- added `list_attributes` to allow listing of attributes
- added `list_functions` in `mstrio.modeling.expression` subpackage
  to allow listing of functions
- added `fact_expression`, `expression`, `expression_nodes`, `parameters` and
  `dynamic_date_time` modules in `mstrio.modeling.expression` subpackage to allow
  management of fact expressions

### Minor changes

- Changed `ExecutionMode` elements from `ASYNCH_CONNECTION` to `ASYNC_CONNECTION` and from `ASYNCH_STATEMENT` to `ASYNC_STATEMENT`
- refactored `examples` into `code_snippets` folder, with changes to make them more
  easily usable in MicroStrategy Workstation
- renamed folder `workstation_demos` into `workflows`

## 11.3.5.101 - 2022/03/25

### Major changes

- added `SchemaManagement` class in `mstrio.modeling` subpackage to allow
  schema management
- added `UserHierarchy` class in `mstrio.modeling` subpackage to allow
  user hierarchy management
- `Migration` module is available now as a Functionality Preview
- added function `list_user_hierarchies` to allow listing of objects of newly created class `UserHierarchy`

## 11.3.4.101 - 2022/01/28

### Major changes

- added `Contact` class in `mstrio.distribution_services.contact` subpackage to allow
  contact management
- added `ContactGroup` class in `mstrio.distribution_services.contact_group` subpackage
  to allow contact group management
- added `Device` class in `mstrio.distribution_services.device` subpackage to allow
  device management
- added `Transmitter` class in `mstrio.distribution_services.transmitter` subpackage
  to allow transmitter management
- added functions `list_contact`, `list_contact_groups`, `list_devices`,
  `list_transmitters` to allow listing of objects of newly created classes
- added `Migration` class in `mstrio.object_management.migration` for migration related
  functionalities. This feature is still work in progress, and it will be completed by 03.2022.
- added `PackageConfig` class in `mstrio.object_management.migration` with supporting
  `PackageSettings` and `PackageContentInfo` used for configurating migration
- extended `Event` class in `mstrio.distribution_services.event` with functionalities to
  create, update and delete events.

### Minor changes

- added delete functionality to `Document`, `Dossier` and `Report` classes
- change `Connection` object to automatically renew the connection or reconnect
  when the session becomes inactive if authenticated with login and password
- deprecate `Connection` object attribute `session` and renamed it into `_session`,
  making it private
- add the following HTTP requests methods to `Connection` object:
  `get`, `head`, `post`, `put`, `delete`, `patch`

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

- fixed custom cell collapsing at re-run at certain conditions
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
- `project_id` and `project_name` parameters/attributes are deprecated across
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
