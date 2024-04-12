# -*- coding: future_typing -*-
from mstrio.helpers import NotSupportedError  # NOQA
from mstrio.utils.helper import deprecation_warning

deprecation_warning(
    deprecated=("mstrio.utils.exceptions"),
    new=("mstrio.helpers"),
    version='11.3.11.103',  # NOSONAR
    module=True,
)
