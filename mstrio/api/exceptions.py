# -*- coding: future_typing -*-
from mstrio.helpers import (  # NOQA
    IServerException,
    MstrException,
    MstrTimeoutError,
    PartialSuccess,
    PromptedContentError,
    Success,
    VersionException,
)
from mstrio.utils.helper import deprecation_warning

deprecation_warning(
    deprecated=("mstrio.api.exceptions"),
    new=("mstrio.helpers"),
    version='11.3.11.103',  # NOSONAR
    module=True,
)
