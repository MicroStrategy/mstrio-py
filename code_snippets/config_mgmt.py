"""
This demo script shows how to customize mstrio-py's global configuration.

This script's basic goal is to present what can be done with this module and
to ease its usage.
"""

from mstrio import config

# mstrio-py's behaviour can be customized in many ways
#
# `mstrio.config` module allows you to set a number of properties all objects
# and modules in mstrio will follow once set. All of them have some default
# values as will be described below.
#
# You change the parameter value just by assigning to it
# (examples):
config.verbose = False
config.verbose = True
config.wip_warnings_enabled = True
config.wip_warnings_enabled = False
config.default_request_timeout = 60 * 60 * 3  # 3h
...

# List of all available properties in `config` module:
# [Config Parameters]:
"""Controls the amount of feedback from the I-Server.
boolean, default: `True`
"""
config.verbose

"""Controls if object will fetch basic data from server on init.
boolean, default: `True`
"""
config.fetch_on_init

"""Controls whether progress bar will be shown during long fetch operations.
boolean, default: `True`
"""
config.progress_bar

"""Lets the program run in debugging mode, logging more information
at each step.
boolean, default: `False`
"""
config.debug

"""Controls whether warnings/errors about WIP functionality are emitted
boolean, default: `True`
"""
config.wip_warnings_enabled

"""Time (in seconds) after which every `Connection.<request_type>(...)` method
(example: `Connection.get(...)`) times out and stops waiting for response,
raising `requests.Timeout`. Default is 86400 seconds (24 hours).

It uses `requests` library's `timeout` parameter under the hood. (read more:
<https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts>)

Each `Connection` instance can have its own `request_timeout` parameter set,
overwriting this config value, if set to a number and not `None`.

int | float | None, default: 86400 (24h)
"""
config.default_request_timeout

# [Config Methods]:
"""Toggle mstrio-py's logger debug level between INFO (default) and DEBUG."""
config.toggle_debug_mode()

"""Context manager to temporarily disable verbose mode."""
with config.temp_verbose_disable():
    ...

# [Config Objects]:
"""Get mstrio-py's root STDOUT logger object to customize its settings."""
config.logger

"""Get mstrio-py's root STDERR logger object to customize its settings."""
config.warnings_logger
