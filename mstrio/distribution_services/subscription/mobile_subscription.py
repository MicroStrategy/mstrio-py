from mstrio.connection import Connection
from mstrio.distribution_services.schedule.schedule import Schedule
from mstrio.distribution_services.subscription import Subscription
from mstrio.distribution_services.subscription.content import Content
from mstrio.distribution_services.subscription.delivery import ClientType, Delivery
from mstrio.utils.version_helper import class_version_handler


@class_version_handler('11.3.0960')
class MobileSubscription(Subscription):
    """Class representation of Strategy One Mobile Subscription
    object."""

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        subscription_id: str | None = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Initializes MobileSubscription object and populates it with
        I-Server data if id or subscription_id is passed.
        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.
        Args:
            connection (Connection): Strategy One connection object returned
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
        project_id: str | None = None,
        project_name: str | None = None,
        multiple_contents: bool | None = False,
        allow_delivery_changes: bool | None = None,
        allow_personalization_changes: bool | None = None,
        allow_unsubscribe: bool | None = None,
        send_now: bool | None = None,
        owner_id: str | None = None,
        schedules: str | list[str] | Schedule | list[Schedule] | None = None,
        contents: Content | None = None,
        recipients: list[dict] | list[str] | None = None,
        delivery: Delivery | dict | None = None,
        delivery_expiration_date: str | None = None,
        delivery_expiration_timezone: str | None = None,
        contact_security: bool = True,
        mobile_client_type: ClientType = ClientType.PHONE,
        device_id: str | None = None,
        do_not_create_update_caches: bool = False,
        overwrite_older_version: bool = False,
        re_run_hl: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: str | None = None,
    ) -> "MobileSubscription":
        """Creates a new mobile subscription.
        Args:
            connection (Connection): a Strategy One connection object
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
            mobile_client_type: The mobile client type
            device_id: The mobile target project
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                cache in the history list
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list
            re_run_hl (bool): whether subscription will re-run against warehouse
            delivery_notification_enabled (bool): whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                notification details

        Notes:
            To create a subscription with prompts, you need to provide
            the report instance ID with answered prompts for the content.
            Example:
            >>>contents=Content(
            >>>    id="<report_id>",
            >>>    type=Content.Type.REPORT,
            >>>    personalization=Content.Properties(
            >>>        format_type=Content.Properties.FormatType.PDF,
            >>>        prompt=Content.Properties.Prompt(
            >>>            enabled=True,
            >>>            instance_id="<instance_id>",
            >>>        ),
            >>>    ),
            >>>)
        """
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
            delivery_mode=Delivery.DeliveryMode.MOBILE,
            delivery_expiration_date=delivery_expiration_date,
            delivery_expiration_timezone=delivery_expiration_timezone,
            contact_security=contact_security,
            mobile_client_type=mobile_client_type,
            device_id=device_id,
            do_not_create_update_caches=do_not_create_update_caches,
            overwrite_older_version=overwrite_older_version,
            re_run_hl=re_run_hl,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=(
                delivery_personal_notification_address_id
            ),
        )

    def alter(
        self,
        name: str | None = None,
        contents: Content | None = None,
        multiple_contents: bool | None = None,
        allow_delivery_changes: bool | None = None,
        allow_personalization_changes: bool | None = None,
        allow_unsubscribe: bool | None = None,
        send_now: bool | None = None,
        owner_id: str | None = None,
        schedules: str | list[str] | Schedule | list[Schedule] | None = None,
        recipients: list[dict] | list[str] | None = None,
        delivery: Delivery | dict | None = None,
        delivery_expiration_date: str | None = None,
        delivery_expiration_timezone: str | None = None,
        contact_security: bool = True,
        mobile_client_type: ClientType | None = None,
        device_id: str | None = None,
        do_not_create_update_caches: bool = False,
        overwrite_older_version: bool = False,
        re_run_hl: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: str | None = None,
        custom_msg: str | None = None,
    ):
        """Alter subscription.
        Args:
            name (str): name of the subscription
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
            mobile_client_type: The mobile client type
            device_id: The mobile target project
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                cache in the history list
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list
            re_run_hl (bool): whether subscription will re-run against warehouse
            delivery_notification_enabled (bool): whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                notification details
            custom_msg (str, optional): customized message displayed when
                Subscription has been successfully altered
        """
        # Alias, for formatting purposes
        notification_address_id = delivery_personal_notification_address_id
        return super().alter(
            name=name,
            contents=contents,
            multiple_contents=multiple_contents,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe,
            send_now=send_now,
            owner_id=owner_id,
            schedules=schedules,
            recipients=recipients,
            delivery=delivery,
            delivery_expiration_date=delivery_expiration_date,
            delivery_expiration_timezone=delivery_expiration_timezone,
            contact_security=contact_security,
            mobile_client_type=mobile_client_type,
            device_id=device_id,
            do_not_create_update_caches=do_not_create_update_caches,
            overwrite_older_version=overwrite_older_version,
            re_run_hl=re_run_hl,
            delivery_notification_enabled=delivery_notification_enabled,
            delivery_personal_notification_address_id=notification_address_id,
            custom_msg=custom_msg,
        )
