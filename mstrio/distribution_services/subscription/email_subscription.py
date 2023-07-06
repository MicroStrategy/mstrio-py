from mstrio.connection import Connection

from ..schedule import Schedule
from .base_subscription import Subscription
from .content import Content


class EmailSubscription(Subscription):
    """Class representation of MicroStrategy Email Subscription object."""

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        subscription_id: str | None = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Initialize EmailSubscription object, populates it with I-Server data
        if id or subscription_id is passed.
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
        project_id: str | None = None,
        project_name: str | None = None,
        allow_delivery_changes: bool | None = None,
        allow_personalization_changes: bool | None = None,
        allow_unsubscribe: bool = True,
        send_now: bool | None = None,
        owner_id: str | None = None,
        schedules: str | list[str] | Schedule | list[Schedule] | None = None,
        contents: Content | None = None,
        recipients: list[str] | list[dict] = None,
        delivery_expiration_date: str | None = None,
        delivery_expiration_timezone: str | None = None,
        contact_security: bool | None = None,
        space_delimiter: str | None = None,
        email_subject: str | None = None,
        email_message: str | None = None,
        email_send_content_as: str = 'data',
        overwrite_older_version: bool = False,
        filename: str | None = None,
        compress: bool = False,
        zip_filename: str | None = None,
        zip_password_protect: bool | None = None,
        zip_password: str | None = None,
    ):
        """Creates a new email subscription.

        Args:
            connection (Connection): a MicroStrategy connection object
            name (str): name of the subscription,
            project_id (str, optional): project ID,
            project_name (str, optional): project name,
            allow_delivery_changes (bool, optional): whether the recipients can
                change the delivery of the subscription,
            allow_personalization_changes (bool, optional): whether the
                recipients can personalize the subscription,
            allow_unsubscribe (bool, optional): whether the recipients can
                unsubscribe from the subscription,
            send_now (bool, optional): indicates whether to execute the
                subscription immediately,
            owner_id (str, optional): ID of the subscription owner, by default
                logged in user ID,
            schedules (str | list[str] | Schedule | list[Schedule], optional):
                Schedules IDs or Schedule objects,
            contents (Content, optional): The content settings.
            recipients (list[str] | list[dict], optional): list of recipients
                IDs or dicts,
            delivery_expiration_date (str, optional): expiration date of the
                subscription, format should be yyyy - MM - dd,
            delivery_expiration_timezone (str, optional): expiration timezone
                of the subscription, example value 'Europe/London'
            contact_security (bool): whether to use contact security for each
                contact group member
            filename (str, optional): the filename that will be delivered when
                the subscription is executed,
            compress (bool): whether to compress the file
            space_delimiter (str, optional): space delimiter,
            email_subject (str, optional): email subject associated with
                the subscription,
            email_message (str, optional): email body of subscription,
            email_send_content_as (str, enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename (str, optional): filename of the compressed content,
            zip_password_protect (bool, optional): whether to password protect
                zip file,
            zip_password (str, optional): optional password for the compressed
                file
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
            delivery_mode='EMAIL',
            delivery_expiration_date=delivery_expiration_date,
            delivery_expiration_timezone=delivery_expiration_timezone,
            contact_security=contact_security,
            email_subject=email_subject,
            email_message=email_message,
            filename=filename,
            compress=compress,
            space_delimiter=space_delimiter,
            email_send_content_as=email_send_content_as,
            overwrite_older_version=overwrite_older_version,
            zip_filename=zip_filename,
            zip_password_protect=zip_password_protect,
            zip_password=zip_password,
        )
