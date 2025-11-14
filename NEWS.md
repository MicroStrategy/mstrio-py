# Changelog

## 11.5.11.101 - 2025/11/14

### Minor changes

- added a set of `folder`-related parameters to filtering in listing and creation methods in majority of existing modules. Please read mstrio-py documentation or class-specific code snippets for details regarding their use.
- added `temporary_project_change` context-method to `Connection` class for ease of temporary project selection where keeping the old one long-term is important
- added `get_subfolders`, `traversal` and `traverse_folders` methods and `path` attribute to `Folder` class
- added option of initialization of `Folder` class by its name. Please read the documentation to learn about risks of this approach
- added argument `on_nodes` in `Project.is_loaded()` method to check status on specific nodes
- added argument `check_all_selected_nodes` in `Project.is_loaded()` method to use logic requiring all nodes to have the project loaded
- added `change_journal` property to view objects change journal entries
- added `list_change_journal_entries` function to list change journal entries across environment with specified filters
- added `purge_change_journal_entries` function to purge change journal entries in specified projects
- added `purge_change_journals` method to `Project` class to purge selected project change journal entries
- added `purge_all_change_journals` method to `Environment` class to purge change journal entries for every project
- added `purge_configuration_change_journals` method to `Environment` class to purge change journal entries for configuration objects
- added code snippet for mstrio-py's configuration, named `config_mgmt.py`
- added alias `disconnect` to method `close` on `Connection` object
- added alias `open` to method `connect` on `Connection` object
- added parameters `request_timeout` and `request_retry_on_timeout_count` on `Connection` object and methods `set_request_timeout` and `set_request_retry_on_timeout_count` as well as global config parameter `default_request_timeout` to be able to customize timeout and retry logic on mstrio-py's requests to REST API
- added `get_valid_page_by_elements` method to `Report` class to get all possible elements combinations for page by attributes
- added `valid_page_by_elements` property to `Report` class that stores valid page by elements combinations
- added `get_selected_page_by_elements` method to `Report` class to get list of page by elements based on valid combination
- enhanced `find_objects_with_id` method to be able to find any type of object by only ID, regardless whether it is configuration-level or project-level, in an efficient manner
- extended `Delivery.DeliveryMode` enum with `SHAREPOINT`, `ONEDRIVE` and `S3` entries for support in listing existing subscriptions

### Bug fixes

- fixed error when generating dataframe from prompted reports with metric names in rows
- fixed issue with field `ContentCache.warehouse_tables_used` storing incorrect data
- fixed defect that `Report.page_by_elements` returned maximum first 50 elements

### Breaking changes

- performed holistic cleanup and standardization regarding `folder`-related parameters and in turn removed and renamed obsolete `destination_folder_id` parameter from many methods. Please read mstrio-py documentation regarding what and how to do if you were using this parameter in your script

## 11.5.10.101 - 2025/10/17

### New features

- updated the `SearchObject` class
  - added method `alter`
  - released methods `create` and `run` for general availability
- added function `list_search_objects`
- added support for LDAP batch import management within `Environment` module
- added `delete_unused_managed_objects` method to `Project` class to allow deleting unused managed objects in a specific project

### Minor changes

- added arguments `description`, `query_modification_time`, `query_creation_time`, `owner`, `locale_id`, `include_hidden`, `include_subfolders`, `exclude_folders` and `scope` to `full_search` and `start_full_search` functions
- enabled passing `SearchObject` as content for object migration
- added `has_dependents` method to `DependenceMixin` class
- added `scope` parameter into `DependenceMixin`'s methods
- added support for `ObjectSubTypes` for `object_type` parameter in `list_objects`
- improved `Usage Remarks` section of mstrio-py's documentation with instructions on how to use `project`-related parameters, how to recognize types and subtypes and how to apply `**filters` in listing methods

### Deprecated

- `mstrio.project_objects.bots` module is superseded by
  `mstrio.project_objects.agents` and will be removed in the future

