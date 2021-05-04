from mstrio.distribution_services.subscription.delivery import (  # noqa: F401
    SendContentAs, Orientation, CacheType, ShortcutCacheFormat, ClientType, DeliveryDictable,
    ZipSettings, Delivery)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.subscription.delivery",
                    "mstrio.distribution_services.subscription.delivery", "11.3.2.101")
