# flake8: noqa
from mstrio.server.project import *
from mstrio.utils import helper

helper.deprecation_warning(
    '`mstrio.server.application`',
    '`mstrio.server.project`',
    '11.3.4.101',  # NOSONAR
    False)
