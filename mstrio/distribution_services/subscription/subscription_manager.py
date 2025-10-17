import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import subscriptions as subscriptions_
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.resolvers import (
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.version_helper import (
    class_version_handler,
    is_server_min_version,
    method_version_handler,
)

from . import (
    CacheUpdateSubscription,
    EmailSubscription,
    FileSubscription,
    FTPSubscription,
    HistoryListSubscription,
    MobileSubscription,
    Subscription,
)
from .content import Content
from .delivery import Delivery

if TYPE_CHECKING:
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


@method_version_handler('11.2.0203')
def list_subscriptions(
    connection: Connection,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    last_run: bool = False,
    **filters,
) -> list["Subscription"] | list[dict]:
    """Get all subscriptions per project as list of Subscription objects or
    dictionaries.

    Optionally filter the subscriptions by specifying filters.

    Args:
        connection (Connection): Strategy One connection object
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        to_dictionary (bool): If True returns a list of subscription dicts,
            otherwise (default) returns a list of subscription objects
        limit (int | None): limit the number of elements returned. If `None`
            (default), all objects are returned.
        last_run (bool): If True, adds the last time that the subscription ran.
        **filters: Available filter parameters: ['id', 'multiple_contents',
            'name', 'editable', 'allow_delivery_changes'
            'allow_personalization_changes', 'allow_unsubscribe',
            'date_created', 'date_modified', 'owner', 'delivery']
    """

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )
    chunk_size = 1000 if is_server_min_version(connection, '11.3.0300') else 1000000

    validate_owner_key_in_filters(filters)

    if (
        not is_server_min_version(connection, '11.4.0600')
        and last_run
        and config.verbose
    ):
        logger.info('`last_run` argument is available from iServer Version 11.4.0600')

    msg = 'Error getting subscription list.'
    objects = helper.fetch_objects_async(
        connection=connection,
        api=subscriptions_.list_subscriptions,
        async_api=subscriptions_.list_subscriptions_async,
        limit=limit,
        chunk_size=chunk_size,
        filters=filters,
        error_msg=msg,
        dict_unpack_value="subscriptions",
        project_id=proj_id,
        last_run=last_run,
    )

    if to_dictionary:
        return objects
    return [
        dispatch_from_dict(
            source=obj,
            connection=connection,
            project_id=proj_id,
        )
        for obj in objects
    ]


DeliveryMode = Delivery.DeliveryMode
subscription_type_from_delivery_mode_dict = {
    DeliveryMode.CACHE: CacheUpdateSubscription,
    DeliveryMode.EMAIL: EmailSubscription,
    DeliveryMode.FILE: FileSubscription,
    DeliveryMode.FTP: FTPSubscription,
    DeliveryMode.HISTORY_LIST: HistoryListSubscription,
    DeliveryMode.MOBILE: MobileSubscription,
}


def get_subscription_type_from_delivery_mode(mode: DeliveryMode):
    """Returns the subscription type of the provided Delivery Mode.

    Args:
        mode: DeliveryMode object of which to get the subscription type"""
    return subscription_type_from_delivery_mode_dict.get(mode, Subscription)


def dispatch_from_dict(
    source: dict, connection: Connection, project_id: str
) -> 'Subscription':
    """Returns the subscription type object from the provided source

    Args:
        source: dictionary of an object to return from the specified
            subscription
        connection: Strategy One connection object returned
            by `connection.Connection()`
        project_id: Project ID

    Returns:
        Subscription: The subscription type object
    """
    delivery_mode = DeliveryMode(source["delivery"]["mode"])
    sub_type = get_subscription_type_from_delivery_mode(delivery_mode)
    return sub_type.from_dict(source, connection, project_id)


