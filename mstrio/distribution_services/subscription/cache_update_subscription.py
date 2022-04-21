from typing import List, Optional, Union

from mstrio.connection import Connection

from ..schedule import Schedule
from .base_subscription import Subscription
from .content import Content
from .delivery import CacheType, Delivery, LibraryCacheTypes, ShortcutCacheFormat


class CacheUpdateSubscription(Subscription):
    """Class representation of MicroStrategy Cache Update Subscription
    object."""
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, subscription_id: str = None, project_id: str = None,
                 project_name: str = None):
        """Initialize CacheUpdateSubscription object, populates it with
        I-Server data if subscription_id is passed.
        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is
        omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            subscription_id: ID of the subscription to be initialized
            project_id: Project ID
            project_name: Project name
        """
        if subscription_id:
            super().__init__(connection, subscription_id, project_id, project_name)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        allow_delivery_changes: Optional[bool] = None,
        allow_personalization_changes: Optional[bool] = None,
        allow_unsubscribe: Optional[bool] = None,
        send_now: Optional[bool] = None,
        owner_id: Optional[str] = None,
        schedules: Optional[Union[str, List[str], Schedule, List[Schedule]]] = None,
        contents: Optional[Content] = None,
        recipients: Optional[Union[List[dict], List[str]]] = None,
        delivery: Optional[Union[Delivery, dict]] = None,
        delivery_expiration_date: Optional[str] = None,
        contact_security: bool = True,
        cache_cache_type: Union[CacheType, str] = CacheType.RESERVED,
        cache_shortcut_cache_format: Union[ShortcutCacheFormat,
                                           str] = ShortcutCacheFormat.RESERVED,
        cache_library_cache_types: List[Union[LibraryCacheTypes, str]] = [LibraryCacheTypes.WEB],
        cache_reuse_dataset_cache: bool = False,
        cache_is_all_library_users: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: Optional[str] = None,
    ) -> "CacheUpdateSubscription":
        """Creates a new cache update subscription.

        Args:
            connection: a MicroStrategy connection object
            name: name of the subscription,
            project_id: project ID,
            project_name: project name,
            allow_delivery_changes: whether the recipients can change
                the delivery of the subscription,
            allow_personalization_changes: whether the recipients can
                personalize the subscription,
            allow_unsubscribe: whether the recipients can unsubscribe
                from the subscription,
            send_now: indicates whether to execute the subscription
                immediately,
            owner_id: ID of the subscription owner, by default logged in
                user ID,
            schedules:
                Schedules IDs or Schedule objects,
            contents: The content settings.
            recipients: list of recipients IDs
                or dicts,
            delivery: delivery object or dict
            delivery_expiration_date: expiration date of the subscription,
                format should be yyyy - MM - dd,
            contact_security: whether to use contact security for each
                contact group member
            cache_cache_type: [RESERVED, SHORTCUT, SHORTCUTWITHBOOKMARK]
            cache_shortcut_cache_format: [RESERVED, JSON, BINARY, BOTH]
            cache_library_cache_types: Set of library cache types,
                available types can be web, android, ios
            cache_reuse_dataset_cache: Whether to reuse dataset cache
            cache_is_all_library_users: Whether for all library users
            delivery_notification_enabled: Whether notification is enabled,
                notification applies to cache
            delivery_personal_notification_address_id: Notification details
        """
        return super()._Subscription__create(
            connection=connection,
            name=name,
            project_id=project_id,
            project_name=project_name,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe,
            send_now=send_now,
            owner_id=owner_id,
            schedules=schedules,
            contents=contents,
            recipients=recipients,
            delivery=delivery,
            delivery_mode=Delivery.DeliveryMode.CACHE,
            delivery_expiration_date=delivery_expiration_date,
            contact_security=contact_security,
            cache_cache_type=cache_cache_type,
            cache_shortcut_cache_format=cache_shortcut_cache_format,
            cache_library_cache_types=cache_library_cache_types,
            cache_reuse_dataset_cache=cache_reuse_dataset_cache,
            cache_is_all_library_users=cache_is_all_library_users,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=delivery_personal_notification_address_id,
        )

    def alter(
        cls,
        name: Optional[str] = None,
        allow_delivery_changes: Optional[bool] = None,
        allow_personalization_changes: Optional[bool] = None,
        allow_unsubscribe: Optional[bool] = None,
        send_now: Optional[bool] = None,
        owner_id: Optional[str] = None,
        schedules: Union[str, List[str], Schedule, List[Schedule]] = None,
        contents: Content = None,
        recipients: Union[List[dict], List[str]] = None,
        delivery: Union[Delivery, dict] = None,
        custom_msg=None,
        delivery_expiration_date: Optional[str] = None,
        contact_security: bool = True,
        cache_cache_type: Union[CacheType, str] = CacheType.RESERVED,
        cache_shortcut_cache_format: Union[ShortcutCacheFormat,
                                           str] = ShortcutCacheFormat.RESERVED,
        cache_library_cache_types: List[Union[LibraryCacheTypes, str]] = [LibraryCacheTypes.WEB],
        cache_reuse_dataset_cache: bool = False,
        cache_is_all_library_users: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: Optional[str] = None,
    ):
        """Alter the subscription.

        Args:
            name: name of the subscription,
            allow_delivery_changes: whether the recipients can change
                the delivery of the subscription,
            allow_personalization_changes: whether the recipients can
                personalize the subscription,
            allow_unsubscribe: whether the recipients can unsubscribe
                from the subscription,
            send_now: indicates whether to execute the subscription
                immediately,
            owner_id: ID of the subscription owner, by default logged in
                user ID,
            schedules:
                Schedules IDs or Schedule objects,
            contents: The content settings.
            recipients: list of recipients IDs
                or dicts,
            delivery: delivery object or dict
            delivery_expiration_date: expiration date of the subscription,
                format should be yyyy - MM - dd,
            contact_security: whether to use contact security for each
                contact group member
            cache_cache_type: [RESERVED, SHORTCUT,
                SHORTCUTWITHBOOKMARK]
            cache_shortcut_cache_format: [RESERVED, JSON, BINARY, BOTH]
            cache_library_cache_types: Set of library cache types,
                available types can be web, android, ios
            cache_reuse_dataset_cache: Whether to reuse dataset cache
            cache_is_all_library_users: Whether for all library users
            delivery_notification_enabled: Whether notification is enabled,
                notification applies to cache
            delivery_personal_notification_address_id: Notification details
        """
        return super().alter(
            name=name, allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe, send_now=send_now, owner_id=owner_id,
            schedules=schedules, contents=contents, recipients=recipients, delivery=delivery,
            custom_msg=custom_msg, delivery_expiration_date=delivery_expiration_date,
            contact_security=contact_security, cache_cache_type=cache_cache_type,
            cache_shortcut_cache_format=cache_shortcut_cache_format,
            cache_library_cache_types=cache_library_cache_types,
            cache_reuse_dataset_cache=cache_reuse_dataset_cache,
            cache_is_all_library_users=cache_is_all_library_users,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=delivery_personal_notification_address_id)