## 11.5.9.101 - 2025/09/19

### New features

- updated the `SearchObject` class
  - added properties related to search query
  - (preview) added methods `create` and `run`
- updated `Prompt` class to support general prompt management

### Minor changes

- updated `Project.load()` and `Project.unload()` to use more performant endpoint with server-wide operations
- improved answering prompts in Report, Document, Dashboard, Subscription

### Bug fixes

- fixed error in enum value name `ObjectSubTypes.SUPER_CUBE_IRR`
- restored several object types missing in Migration Package contents

### Deprecated

- `mstrio.project_objects.prompt` module is superseded by
  `mstrio.modeling.prompt` and will be removed in the future, after 1-year deprecation period

## 11.5.8.101 - 2025/08/22

### Minor changes

- added `is_run_in_workstation` method to `Connection` class to check if the script is run in Workstation context
- added prevention logic to `get_connection` method disallowing accidental connection closing
- added `model_list_vldb_settings` method to `Report`
- added possibility to alter `owner` field with `Object` class `alter()` method
- added possibility to set application name as Library title of `Application` object
- added `data_source_script_all_users.py` and `transaction_edit_users.py` script templates
- improved error message for server not supporting new Python Application Type during login
- added support for object subtypes corresponding to Bots 2.0, Universal Bots and Datamart Reports

### Bug fixes

- fixed `Metric` and `list_metrics` erroneously supporting Subtotal objects

## 11.5.7.101 - 2025/07/18

### New features

- added `duplicate` method to `Project` class that allows duplicating projects on the same environment
- added `ProjectDuplication`, `ProjectDuplicationStatus`, `DuplicationConfig`, `ProjectInfo` classes and `list_projects_duplications` function in mstrio.server.project to support project duplication process
- added `LibraryShortcut` class and `list_library_shortcuts` method in `Library` class to manage items as published to the user's Library
- added `get_library_shortcut` method in `Document`, `Dashboard` and `Bot` to manage published items

### Minor changes

- added Library-related methods to `Bot` class
- added code snippet `logging.py` to show how to add custom logging inside custom scripts
- updated `publish()` to use User Groups as a whole instead of each user separately
- updated `unpublish()` to enable unpublishing for User Groups

### Bug fixes

- fixed the `execute()` method for Subscription classes failing with multiple contents
- fixed `Document` class initialization incorrectly overwriting `project_id` with a one from `Connection` object
- fixed `list_bots` skipping Bots 2.0 and Universal Bots

## 11.5.6.101 - 2025/06/20

### Setup

- connections done through class `Connection` are now being identified by their own application type 76 "DssXmlApplicationPython"

### Minor changes

- added `working_set` and `max_search` optional parameters when creating `Connection` object
- added `get_api_token` method to `User` class to allow creating API Token by administrator for the user
- added filtering arguments in `list_shortcuts`
- added `invalidate` and bulk `invalidate_caches` methods for content cache management

### Bug fixes

- fixed `UserGroup.remove_all_users()` not working with empty User Groups
- fixed the issue with `ContentCache.list_caches()` not working when caches in the 'binary_definition, binary_data' format exist
- fixed Metric retrieval failing if series formatting is set
- fixed invalid `ScheduleEnums.YearlyPattern` enum throwing error for yearly schedule

## 11.5.5.101 - 2025/05/23

### New features

- `License` class refined with methods to support `compliance_check` and `audit`
- added `UserLicense` and `PrivilegeInfo` data classes in the license module

### Minor changes

- added methods `is_html_js_execution_enabled` and `set_html_js_execution_enabled` to Documents and Dashboards

### Bug fixes

- fixed the `alter()` method for Subscription classes failing with prompted content

## 11.5.4.101 - 2025/04/18

### New features

- added `License` class in `mstrio.server.license` subpackage to allow management of License

### Minor changes