@class_version_handler('11.2.0203')
class SubscriptionManager:
    """Manage subscriptions."""

    def __init__(
        self,
        connection: Connection,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Initialize the SubscriptionManager object.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        self.connection = connection
        self.project_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )

    def list_subscriptions(
        self,
        to_dictionary: bool = False,
        limit: int | None = None,
        last_run: bool = False,
        **filters,
    ):
        """Get all subscriptions as list of Subscription objects or
        dictionaries.

        Optionally filter the subscriptions by specifying filters.

        Args:
            to_dictionary: If True returns a list of subscription dicts,
                otherwise returns a list of subscription objects
            limit: limit the number of elements returned. If `None` (default),
                all objects are returned.
            last_run: If True, adds the last time that the subscription ran.
            **filters: Available filter parameters: ['id', 'name', 'editable',
                'allowDeliveryChanges', 'allowPersonalizationChanges',
                'allowUnsubscribe', 'dateCreated', 'dateModified', 'owner',
                'schedules', 'contents', 'recipients', 'delivery']
        """
        return list_subscriptions(
            connection=self.connection,
            project_id=self.project_id,
            to_dictionary=to_dictionary,
            limit=limit,
            last_run=last_run,
            **filters,
        )

    def _normalize_subscriptions(self, subscriptions) -> list[Subscription]:
        if not isinstance(subscriptions, list):
            subscriptions = [subscriptions]
        return [
            (
                sub
                if isinstance(sub, Subscription)
                else Subscription(
                    connection=self.connection, id=sub, project_id=self.project_id
                )
            )
            for sub in subscriptions
        ]

    def _delete_subscription(self, subscription) -> bool:
        response = subscriptions_.remove_subscription(
            self.connection,
            subscription.id,
            self.project_id,
            error_msg=(
                f"Subscription '{subscription.name}' with id "
                f"'{subscription.id}' could not be deleted."
            ),
            exception_type=UserWarning,
        )
        if response.ok and config.verbose:
            logger.info(
                f"Deleted subscription '{subscription.name}' "
                f"with ID '{subscription.id}'."
            )
        return response.ok

    def create_copy(
        self,
        subscription: Subscription | str,
        name: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        send_now: bool = False,
    ):
        """Create a copy of the subscription on the I-Server.

        Args:
            subscription (Subscription | str): Subscription object or ID of the
                subscription to be copied
            name (str, optional): New name of the object. If None, a default
                name is generated, such as 'Old Name (1)'
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            send_now (bool): indicates whether to execute the subscription
                immediately.

        Returns:
            New object, the copied subscription. The subscription's name might
            be changed to avoid conflicts with existing objects.
        """
        # Subscription is not a Metadata object and as such cannot be copied
        # with the objects' copy endpoint.
        # For the same reason, duplicate name has to be determined client-side
        if not isinstance(subscription, Subscription):
            subscription = Subscription(
                connection=self.connection, id=subscription, project_id=self.project_id
            )
        name = name or subscription.name
        existing_names: list[str] = [
            s['name']
            for s in list_subscriptions(
                subscription.connection,
                to_dictionary=True,
                project=project,
                project_id=project_id,
                project_name=project_name,
            )
        ]
        new_name = helper.deduplicated_name(name, existing_names)

        proj_id = get_project_id_from_params_set(
            self.connection,
            project,
            project_id or self.project_id,
            project_name,
        )

        return Subscription._Subscription__create(
            connection=subscription.connection,
            name=new_name,
            contents=subscription.contents,
            project_id=proj_id,
            project_name=project_name,
            multiple_contents=subscription.multiple_contents,
            allow_delivery_changes=subscription.allow_delivery_changes,
            allow_personalization_changes=subscription.allow_personalization_changes,
            allow_unsubscribe=subscription.allow_unsubscribe,
            send_now=send_now,
            owner_id=subscription.owner.id,
            schedules=subscription.schedules,
            recipients=subscription.recipients,
            delivery=subscription.delivery,
        )

    def delete(
        self, subscriptions: list[Subscription] | list[str], force=False
    ) -> bool:
        """Deletes all passed subscriptions. Returns True if successfully
        removed all subscriptions.

        Args:
            subscriptions (list[Subscription] | list[str]):
                list of subscriptions to be deleted
            force (bool, optional): if True skips the prompt asking for
                confirmation before deleting subscriptions. False by default.
        """
        subscriptions = self._normalize_subscriptions(subscriptions)
        if not subscriptions:
            if config.verbose:
                logger.info('No subscriptions passed.')
            return False

        if not force:
            logger.info("Found subscriptions:")
            for sub in subscriptions:
                logger.info(f"Subscription '{sub.name}' with ID: '{sub.id}'")
            if input("Are you sure you want to delete all of them? [Y/N]: ") != 'Y':
                return False

        succeeded = sum(
            1
            for subscription in subscriptions
            if self._delete_subscription(subscription)
        )

        return succeeded == len(subscriptions)

    def execute(self, subscriptions: list[Subscription] | list[str]) -> None:
        """Executes all passed subscriptions.

        Args:
            subscriptions (list[Subscription] | list[str]):
                list of subscription objects or subscription ids to be executed
        """
        if not subscriptions:
            if config.verbose:
                logger.info('No subscriptions passed.')
            return

        subscriptions = (
            subscriptions if isinstance(subscriptions, list) else [subscriptions]
        )
        for subscription in subscriptions:
            if not isinstance(subscription, Subscription):
                subscription = Subscription(
                    connection=self.connection,
                    id=subscription,
                    project_id=self.project_id,
                )

            if subscription.delivery.mode in (
                'EMAIL',
                'FILE',
                'HISTORY_LIST',
                'FTP',
            ):
                subscription.execute()
            else:
                msg = (
                    f"Subscription '{subscription.name}' with ID "
                    f"'{subscription.id}' could not be executed. Delivery mode "
                    f"'{subscription.delivery.mode}' is not supported."
                )
                helper.exception_handler(msg, UserWarning)

    @method_version_handler('11.3.0000')
    def available_bursting_attributes(self, content: dict | Content) -> list[dict]:
        """Get a list of available attributes for bursting feature, for a given
        content.

        Args:
            content (dict | Content): content dictionary or Content object
                (from subscription.content)
        """
        c_id = content.id if isinstance(content, Content) else content.get('id')
        c_type = (
            get_enum_val(content.type, Content.Type)
            if isinstance(content, Content)
            else content.get('type')
        )

        response = subscriptions_.bursting_attributes(
            self.connection, self.project_id, c_id, c_type.upper()
        )

        return response.json()['burstingAttributes']

    @method_version_handler('11.3.0000')
    def available_recipients(
        self,
        content_id: str | None = None,
        content_type: str | Content.Type | None = None,
        content: 'Content | None' = None,
        delivery_type: str | DeliveryMode = 'EMAIL',
    ) -> list[dict]:
        """List available recipients for a subscription contents.
        Specify either both `content_id` and `content_type` or just `content`
        object.

        Args:
            content_id (str): ID of the content.
            content_type (str | Content.Type): type of the content.
            content (Content): Content object.
            delivery_type (str | DeliveryMode): The delivery type
                of the subscription.
        """
        if isinstance(content, Content):
            content_id = content.id
            content_type = content.type
        elif not (content_id and content_type):
            helper.exception_handler(
                'Specify either a content ID and type or content object.', ValueError
            )

        body = {
            "contents": [
                {"id": content_id, "type": get_enum_val(content_type, Content.Type)}
            ],
        }

        response = subscriptions_.available_recipients(
            connection=self.connection,
            project_id=self.project_id,
            body=body,
            delivery_type=get_enum_val(delivery_type, DeliveryMode),
        )

        return response.json()['recipients']
