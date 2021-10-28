from mstrio.utils.helper import deprecation_warning

from .base_subscription import *  # NOQA
from .email_subscription import *  # NOQA

deprecation_warning(
    "importing EmailSubscription from `mstrio.distribution_services.subscription.subscription`",
    "`mstrio.distribution_services.subscription`", "11.3.4.101")  # NOSONAR