- added support for logging in with API Token to `Connection` class
- added `application_id` argument to `Connection` class to allow logging in using custom application
- added `contact_address` argument to `User.add_address` method to allow passing `ContactAddress` object
- added `create_shortcut` method to all objects inheriting from `Entity`
- added `list_shortcuts` function in `mstrio.object_management.shortcut`
- added `alter` method to the `Shortcut` class
- added `what_can_i_do_with` helper method to `mstrio` root folder for helping with scripts creation

### Bug fixes

- fixed the `update()` method for `SuperCube` class, to correctly encode `Dataframe` chunks, when chunk size is smaller than the `Dataframe`
- fixed the `alter()` method for `SuperCube` and `OlapCube` classes not altering the `description` attribute
- added missing `list_projects` method inside `project.py` module, which was available only via `Environment.list_projects()` class method call

### Removed

- removed the obsolete `CONFIGURATION_AND_ALL_PROJECTS` value from `SearchDomain` enum

## 11.5.3.101 - 2025/03/21

### New features

- added `list_timezones` method and `TimeZone` class in `mstrio.server.timezone` to allow management of Time Zone internationalization objects

### Minor changes

- allowed to provide a string as a qualification when using the `create` and `alter` methods of the `Filter` and `SecurityFilter` classes
- added `alias` argument to `alter` method to `Project` class to allow setting project alias
- added `create_profile_folder` method to `User` class to allow creating profile folders
- added `username`, `user_id` and `object_name` properties to `Job` class
- added `create_copy` methods to `Subscription`, `Schedule`, `Transformation` `Event`
- updated `alter` method in a number of classes to allow changing ownership of their corresponding objects

### Bug fixes

- fixed an error with fetching all `Attribute` object properties listed in a project other than the one selected in the `Connection` object
- fixed `User.add_address()` erroneously allowing to not pass `name` or `address` arguments

### Removed

- removed the `Dossier` class as it is deprecated. From now on, please use only the `Dashboard` class instead

## 11.5.2.101 - 2025/02/14

### New features

- added `list_calendars` method and `Calendar` class in `mstrio.server.calendar` to allow management of Calendar internationalization objects
- added `list_palettes` method and `Palette` class in `mstrio.project_objects.palettes` to allow management of Color Palette objects
- added `answer_prompts` method to `Report`, `Document` and `Dashboard` classes to allow answering prompts
- added `list_related_subscriptions` method to `User`, `Dashboard`, `Report`, `Schedule` and `Event` classes to allow listing related subscriptions

### Minor changes

- added `delete` method to `SearchObject` and `Shortcut` classes
- added `delete_profile_folder` method to `User` class to allow deleting profile folders
- added `delete_profile` argument to `delete` method of `User` class to allow deleting user profiles along with the user
- added `default_email_address` and `email_device` arguments to `create` and `alter` methods of `User` class to allow setting default email address and email device
- changed output of `execute` method for `IncrementalRefreshReport` from None to `Job` object
- added `refresh_status` method for `Job` object to update status of already completed job
- added `list_palettes` method to `Document`

### Bug fixes

- fixed the `create` method for `Schedule` not correctly checking the `schedule_type` argument if it was passed as `str`
- fixed the issue requiring Architect privilege when fetching data about the cube
- fixed the `create` method for `EmailSubscription` not allowing the creation of subscriptions with multiple content objects

## 11.4.12.101 - 2024/12/13

### New features

- added `list_fences` method and `Fence` class in `mstrio.server.fence` subpackage to allow management of Fences
- added `list_cluster_startup_membership` and `update_cluster_startup_membership` methods to `Cluster` class in `mstrio.server.cluster` to allow management of cluster startup membership
- added arguments `add_to_cluster_startup` and `remove_from_cluster_startup` to `add_node` and `remove_node` methods in `Cluster` class in `mstrio.server.cluster` to allow adding and removing nodes from cluster startup
- added `port`, `status`, `load`, `projects` and `default` attributes to `Node` class in `mstrio.server.node` subpackage
- added `get_status_on_node` method to `Project` in `mstrio.server.project` class to allow checking the status of a project on a specific node
- added `lock`, `unlock` methods and `lock_status` property to `Project` class in `mstrio.server.project` to allow managing project locks

