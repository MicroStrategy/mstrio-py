![Strategy One Logo][logo]

[![image](https://img.shields.io/pypi/v/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/l/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/dm/mstrio-py.svg)](https://pypi.org/project/mstrio-py)

# mstrio-py: Simple and Secure Access to Strategy One Data

<!-- tox:docs:2: installation :start -->

## Installation

### Prerequisites

- Python 3.10+
- MicroStrategy 2019 Update 4 (11.1.4)+

### Install `mstrio-py` Package

> **Note**: it is NOT recommended to install mstrio-py in an **Anaconda** environment.
> For a seamless experience, install and run it in Python's [virtual environment][python_venv] instead.

Install latest version of [mstrio-py](https://pypi.org/project/mstrio-py) using `pip` command in Terminal:

```bash
pip install mstrio-py
```

To install a specific, archived version of mstrio, choose the desired version available on [PyPI package archive][pypi_archive] and install with `pip`, as follows:

```bash
pip install mstrio-py==10.11.1
```

### Issues or specific use cases

If there are any issues with the installation process it is possible your setup may differ from usual.
In that case, please see below some examples of most common situations and how to resolve them.

In all other cases, please refer to the [official Python libraries installation guide](https://packaging.python.org/en/latest/tutorials/installing-packages/).

#### Offline System or Proxy with Blacklisted `PyPI`

> **Note**: optimally, you should contact your system administrator and either request access to `PyPI` or some proxy setup whitelisting all or some of the `PyPI` libraries.

If your setup does not allow to get packages online directly from Python Packages Index (PyPI) using `pip`, you can download the package manually and install it locally.

1. download `.whl` file from here: <https://pypi.org/project/mstrio-py/#files>
1. in the terminal `cd` into a folder where you want to install _mstrio-py_
1. use the command provided below after filling the path
   - `py -m` tells the terminal to use default install execution of python available locally on the machine
   - `--user` flag says "install only for my user on this machine"
1. If you have issues with `py` command, try the same with `python` instead

```bash
cd path/where/mstrio/will/be/installed
py -m pip install --user path/to/downloaded/wheel/file/mstrio-py.whl
```

#### No Python or `pip` Installed on the Machine

You cannot use `mstrio-py` without Python installed on your machine unless directly via **Strategy Workstation**.

<!-- tox:docs: installation :end -->

## Documentation

Detailed information about **mstrio-py** package can be found in [**official documentation**][mstrio_py_doc].

<!-- tox:docs:1: main features :start -->

## Main Features

Main features of **mstrio-py** allows to access Strategy One data:

- Connect to your Strategy One environment using **Connection** class (see [code_snippets][code_snippet_conn])

  **Note**: to log into Library and use mstrio-py user needs to have _UseLibrary_ privilege.

- Import and filter data from a **OlapCube**, **SuperCube** or **Report** into a Pandas DataFrame (see [code_snippets][code_snippet_import])
- Export data into Strategy One by creating or updating **SuperCube** (see [code_snippets][code_snippet_export])

Since version **11.3.0.1**, **mstrio-py** includes also administration modules:

<!-- tox:docs:sort:start -->

- **Project** management module (see [code_snippets][code_snippet_project]) with **VLDB settings** management (see [code_snippets][code_snippet_vldb])
- **Project languages** management module (see [code_snippets][code_snippet_project_languages])
- **Server** management module (see [code_snippets][code_snippet_server])
- **User** and **User Group** management modules (see [code_snippets][code_snippet_user])
- **Schedules** management module (see [code_snippets][code_snippet_schedules])
- **Subscription** management modules including **Email Subscription**, **Cache Update Subscription**, **File Subscription**, **FTP Subscription**, **History List Subscription** and **Mobile Subscription** (see [code_snippets][code_snippet_subs])
- **User Library** module (see [code_snippets][code_snippet_library])
- **User Connections** management module
- **Privilege** and **Security Role** management modules (see [code_snippets][code_snippet_privilege])
- **Cube Cache** management module (see [code_snippets][code_snippet_cache])
- **Report Cache** management module (see [code_snippets][code_snippet_report_cache])
- **Intelligent Cube** management modules (see [code_snippets][code_snippet_olap]) with **VLDB settings** management (see [code_snippets][code_snippet_vldb])
- **Security filter** module (see [code_snippets][code_snippet_security_filter])
- **Datasources and Connection Mapping** subpackage for database management (see [code_snippets][code_snippet_datasource]) with **VLDB settings** management (see [code_snippets][code_snippet_vldb])
- **Job Monitor** module for job monitoring (see [code_snippets][code_snippet_job_monitor])
- **Object management** module (see [code_snippets][code_snippet_object_mgmt])
- **Contact** module (see [code_snippets][code_snippet_contact])
- **Contact Group** module (see [code_snippets][code_snippet_contact_group])
- **Device** module (see [code_snippets][code_snippet_device])
- **Transmitter** module (see [code_snippets][code_snippet_transmitter])
- **Event** module (see [code_snippets][code_snippet_events])
- **Migration** module (see [code_snippets][code_snippet_migration])
- **Schema Management** module (see [code_snippets][code_snippet_schema_mgmt])
- **User Hierarchy** module (see [code_snippets][code_snippet_user_hierarchy])
- **Attribute** module (see [code_snippets][code_snippet_attribute])
- **Fact** module (see [code_snippets][code_snippet_fact])
- **Table** module (see [code_snippets][code_snippet_table_mgmt])
- **Filter** module (see [code_snippets][code_snippet_filter])
- **Transformation** module (see [code_snippets][code_snippet_transformation])
- **Metric** module (see [code_snippets][code_snippet_metrics])
- **Document** module (see [code_snippets][code_snippet_document])
- **Dashboard** module (see [code_snippets][code_snippet_dashboard])
- **Content Cache** module (see [code_snippets][code_snippet_content_cache])
- **Dynamic Recipient List** module (see [code_snippets][code_snippet_dynamic_recipient_list])
- **Driver** module (see [code_snippets][code_snippet_datasource])
- **Gateway** module (see [code_snippets][code_snippet_datasource])
- **Language** module (see [code_snippets][code_snippet_languages])
- **Translation** module (see [code_snippets][code_snippet_translations])
- **Report** module (see [code_snippets][code_snippet_report])
- **Incremental Refresh Report** module (see [code_snippets][code_snippet_irr])
- **Agents** module (see [code_snippets][code_snippet_agents])
- **Content Group** module (see [code_snippets][code_snippet_content_groups])
- **Applications** module (see [code_snippets][code_snippet_applications])
- **Fence** module (see [code_snippets][code_snippet_fences])
- **Prompt** module (see [code_snippets][code_snippet_prompt])
- **Search Object** module (see [code_snippets][code_snippet_search_object])

<!-- tox:docs:sort:end -->
<!-- tox:docs: main features :end -->

<!-- tox:docs:4: versioning & changelog :start -->

## Versioning & Changelog

Current version: **11.5.11.101** (14 November 2025). Check out [CHANGELOG][release_notes] to see what's new.

`mstrio-py` is constantly developed to support newest Strategy One REST APIs. Functionalities may be added to mstrio on monthly basis. It is **recommended** to always install the newest version of mstrio-py, as it will be most stable and still maintain backwards compatibility with various Strategy One installations, dating back to 11.1.4.

Features that will be added to the package but require APIs not supported by your environment (I-Server), will raise `VersionException`.

`mstrio-py` can be used for both, **data-science** related activities and for **administrative tasks**. Former requires at least MicroStrategy 2019 Update 4 (11.1.4), latter works with 11.2.1 and higher.

If you intend to use mstrio with MicroStrategy 2019 Update 3 (11.1.3) or older, refer to the PyPI package archive to download mstrio 10.11.1, which is supported on:

- MicroStrategy 2019 (11.1)
- MicroStrategy 2019 Update 1 (11.1.1)
- MicroStrategy 2019 Update 2 (11.1.2)
- MicroStrategy 2019 Update 3 (11.1.3)

Refer to the [PyPI package archive][pypi_archive] for a list of available versions.

<!-- tox:docs: versioning & changelog :end -->

<!-- tox:docs:6: info & resources :start -->

## Additional Information

### `mstrio-py` Configuration

You can customize some global `mstrio-py`'s behavior by setting global configuration. Learn more in [config code snippets][code_snippet_config].

### Search for ID without additional data

`mstrio-py` has a dedicated method to identify what a particular object is knowing only its ID. Learn more in [search actions code snippet][code_snippet_search_actions]

### Deprecating Features

When features (modules, parameters, attributes, methods etc.) are marked for deprecation but still accessed, the following `DeprecationWarning` will be shown (example below). The functionality will continue to work until the version specified in the warning is released.

![Deprecation warning][deprecation]

### More Resources

- [Tutorials for mstrio][mstr_datasci_comm]
- [Learn more about the Strategy One REST API][mstr_rest_docs]
- [Strategy One REST API demo documentation][mstr_rest_demo]

<!-- tox:docs: info & resources :end -->

<!-- tox:docs: references -->

[pypi_archive]: https://pypi.org/project/mstrio-py/#history
[mstr_datasci_comm]: https://community.microstrategy.com/s/topic/0TO44000000AJ2dGAG/python-r-u108
[mstrio_py_doc]: http://www2.microstrategy.com/producthelp/Current/mstrio-py/
[mstr_rest_demo]: https://demo.microstrategy.com/MicroStrategyLibrary/api-docs/index.html
[mstr_rest_docs]: https://microstrategy.github.io/rest-api-docs/
[python_venv]: https://docs.python.org/3/tutorial/venv.html
[release_notes]: https://github.com/MicroStrategy/mstrio-py/blob/master/NEWS.md
[logo]: https://github.com/MicroStrategy/mstrio-py/blob/master/strategy-logo.png?raw=true
[deprecation]: https://github.com/MicroStrategy/mstrio-py/blob/master/deprecation.png?raw=true
[code_snippet_attribute]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/attributes.py
[code_snippet_config]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/config_mgmt.py
[code_snippet_conn]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/connect.py
[code_snippet_contact]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/contacts.py
[code_snippet_contact_group]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/contact_group_mgmt.py
[code_snippet_device]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/device_mgmt.py
[code_snippet_import]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/cube_report.py
[code_snippet_export]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/create_super_cube.py
[code_snippet_project]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/project_mgmt.py
[code_snippet_server]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/server_mgmt.py
[code_snippet_user]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/user_mgmt.py
[code_snippet_schedules]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/schedules.py
[code_snippet_subs]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/subscription_mgmt.py
[code_snippet_library]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/user_library.py
[code_snippet_cache]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/cube_cache.py
[code_snippet_olap]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/intelligent_cube.py
[code_snippet_job_monitor]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/job_monitor.py
[code_snippet_object_mgmt]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/object_mgmt.py
[code_snippet_security_filter]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/security_filters.py
[code_snippet_datasource]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/datasource_mgmt.py
[code_snippet_transmitter]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/transmitter_mgmt.py
[code_snippet_events]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/events.py
[code_snippet_migration]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/migration.py
[code_snippet_schema_mgmt]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/schema_mgmt.py
[code_snippet_user_hierarchy]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/user_hierarchy_mgmt.py
[code_snippet_fact]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/fact.py
[code_snippet_table_mgmt]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/table_mgmt.py
[code_snippet_filter]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/filter.py
[code_snippet_privilege]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/security_roles_and_privileges.py
[code_snippet_transformation]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/transformation.py
[code_snippet_metrics]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/metrics.py
[code_snippet_content_cache]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/content_cache.py
[code_snippet_document]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/document.py
[code_snippet_dashboard]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/dashboard.py
[code_snippet_dynamic_recipient_list]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/dynamic_recipient_list.py
[code_snippet_vldb]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/vldb.py
[code_snippet_languages]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/languages.py
[code_snippet_translations]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/translations.py
[code_snippet_project_languages]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/project_languages_mgmt.py
[code_snippet_irr]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/incremental_refresh_report.py
[code_snippet_report_cache]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/report_cache.py
[code_snippet_report]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/reports.py
[code_snippet_agents]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/agents.py
[code_snippet_content_groups]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/content_groups.py
[code_snippet_applications]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/applications.py
[code_snippet_fences]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/fences.py
[code_snippet_prompt]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/prompt_mgmt.py
[code_snippet_search_object]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/search_object.py
[code_snippet_search_actions]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/search_actions.py
