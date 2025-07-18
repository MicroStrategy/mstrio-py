"""This is the demo script to show how to include custom logging messages
into your script, independently from what the code itself will log.
"""

import logging
import sys

from mstrio.connection import get_connection
from mstrio.datasources import list_datasource_instances

# At any point you can you use built-in `print` method to print something
# to console and, in turn, to the log file.
print('I am running MyCustomScript!')

# However, if you wish to customize what and how will be logged, you can use a
# built-in `logging` module and customize it for your script specifically.
LOGGER_REFERENCE = 'MyCustomScript'
logger = logging.getLogger(LOGGER_REFERENCE)

# You can customize what level of logging will be stored. Every level below it
# will just be ignored. Available levels (in order) are:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)  # we set the level to INFO, so DEBUG will be ignored

# The below set if instructions basically tell the script to do the following:
# 1. Whenever `logger` is used, print the message to console and keep it in logs
# 2. Format messages in a custom way including logger name and message's level
stream_handler = logging.StreamHandler(sys.stdout)
# (feel free to customize the formatting to your liking)
# (details in documentation: <https://docs.python.org/3/library/logging.html>)
stream_handler.setFormatter(logging.Formatter('[%(name)s]{%(levelname)s}: %(message)s'))
# (this level should always be DEBUG as this applies to message stream
# configuration and not the logger itself)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

# Now you can use the logger to log messages of different levels.
#
# If you did not change anything above you'll notice that only messages INFO
# and above will be logged to console, while DEBUG message will be ignored.
# This is because of `logger.setLevel(logging.INFO)` line above.
logger.debug('This is DEBUG')
logger.info('This is INFO')
logger.warning('This is WARN')
logger.error('This is ERROR')
logger.critical('This is CRIT')


"""
Below is an example of logging use in actual workflow.

We're updating VLDB SQL username settings to '/*!u*/'
for all relevant datasource instances.
"""

vldb_names = [  # example names
    'Post Insert String',
    'SELECT PostString for Main SQL',
    'SELECT PostString',
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

conn = get_connection(workstationData)

try:
    datasource_instances = list_datasource_instances(connection=conn)
except Exception as e:
    logger.error(f"Failed to list datasource instances: {e}")
    raise e  # break the script by re-raising the error

for datasource in datasource_instances:
    try:
        vldb_settings = datasource.list_vldb_settings(
            to_dictionary=True,
            groups=['Select/Insert'],
        )
        relevant_vldbs = [vldb for vldb in vldb_settings if vldb in vldb_names]

        vldbs_to_update = {}
        for vldb in relevant_vldbs:
            current_value = datasource.vldb_settings[vldb].value
            logger.debug(f'{vldb}: {current_value}')
            if current_value != '/*!u*/':
                logger.debug(
                    f'Adding {vldb} for datasource {datasource.name} to update list'
                )
                vldbs_to_update[vldb] = '/*!u*/'

        if vldbs_to_update:
            logger.info(f"Updating '{datasource.name}' VLDBs: {list(vldb)} to '/*!u*/'")
            try:
                datasource.alter_vldb_settings(names_to_values=vldbs_to_update)
            except Exception as e:
                logger.error(
                    "Failed to update VLDB settings "
                    f"for datasource '{datasource.name}': {e}"
                )
                continue
    except Exception as e:
        logger.error(f"Failed to process datasource '{datasource.name}': {e}")
