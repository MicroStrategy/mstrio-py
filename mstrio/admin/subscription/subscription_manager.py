import warnings

from mstrio.distribution_services.subscription.subscription_manager import (  # noqa: F401
    Content, list_subscriptions, Subscription, SubscriptionManager)

warnings.warn(
    DeprecationWarning(
        ("mstrio.admin.subscription.subscription_manager module is "
         "deprecated and will be removed in version 11.3.2.101. Use "
         "mstrio.distribution_services.subscription.subscription_manager instead.")))
