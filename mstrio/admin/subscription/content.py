from mstrio.distribution_services.subscription.content import Content, RefreshPolicy  # noqa: F401

import warnings
warnings.warn(
    DeprecationWarning(
        ("mstrio.admin.subscription.content module is deprecated and will be removed "
         "in version 11.3.2.101. Use mstrio.distribution_services.subscription.content "
         "instead.")))
