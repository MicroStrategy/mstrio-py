![MicroStrategy Logo][logo]

[![image](https://img.shields.io/pypi/v/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/l/mstrio-py.svg)](https://pypi.org/project/mstrio-py)
[![image](https://img.shields.io/pypi/dm/mstrio-py.svg)](https://pypi.org/project/mstrio-py)

# mstrio: Simple and Secure Access to MicroStrategy Data <!-- omit in toc -->

**mstrio** provides a high-level interface for [Python][py_github] and [R][r_github] and is designed to give **data scientists**, **developers**, and **administrators** simple and secure access to their MicroStrategy environment. It wraps [MicroStrategy REST APIs][mstr_rest_docs] into simple workflows, allowing users to fetch data from cubes and reports, create new datasets, add new data to existing datasets, and manage Users/User Groups, Servers, Projects, and more. Since it enforces MicroStrategy’s user and object security model, you don’t need to worry about setting up separate security rules.

With mstrio-py for **data science**, it’s easy to integrate cross-departmental, trustworthy business data in machine learning workflows and enable decision-makers to take action on predictive insights in MicroStrategy Reports, Dossiers, HyperIntelligence Cards, and customized, embedded analytical applications.

With mstrio-py for **system administration**, it’s easy to minimize costs by automating critical, time-consuming administrative tasks, even enabling administrators to leverage the power of Python to address complex administrative workflows for maintaining a MicroStrategy environment.

**MicroStrategy for Jupyter** is an extension for Jupyter Notebook which provides a graphical user interface for mstrio-py methods with the help of which user can perform all of the import and export actions without writing a single line of code manually. MicroStrategy for Jupyter is contained within mstrio-py package and is available after installation and enabling as Jupyter extension

# Table of Contents <!-- omit in toc -->

<!--ts-->

- [Main Features](#main-features)
- [Documentation](#documentation)
- [Usage Remarks](#usage-remarks)
  - [General](#general)
  - [GUI](#gui)
  - [Backend](#backend)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
    - [mstrio-py](#mstrio-py)
    - [MicroStrategy for Jupyter](#microstrategy-for-jupyter)
  - [Install the `mstrio-py` Package](#install-the-mstrio-py-package)
  - [Enable the Jupyter Notebook extension](#enable-the-jupyter-notebook-extension)
- [Versioning & Changelog](#versioning--changelog)
- [Deprecating Features](#deprecating-features)
- [More Resources](#more-resources)
- [Other](#other)
<!--te-->

<a id="main-features" name="main-features"></a>
# Main Features

Main features of **mstrio-py** allows to access MicroStrategy data:

- Connect to your MicroStrategy environment using **Connection** class (see [code_snippets][code_snippet_conn])

  **Note**: to log into Library and use mstrio-py user needs to have _UseLibrary_ privilege.

- Import and filter data from a **OlapCube**, **SuperCube** or **Report** into a Pandas DataFrame (see [code_snippets][code_snippet_import])
- Export data into MicroStrategy by creating or updating **SuperCube** (see [code_snippets][code_snippet_export])

Since version **11.3.0.1**, **mstrio-py** includes also administration modules:

- **Project** management module (see [code_snippets][code_snippet_project])
- **Server** management module (see [code_snippets][code_snippet_server])
- **User** and **User Group** management modules (see [code_snippets][code_snippet_user])
- **Schedules** management module (see [code_snippets][code_snippet_schedules])
- **Subscription** management modules including **Email Subscription**,  **Cache Update Subscription**, **File Subscription**, **FTP Subscription** and **History List Subscription** (see [code_snippets][code_snippet_subs])
- **User Library** module (see [code_snippets][code_snippet_library])
- **User Connections** management module
- **Privilege** and **Security Role** management modules (see [code_snippets][code_snippet_privilege])
- **Cube Cache** management modules (see [code_snippets][code_snippet_cache])
- **Intelligent Cube** management modules (see [code_snippets][code_snippet_olap])
- **Security filter** module (see [code_snippets][code_snippet_security_filter])
- **Datasources and Connection Mapping** subpackage for database management (see [code_snippets][code_snippet_datasource])
- **Job Monitor** module for job monitoring (see [code_snippets][code_snippet_job_monitor])
- **Object management** module (see [code_snippets][code_snippet_object_mgmt])
- **Contact** module (see [code_snippets][code_snippet_contact])
- **Contact Group** module (see [code_snippets][code_snippet_contact_group])
- **Device** module (see [code_snippets][code_snippet_device])
- **Transmitter** module (see [code_snippets][code_snippet_transmitter])
- **Event** module (see [code_snippets][code_snippet_events])
- **Migration** module (see [code_snippets][code_snippet_migration]) - **NOTE**: available as a Functionality Preview.
It is subject to change until it is released as Generally Available.
- **Schema Management** module (see [code_snippets][code_snippet_schema_mgmt])
- **User Hierarchy** module (see [code_snippets][code_snippet_user_hierarchy])
- **Attribute** module (see [code_snippets][code_snippet_attribute])
- **Fact** module (see [code_snippets][code_snippet_fact])
- **Table** module (see [code_snippets][code_snippet_table_mgmt])
- **Filter** module (see [code_snippets][code_snippet_filter])
- **Transformation** module (see [code_snippets][code_snippet_transformation])
- **Metric** module (see [code_snippets][code_snippet_metrics])
- **Document** module (see [code_snippets][code_snippet_document])
- **Dossier** module (see [code_snippets][code_snippet_dossier])
- **Content Cache** module (see [code_snippets][code_snippet_content_cache])
- **Dynamic Recipient List** module (see [code_snippets][code_snippet_dynamic_recipient_list])

<a id="documentation" name="documentation"></a>
# Documentation

Detailed information about **mstrio-py** package can be found in [**official documentation**][mstrio_py_doc].

<a id="usage-remarks" name="usage-remarks"></a>
# Usage Remarks

<a id="general" name="general"></a>
## General

- **Chrome** is the only supported web browser. `mstrio-py` should work properly in **Safari**, **Opera** or **Edge** but we cannot guarantee a seamless experience.
- It is recommended NOT to use Anaconda environment. Please see **Installation** section below for details.

<a id="gui" name="gui"></a>
## GUI

- GUI `Import -> Prepare Data` filters out all "**_Row Count - ..._**" columns even if they are an integral part of a Dataset. Starting column's name with "_Row Count_" is not advised.

<a id="backend" name="backend"></a>
## Backend

- Currently it is not possible to use `mstrio-py` package to update cubes created via Web. Unfortunately it is not possible to use any REST API endpoint to check whether cube was created
via Web or via REST API to provide some warning. In case of seeing one of the following error
messages it is most probable that cube was created via Web and REST API can't handle its update,
so if you want to update this particular cube you have to use Web.

```
When we tried to map the new dataset, we detected that some columns are missing or the data type changed, etc.
```

```
We could not obtain the data because the DB connection changed and the table does not exist anymore.
```

- When trying to download a big IMDB Cube (or a Report based on such Cube) on multi-node environment, sometimes the process may fail. This is due to the characteristic of data retrieval of IMDB Cubes with connection to more than one node on iServer. For now, known workaround is to log out and just simply try again. This type of issue can be identified when seeing any of the following error messages during work with IMDB Cube on multi-node environment:

```
Cube cannot be found.
```
(even if previously it was found without issue)

```
Error getting cube metadata information. I-Server Error ERR001, (ServiceManager: XML syntax error.)
```

<a id="installation" name="installation"></a>
# Installation

<a id="prerequisites" name="prerequisites"></a>
## Prerequisites

<a id="mstrio-py" name="mstrio-py"></a>
### mstrio-py

- Python 3.10+
- MicroStrategy 2019 Update 4 (11.1.4)+

<a id="microstrategy-for-jupyter" name="microstrategy-for-jupyter"></a>
### MicroStrategy for Jupyter

- [CORS enabled on MicroStrategy Library server][cors_manual]
- [Cookies sent by MicroStrategy Library server have 'SameSite' parameter set to 'None'][same_site_manual]

**Note**: MicroStrategy for Jupyter is accessible only to users with assigned Microstrategy privileges:
`Use Application Jupyter` and `Use Library Web`. For more details, please refer to Microstrategy licensing.

<a id="install-the-mstrio-py-package" name="install-the-mstrio-py-package"></a>
## Install the `mstrio-py` Package

**Note**: it is NOT recommended to install mstrio-py in an Anaconda environment.
For a seamless experience, install and run it in Python's [virtual environment][python_venv] instead.

Installation is easy when using [pip](https://pypi.org/project/mstrio-py). Read more about installation on MicroStrategy's [product documentation][mstr_help_docs].

```bash
pip install mstrio-py
```

<a id="enable-the-jupyter-notebook-extension" name="enable-the-jupyter-notebook-extension"></a>
## Enable the Jupyter Notebook extension

Once mstrio-py is installed you can install and enable the Jupyter Notebook extension by using the commands below:

```
jupyter nbextension install connector-jupyter --py --sys-prefix
jupyter nbextension enable connector-jupyter --py --sys-prefix
```

<a id="versioning--changelog" name="versioning--changelog"></a>
# Versioning & Changelog

Current version: **11.3.9.101** (3 March 2023). Check out [**Changelog**][release_notes] to see what's new.

mstrio-py is constantly developed to support newest MicroStrategy REST APIs. Functionalities may be added to mstrio on monthly basis. It is **recommended** to always install the newest version of mstrio-py, as it will be most stable and still maintain backwards compatibility with various MicroStrategy installations, dating back to 11.1.4.

Features that will be added to the package but require APIs not supported by your environment (I-Server), will raise `VersionException`.

mstrio-py can be used for both, **data-science** related activities and for **administrative tasks**. Former requires at least MicroStrategy 2019 Update 4 (11.1.4), latter works with 11.2.1 and higher.

If you intend to use mstrio with MicroStrategy version older than 11.1.4, refer to the PyPI package archive to download mstrio 10.11.1, which is supported on:

- MicroStrategy 2019 (11.1)
- MicroStrategy 2019 Update 1 (11.1.1)
- MicroStrategy 2019 Update 2 (11.1.2)
- MicroStrategy 2019 Update 3 (11.1.3)

Refer to the [PyPI package archive][pypi_archive] for a list of available versions.

To install a specific, archived version of mstrio, choose the desired version available on [PyPI package archive][pypi_archive] and install with `pip`, as follows:

```python
pip install mstrio-py==10.11.1
```

<a id="deprecating-features" name="deprecating-features"></a>
# Deprecating Features

When features (modules, parameters, attributes, methods etc.) are marked for deprecation but still accessed, the following `DeprecationWarning` will be shown (example below). The functionality will continue to work until the version specified in the warning is released.

![Deprecation warning ][deprecation]

<a id="more-resources" name="more-resources"></a>
# More Resources

- [Tutorials for mstrio][mstr_datasci_comm]
- [Check out mstrio for R][r_github]
- [Learn more about the MicroStrategy REST API][mstr_rest_docs]
- [MicroStrategy REST API demo documentation][mstr_rest_demo]

<a id="other" name="other"></a>
# Other

"Jupyter" and the Jupyter logos are trademarks or registered trademarks of NumFOCUS.

[pypi_archive]: https://pypi.org/project/mstrio-py/#history
[py_github]: https://github.com/MicroStrategy/mstrio-py
[r_github]: https://github.com/MicroStrategy/mstrio
[mstr_datasci_comm]: https://community.microstrategy.com/s/topic/0TO44000000AJ2dGAG/python-r-u108
[mstrio_py_doc]: http://www2.microstrategy.com/producthelp/Current/mstrio-py/
[mstr_rest_demo]: https://demo.microstrategy.com/MicroStrategyLibrary/api-docs/index.html
[mstr_rest_docs]: https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API.htm
[mstr_help_docs]: https://www2.microstrategy.com/producthelp/current/MSTR-for-Jupyter/Content/mstr_for_jupyter.htm
[cors_manual]: https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/EmbeddingSDK/Content/topics/EnableCORS.htm
[same_site_manual]: https://community.microstrategy.com/s/article/Chrome-v80-Cookie-Behavior-and-the-impact-on-MicroStrategy-Deployments?language=undefined&t=1581355581289
[python_venv]: https://docs.python.org/3/tutorial/venv.html
[release_notes]: https://github.com/MicroStrategy/mstrio-py/blob/master/NEWS.md
[logo]: https://github.com/MicroStrategy/mstrio-py/blob/master/mstr-logo.png?raw=true
[deprecation]: https://github.com/MicroStrategy/mstrio-py/blob/master/deprecation.png?raw=true
[code_snippet_attribute]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/attributes.py
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
[code_snippet_dossier]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/dossier.py
[code_snippet_dynamic_recipient_list]: https://github.com/MicroStrategy/mstrio-py/blob/master/code_snippets/dynamic_recipient_list.py