### Minor changes

- added `include_subfolders` flag to `list_folders` method of `mstrio.object_management.folder` package to allow getting all folders in the specified project or configuration-level folders
- added `parent_folder` argument to `list_folders` method of `mstrio.object_management.folder` package to allow getting all folders from specified parent folder only

### Bug fixes

- fixed the `settings` property for the `UserGroup` class to allow fetching a list of settings on the environment version 11.4.1200 and above. On the previous environments versions no change in behaviour will happen and the settings for the `jobMemGoverning` will be returned
- fixed the `create` method for the `ContentGroup` to allow creation without the need to provide `recipients`
- fixed the `alter` method for the `Application` class, passing the wrong body to the server
- fixed the `alter` methods for `Event` and `Driver` classes to allow update comments
- fixed `EmbeddedConnection` so that its objects properly link to their correspondent DSNs
- fixed `User.last_login` erroneously reporting the user does not exist in some cases

## 11.4.9.101 - 2024/09/20

### New features

- added `list_bots` method and `Bot` class in `mstrio.project_objects.bots` subpackage to allow management of Bots
- added `list_content_groups` method and `ContentGroup` class in `mstrio.project_objects.content_group` subpackage to allow management of Content Groups
- added `list_applications` method and `Application` class in `mstrio.project_objects.applications` subpackage to allow management of Applications
- added `StorageService` class for Storage Service configuration of an environment
- added `storage_service` property, `fetch_storage_service` and `update_storage_service` methods to the `Environment` class to manage the environment's Storage Service configuration
- official release of `Migration` class and its methods (introduces some breaking changes compared to "Preview" state)

### Minor changes

- added `last_update_time` property to `Cube` based classes

### Bug fixes

- fixed `utils.wip` to not configure root logger, added separate logger for the library's root module to not interfere with loggers defined in users' scripts
- fixed `DatasourceInstance.to_dict` so that incomplete REST response does not invalidate listing Datasource Instances and lookup by name

## 11.4.6.101 - 2024/06/21

### New features

- added `refresh()` method to `OlapCube` and `SuperCube` classes to allow cubes republish without interaction, creating a `Job`
- added support for providing a folder path instead of a folder ID to methods within the `Folder` class,
  and also `quick_search`, `full_search` and all methods inheriting from them that accept a folder ID argument
- added `include_subfolders` flag to `get_contents` method of `Folder` class to allow getting the contents of
  the children of the specified folder recursively
- added the `sql` property to `Report` class, that allows getting the SQL View of a report without executing it
- added `IncrementalRefreshReport` class in `mstrio.object_management.incremental_refresh_report` package to allow managing Incremental Refresh Reports
- added `list_incremental_refresh_reports` method to allow listing Incremental Refresh Reports in a project
- added function `quick_search_by_id()` in `mstrio.object_management.search_operations`
  to allow searching for objects by object and project ID
- added function `send_email()` in `mstrio.distribution_services.email` to allow sending emails
- added `execute_query()` method to `DatasourceInstance` class to allow executing SQL queries
- added `status` property to `Subscription` class to allow checking the status of a subscription
- added support for answering prompts in `to_datasource()` method of `Report` class, along with
  a `Prompt` class in `mstrio.project_objects.prompts` to support prompts
- added support for `password_auto_expire` and `password_expiration_frequency` fields to `User` class
- added support for Page By in `Report` class
- added support for VLDB properties in `Report` class

### Minor changes

- added Warning message to `OlapCube` nad `SuperCube` classes that is shown when provided ID belongs to Cube of different type
- updated `PageSize` Enum values to allow proper Subscription initialization
- added support for both `name` and `display_name` in VLDB settings provided by `ModelVldbMixin`
- added `vldb_settings` property in `VldbMixin` class that stores VLDB settings in dict with setting names as keys

