from typing import List, Optional, Union

from mstrio.connection import Connection

from ..schedule import Schedule
from .base_subscription import Subscription
from .content import Content


class EmailSubscription(Subscription):
    """Class representation of MicroStrategy Email Subscription object."""
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, subscription_id: Optional[str] = None,
                 project_id: Optional[str] = None, project_name: Optional[str] = None):
        """Initialize EmailSubscription object, populates it with I-Server data
        if subscription_id is passed.
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
        allow_unsubscribe: bool = True,
        send_now: Optional[bool] = None,
        owner_id: Optional[str] = None,
        schedules: Optional[Union[str, List[str], Schedule, List[Schedule]]] = None,
        contents: Optional[Content] = None,
        recipients: Union[List[str], List[dict]] = None,
        delivery_expiration_date: Optional[str] = None,
        contact_security: Optional[bool] = None,
        space_delimiter: Optional[str] = None,
        email_subject: Optional[str] = None,
        email_message: Optional[str] = None,
        email_send_content_as: str = 'data',
        overwrite_older_version: bool = False,
        filename: Optional[str] = None,
        compress: bool = False,
        zip_filename: Optional[str] = None,
        zip_password_protect: Optional[bool] = None,
        zip_password: Optional[str] = None
    ):
        """Creates a new email subscription.

        Args:
            connection(Connection): a MicroStrategy connection object
            name(str): name of the subscription,
            project_id(str): project ID,
            project_name(str): project name,
            allow_delivery_changes(bool): whether the recipients can change
                the delivery of the subscription,
            allow_personalization_changes(bool): whether the recipients can
                personalize the subscription,
            allow_unsubscribe(bool): whether the recipients can unsubscribe
                from the subscription,
            send_now(bool): indicates whether to execute the subscription
                immediately,
            owner_id(str): ID of the subscription owner, by default logged in
                user ID,
            schedules (Union[str, List[str], Schedule, List[Schedule]]):
                Schedules IDs or Schedule objects,
            contents(Content): The content settings.
            recipients(Union[List[str], List[dict]]): list of recipients IDs
                or dicts,
            delivery_expiration_date(str): expiration date of the subscription,
                format should be yyyy - MM - dd,
            contact_security(bool): whether to use contact security for each
                contact group member,
            filename(str): the filename that will be delivered when
                the subscription is executed,
            compress(bool): whether to compress the file
            space_delimiter(str): space delimiter,
            email_subject(str): email subject associated with the subscription,
            email_message(str): email body of subscription,
            email_send_content_as(str, enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version(bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename(str): filename of the compressed content,
            zip_password_protect(bool): whether to password protect zip file,
            zip_password(str): optional password for the compressed file
        """
        return super()._Subscription__create(
            connection=connection, name=name, project_id=project_id, project_name=project_name,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe, send_now=send_now, owner_id=owner_id,
            schedules=schedules, contents=contents, recipients=recipients, delivery_mode='EMAIL',
            delivery_expiration_date=delivery_expiration_date, contact_security=contact_security,
            email_subject=email_subject, email_message=email_message, filename=filename,
            compress=compress, space_delimiter=space_delimiter,
            email_send_content_as=email_send_content_as,
            overwrite_older_version=overwrite_older_version, zip_filename=zip_filename,
            zip_password_protect=zip_password_protect, zip_password=zip_password)
