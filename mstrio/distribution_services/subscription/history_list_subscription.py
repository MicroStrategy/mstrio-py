from typing import Optional

from mstrio.connection import Connection
from mstrio.distribution_services.schedule import Schedule
from mstrio.distribution_services.subscription import Content, Delivery, Subscription
from mstrio.utils.version_helper import class_version_handler


@class_version_handler('11.3.0600')
class HistoryListSubscription(Subscription):
    """Class representation of MicroStrategy History List Subscription
    object."""

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """Initializes HistoryListSubscription object and populates it with
        I-Server data if id or subscription_id is passed.
        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.
        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): ID of the subscription to be initialized, only
                id or subscription_id have to be provided at once, if both are
                provided id will take precedence
            subscription_id (str, optional): ID of the subscription to be
                initialized
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        super().__init__(connection, id, subscription_id, project_id, project_name)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        multiple_contents: Optional[bool] = False,
        allow_delivery_changes: Optional[bool] = None,
        allow_personalization_changes: Optional[bool] = None,
        allow_unsubscribe: Optional[bool] = None,
        send_now: Optional[bool] = None,
        owner_id: Optional[str] = None,
        schedules: Optional[str | list[str] | Schedule | list[Schedule]] = None,
        contents: Optional[Content] = None,
        recipients: Optional[list[dict] | list[str]] = None,
        delivery: Optional[Delivery | dict] = None,
        delivery_expiration_date: Optional[str] = None,
        delivery_expiration_timezone: Optional[str] = None,
        contact_security: bool = True,
        do_not_create_update_caches: bool = True,
        overwrite_older_version: bool = False,
        re_run_hl: bool = True,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: Optional[str] = None,
    ) -> "HistoryListSubscription":
        """Creates a new history list subscription.
        Args:
            connection (Connection): a MicroStrategy connection object
            name (str): name of the subscription
            project_id (str, optional): project ID
            project_name (str, optional): project name
            multiple_contents (bool, optional): whether multiple contents are
                allowed
            allow_delivery_changes (bool, optional): whether the
                recipients can change the delivery of the subscription
            allow_personalization_changes (bool, optional): whether
                the recipients can personalize the subscription
            allow_unsubscribe (bool, optional): whether the recipients
                can unsubscribe from the subscription
            send_now (bool, optional): indicates whether to execute the
                subscription immediately
            owner_id (str, optional): ID of the subscription owner, by
                default logged in user ID
            schedules (list[str] | str | Schedule | list[Schedule], optional):
                Schedules IDs or Schedule objects
            contents (Content, optional): The content settings
            recipients (list[dict] | dict, optional): list of recipients IDs
                or dicts
            delivery (dict | Delivery, optional): delivery object or dict
            delivery_expiration_date (str, optional): expiration date
                of the subscription, format should be yyyy - MM - dd
            delivery_expiration_timezone (str, optional): expiration timezone
                of the subscription, example value 'Europe/London'
            contact_security (bool): whether to use contact security for each
                contact group member
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                cache in the history list
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list
            re_run_hl (bool): whether subscription will re-run against warehouse
            delivery_notification_enabled (bool): Whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                Notification details
        """
        notification_address_id = delivery_personal_notification_address_id

        return super()._Subscription__create(
            connection=connection,
            name=name,
            project_id=project_id,
            project_name=project_name,
            multiple_contents=multiple_contents,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe,
            send_now=send_now,
            owner_id=owner_id,
            schedules=schedules,
            contents=contents,
            recipients=recipients,
            delivery=delivery,
            delivery_mode=Delivery.DeliveryMode.HISTORY_LIST,
            delivery_expiration_date=delivery_expiration_date,
            delivery_expiration_timezone=delivery_expiration_timezone,
            contact_security=contact_security,
            do_not_create_update_caches=do_not_create_update_caches,
            overwrite_older_version=overwrite_older_version,
            re_run_hl=re_run_hl,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=notification_address_id,
        )

    def alter(
        self,
        name: Optional[str] = None,
        multiple_contents: Optional[bool] = None,
        allow_delivery_changes: Optional[bool] = None,
        allow_personalization_changes: Optional[bool] = None,
        allow_unsubscribe: Optional[bool] = None,
        send_now: Optional[bool] = None,
        owner_id: Optional[str] = None,
        schedules: Optional[str | list[str] | Schedule | list[Schedule]] = None,
        recipients: Optional[list[dict] | list[str]] = None,
        delivery: Optional[Delivery | dict] = None,
        custom_msg: Optional[str] = None,
        delivery_expiration_date: Optional[str] = None,
        delivery_expiration_timezone: Optional[str] = None,
        contact_security: bool = True,
        do_not_create_update_caches: bool = True,
        overwrite_older_version: bool = False,
        re_run_hl: bool = True,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: Optional[str] = None,
    ):
        """Alter the subscription.
        Args:
            name (str, optional): name of the subscription
            multiple_contents (bool, optional): whether multiple contents are
                allowed
            allow_delivery_changes (bool, optional): whether the
                recipients can change the delivery of the subscription
            allow_personalization_changes (bool, optional): whether
                the recipients can personalize the subscription
            allow_unsubscribe (bool, optional): whether the recipients
                can unsubscribe from the subscription
            send_now (bool, optional): indicates whether to execute the
                subscription immediately
            owner_id (str, optional): ID of the subscription owner, by
                default logged in user ID
            schedules (list[str] | str | Schedule | list[Schedule], optional):
                Schedules IDs or Schedule objects
            recipients (list[dict] | dict, optional): list of recipients IDs
                or dicts
            delivery (dict | Delivery, optional): delivery object or dict
            delivery_expiration_date (str, optional): expiration date
                of the subscription, format should be yyyy - MM - dd
            delivery_expiration_timezone (str, optional): expiration timezone
                of the subscription
            contact_security (bool): whether to use contact security for each
                contact group member
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                cache in the history list
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list
            re_run_hl (bool): whether subscription will re-run against
                warehouse
            delivery_notification_enabled (bool): Whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                Notification details
        """
        notification_address_id = delivery_personal_notification_address_id

        return super().alter(
            name=name,
            multiple_contents=multiple_contents,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe,
            send_now=send_now,
            owner_id=owner_id,
            schedules=schedules,
            recipients=recipients,
            delivery=delivery,
            custom_msg=custom_msg,
            delivery_expiration_date=delivery_expiration_date,
            delivery_expiration_timezone=delivery_expiration_timezone,
            contact_security=contact_security,
            do_not_create_update_caches=do_not_create_update_caches,
            overwrite_older_version=overwrite_older_version,
            re_run_hl=re_run_hl,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=notification_address_id,
        )