## 11.4.3.101 - 2024/03/22

### New features

- added `delete_object_cache()` and `delete_element_cache()` methods to `Project` class to allow deleting
  object and element cache
- added new optional argument `show_description` to `ProjectSettings.list_caching_properties()` to show description
  for each setting
- added `delete_server_object_cache()` and `delete_server_element_cache()` methods to `Environment` class to allow deleting
  object and element cache from all projects
- added `MobileSubscription` class in `mstrio.distribution_services.subscription` package to allow
  management of the new subscription type
- added new bulk methods to the `Translation` class: `to_json_from_list`, `add_translations_from_json`,
  `to_database_from_list`, `add_translations_from_database`, `to_dataframe_from_list` and
  `add_translations_from_dataframe`
- updated old Translation methods: `to_csv_from_list` and `add_translations_from_csv` with new functionalities
  present in the new bulk methods for json, databases and dataframes
- added support for the `comments` field in MSTR objects to view and edit their long description
- added `EmbeddedConnection` class to allow access to embedded connection templates in `DatasourceInstance`
- added support for Python 3.12

### Minor changes

- updated script template for datasource scripts
- `enableHtmlContentInDossier` server setting is now read-only for environments on Update 13 and newer,
  and cannot be changed using mstrio-py since it is being superseded by `allowHtmlContent`

### Deprecated

- `mstrio.project_objects.dossier` module is superseded by
  `mstrio.project_objects.dashboard` and will be removed in the future, after 1-year deprecation period

### Removed

- MicroStrategy for Jupyter Extension is no longer developed and supported
  and was removed from the mstrio-py package in March 2024.
  You can still use the mstrio-py library and all its current and upcoming features.

## 11.3.12.101 - 2023/12/15

### New features

- changed `list_users` to allow filtering on `enabled` field
- added support for `ldapdn`, `language`,`owner` and `default_timezone` for `Users`
- added support for `ldapdn` for `UserGroups`
- added `add_datasource()` and `remove_datasource()` methods to `Project` class to allow
  adding and removing datasources from the project
- added `data_language_settings` and `metadata_language_settings` properties to `Project` class
  to allow interacting with project internalization:
  - `add_language()`, `alter_language()`, `remove_language()`, `alter_current_mode()`,
    `alter_default_language()` methods for the `data_language_settings` property
  - `add_language()`, `remove_language()` for the `metadata_language_settings` property
- added new optional argument `show_description` to `ProjectSettings.list_properties()`,
  `ProjectSettings.to_csv()`, `ServerSettings.list_properties()`, `ServerSettings.to_csv()`
  to show description for each setting
- added `Enums` in `mstrio.server.setting_types` to allow altering `Enum` settings by providing
  `Enum` values instead of `string`

### Minor changes

- updated code snippets for datasources to use `Language` class and `list_languages` function from `mstrio.server.language` package
  instead of `Locale` class and `list_locales` function
- members in user groups and security roles are now instances of `User` or `UserGroup` class instead of dictionaries
- addresses in `User` class are now instances of `Address` class instead of dictionaries
- added `force_with_dependents` flag in `Schedule.delete()` method that allows to delete `Schedule` with dependent subscriptions without prompt

### Bug fixes

- changed endpoint of `list_users`, allowing for listing users in environments with large number of users more efficiently

### Deprecated

- possibility of providing `initials` as a filter in `list_users` is deprecated and will be removed in the future

### Removed

- removed `Locale` class and `list_locales` function from `mstrio.datasources.datasource_map` module
- removed `update()` method from `OlapCube` class
- removed `mstrio.api.exceptions` and `mstrio.helpers.exceptions` modules
- removed `overwrite`, `attributes` and `meterics` parameters in `OlapCube.create()` method
- removed ability to pass instance of `Locale` class as argument in `mstrio.datasources.datasource_map` module

## 11.3.11.101 - 2023/09/28

### New features

