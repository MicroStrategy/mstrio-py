"""mstrio: Simple and Secure Access to Strategy One Data

Mstrio provides a high-level interface for Python and is designed
to give data scientists, developers, and administrators simple and secure
access to their Strategy One environment.

It wraps Strategy One REST APIs into simple workflows, allowing users
to fetch data from cubes and reports, create new datasets, add new data
to existing datasets, and manage Users/User Groups, Servers, Projects,
and more. Since it enforces Strategy One’s user and object security model,
you don’t need to worry about setting up separate security rules.

With mstrio-py for data science, it’s easy to integrate cross-departmental,
trustworthy business data in machine learning workflows and enable
decision-makers to take action on predictive insights in Strategy One Reports,
Dashboards, HyperIntelligence Cards, and customized, embedded analytical
applications.

With mstrio-py for system administration, it’s easy to minimize costs by
automating critical, time-consuming administrative tasks, even enabling
administrators to leverage the power of Python to address complex
administrative workflows for maintaining a Strategy One environment.
"""

__title__ = "ni-mstrio-py"
__version__ = "2025.1.0"  # NOSONAR
__license__ = "Apache License 2.0"
__description__ = "NI-customized Python interface for the MicroStrategy REST API"
__author__ = "NI"
__author_email__ = "robert.szarvas@emerson.com"

from .utils.dev_helpers import what_can_i_do_with  # noqa: F401
