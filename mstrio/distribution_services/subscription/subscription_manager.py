from typing import List, Union
from mstrio.utils import helper
import mstrio.api.subscriptions as subscriptions_
from mstrio.distribution_services.subscription.subscription import Subscription
from mstrio.distribution_services.subscription.content import Content
import mstrio.config as config
from mstrio.connection import Connection


def list_subscriptions(connection: Connection, application_id: str = None,
                       application_name: str = None, to_dictionary: bool = False,
                       **filters) -> Union[List[Subscription], List[dict]]:
    """Lists all subscriptions filtered by passed params.
    Specify either `application_id` or `application_name`.
    When `application_id` is provided (not `None`), `application_name` is
    omitted.

    Args:
        connection(object): MicroStrategy connection object
        application_id: Application ID
        application_name: Application name
        to_dictionary: If True returns a list of subscription dicts,
            otherwise returns a list of subscription objects
        **filters: Available filter parameters: ['id', 'name', 'editable',
            'allowDeliveryChanges', 'allowPersonalizationChanges',
            'allowUnsubscribe', 'dateCreated', 'dateModified', 'owner',
            'schedules', 'contents', 'recipients', 'delivery']
    """
    # TODO add limit parameter
    # TODO move to subscription module
    application_id = Subscription._app_id_check(connection, application_id, application_name)
    response = subscriptions_.list_subscriptions(connection, application_id)
    subscription_list = helper.filter_list_of_dicts(response.json()['subscriptions'], **filters)

    if to_dictionary:
        return subscription_list
    else:
        subscription_obj_list = []
        for subscription in subscription_list:
            sub = Subscription.from_dict(connection=connection, application_id=application_id,
                                         dictionary=subscription)
            subscription_obj_list.append(sub)
        return subscription_obj_list


class SubscriptionManager:
    """Manage subscriptions."""

    def __init__(self, connection: Connection, application_id: str = None,
                 application_name: str = None):
        """Initialize the SubscriptionManager object.
        Specify either `application_id` or `application_name`.
        When `application_id` is provided (not `None`), `application_name` is
        omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            application_id: Application ID
        """
        self.connection = connection
        self.application_id = Subscription._app_id_check(connection, application_id,
                                                         application_name)

    def list_subscriptions(self, to_dictionary: bool = False, **filters):
        """Lists all subscriptions filtered by passed params.

        Args:
            to_dictionary: If True returns a list of subscription dicts,
                otherwise returns a list of subscription objects
            **filters: Available filter parameters: ['id', 'name', 'editable',
                'allowDeliveryChanges', 'allowPersonalizationChanges',
                'allowUnsubscribe', 'dateCreated', 'dateModified', 'owner',
                'schedules', 'contents', 'recipients', 'delivery']
        """
        return list_subscriptions(connection=self.connection, application_id=self.application_id,
                                  to_dictionary=to_dictionary, **filters)

    def delete(self, subscriptions: Union[List[Subscription], List[str]], force=False) -> bool:
        """Deletes all passed subscriptions. Returns True if successfully
        removed all subscriptions.

        Args:
            subscriptions: list of subscriptions to be deleted
        """
        subscriptions = subscriptions if isinstance(subscriptions, list) else [subscriptions]
        if not subscriptions and config.verbose:
            print("No subscriptions passed.")
        else:
            temp_subs = []
            for subscription in subscriptions:
                subscription = subscription if isinstance(
                    subscription, Subscription) else Subscription(self.connection, subscription,
                                                                  self.application_id)
                temp_subs.append(subscription)
            subscriptions = temp_subs
            succeeded = 0
            user_input = 'N'
            if not force:
                to_be_deleted = [
                    "Subscription '{}' with ID: '{}'".format(sub.name, sub.id)
                    for sub in subscriptions
                ]
                print("Found subscriptions:")
                for sub in to_be_deleted:
                    print(sub)
                user_input = input("Are you sure you want to delete all of them? [Y/N]: ")
            if force or user_input == 'Y':
                succeeded = 0
                for subscription in subscriptions:
                    response = subscriptions_.remove_subscription(
                        self.connection,
                        subscription.id,
                        self.application_id,
                        error_msg="Subscription '{}' with id '{}'' could not be deleted.".format(
                            subscription.name, subscription.id),
                        exception_type=UserWarning,
                    )
                    if response.ok:
                        succeeded += 1
                        if config.verbose:
                            print("Deleted subscription '{}' with ID '{}''.".format(
                                subscription.name, subscription.id))

                return succeeded == len(subscriptions)

    def execute(self, subscriptions: Union[List[Subscription], List[str]]):
        """Executes all passed subscriptions.

        Args:
            subscriptions: list of subscriptions to be executed
        """
        if not subscriptions and config.verbose:
            print("No subscriptions passed.")
        else:
            subscriptions = subscriptions if isinstance(subscriptions, list) else [subscriptions]
            for subscription in subscriptions:
                subscription = subscription if isinstance(
                    subscription, Subscription) else Subscription(self.connection, subscription,
                                                                  self.application_id)
                if subscription.delivery['mode'] == 'EMAIL':
                    subscription.execute()
                else:
                    msg = (f"Subscription '{subscription.name}' with ID '{subscription.id}' "
                           "could not be executed. Delivery mode '{subscription.delivery['mode']}'"
                           " is not supported.")
                    helper.exception_handler(msg, UserWarning)

    def available_bursting_attributes(self, content: Union[dict, "Content"]):
        """Get a list of available attributes for bursting feature, for a given
        content.

        Args:
            content: content dictionary or Content object
                (from subscription.content)
        """
        c_id = content['id'] if isinstance(content, dict) else content.id
        c_type = content['type'] if isinstance(content, dict) else content.type

        response = subscriptions_.bursting_attributes(self.connection, self.application_id, c_id,
                                                      c_type.upper())

        if response.ok:
            return response.json()['burstingAttributes']

    def available_recipients(self, content_id: str = None, content_type: str = None,
                             content: "Content" = None, delivery_type='EMAIL') -> List[dict]:
        """List available recipients for a subscription contents.
        Specify either both `content_id` and `content_type` or just `content`
        object.

        Args:
            content_id: ID of the content
            content_type: type of the content
            content: Content object
            delivery_type: The delivery of the subscription, available values
                are: [EMAIL, FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP].
        """
        if content_id and content_type:
            pass
        elif isinstance(content, Content):
            content_id = content.id
            content_type = content.type
        else:
            helper.exception_handler('Specify either a content ID and type or content object.',
                                     ValueError)

        body = {
            "contents": [{
                "id": content_id,
                "type": content_type
            }],
        }

        response = subscriptions_.available_recipients(self.connection, self.application_id, body,
                                                       delivery_type)

        if response.ok and config.verbose:
            return response.json()['recipients']