- added support for VLDB properties for `Metric` objects by providing
  `list_vldb_settings`, `reset_vldb_settings`, `alter_vldb_settings` methods
  and `vldb_settings` attribute
- add `refresh` argument to `list_datasource_warehouse_tables` to allow refreshing
  warehouse tables available in a datasource
- enhanced `update_physical_table_structure` and `update_physical_table_structure_for_all_tables`
  methods of `LogicalTable` to work after changing `WarehouseTable` structure
- added `Translation` class in `mstrio.object_management.translation` package to allow management
  of Translations for any object with the following methods: `add_translation`, `alter_translation`,
  `remove_translation`, `to_csv_from_list` and `add_translations_from_csv`
- added `list_translations` to allow listing translations for objects
- added `add_translation`, `alter_translation`, `remove_translation` and `list_translations`
  methods to all objects inheriting from Entity to allow translation management directly
  through the objects

### Minor changes

- moved `Rights`, `AggregatedRights`, `Permissions` enums to `mstrio.helpers` module

### Bug fixes

- updated default values of `PackageSettings` class to allow safe initialization
- fixed `Project Not Loaded` error when trying to initialize `Project` object when
  running in a cluster configuration with the project not being loaded on all nodes
- fixed `full_search`, `get_search_results` to always return correct number of objects

### Removed

- removed `list_folders`, `create_folder`, `delete_folder` from `mstrio.utils.helper`
  because they have been superseded by `mstrio.object_management.folder` module

## 11.3.10.103 - 2023/08/04

### New features

- added `delete()` method to `Project` class to allow deleting projects
- added parameter `hidden` to `create` methods of `Attribute` and `Metric` classes

### Minor changes

- rename `ObjectTypes.NONE` to `ObjectTypes.NOT_SUPPORTED` in `mstrio.types` module

### Bug fixes

- fixed `to_dataframe` method of `OlapCube` class to return dataframe containing
  not only default attribute forms (The following types of Intelligent Cube are not
  supported: MDX, Query Builder, Freefrom SQL, Freeform XQuery, and Data Import.)
- add printing info message to `load`, `unload` and `delete` methods of `ContentCache`
  class indicating that operation could not be performed because cache was deleted,
  in that case execution of `load` method will be stopped by raising error
- added support for `Date` type to `SuperCube` class
- updated `User.add_address` and `User.update_address` methods to allow more
  address customizations

### Deprecated

- `mstrio.api.exceptions` and `mstrio.utils.exceptions` modules are superseded by
  `mstrio.helpers`, and will be removed in the future

## 11.3.10.102 - 2023/07/07

### Major changes

- added `Language` class in `mstrio.server.language` package to allow management
  of Languages
- added `list_languages` and `list_interface_languages` to allow listing languages
  and interface languages

### Minor changes

- fixed `Metric` objects always returning `None` for `hidden` field and fixed
  `alter` method to allow updating it

### Deprecated

- `Locale` class in `mstrio.datasources` is no longer supported and is
  superseded by `Language` class in `mstrio.server.language` package
- `list_locales` function in `mstrio.datasources` is no longer supported and is
  superseded by `list_languages` function in `mstrio.server.language` package

## 11.3.10.101 - 2023/06/02

### Major changes

- updated `create` method of `OlapCube` class to support new parameters:
  `template`, `filter`, `options`, `advanced_properties`, `time_based_settings`,
  `show_expression_as` and `show_filter_tokens`
- updated `alter` method of `OlapCube` class to allow altering new parameters:
  `template`, `filter`, `options` and `time_based_settings`
- added `set_partition_attribute`, `remove_partition_attribute` and `list_attribute_forms`
  methods to `OlapCube` class to allow management of partition attribute and observing
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
  `PackageSettings` and `PackageContentInfo` used for configuring migration
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
- `mstrio.browsing` is deprecated and is superseded
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

- `mstrio.admin.schedule` is deprecated and superseded with
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
- `mstrio.cube` and `mstrio.dataset` are deprecated and are superseded by
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
