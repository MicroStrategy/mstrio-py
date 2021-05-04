from mstrio.distribution_services.subscription.subscription import (  # noqa: F401
    CacheType, ClientType, Delivery, EmailSubscription, Orientation, RecipientsTypes,
    SendContentAs, ShortcutCacheFormat, Subscription, ZipSettings)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.subscription.subscription",
                    "mstrio.distribution_services.subscription.subscription", "11.3.2.101")
