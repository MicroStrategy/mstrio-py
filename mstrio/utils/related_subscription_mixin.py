from typing import TYPE_CHECKING

from mstrio.api import subscriptions
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.distribution_services import Event, Schedule, Subscription  # noqa: F401
    from mstrio.project_objects import Dashboard, Report  # noqa: F401
    from mstrio.users_and_groups import User  # noqa: F401

RelatedSubscriptionTypes = 'User | Dashboard | Report | Schedule | Event'


class RelatedSubscriptionMixin:
    """RelatedSubscriptionMixin class adds listing support for supported
    objects."""

    @method_version_handler('11.4.0600')
    def list_related_subscriptions(
        self: RelatedSubscriptionTypes, to_dictionary: bool = False
    ) -> list['Subscription'] | list[dict]:
        """List all subscriptions that are dependent on the object.

        Args:
            to_dictionary (bool, optional): If True returns a list of
                subscription dicts, otherwise (default) returns a list of
                subscription objects
        """
        object_type = self.__class__.__name__.lower()

        if object_type in ['user', 'event', 'schedule']:
            project_id = None
        else:
            project_id = get_project_id_from_params_set(
                self.connection,
                self.project_id,
                None,
                None,
            )

        objects = (
            subscriptions.get_dependent_subscriptions(
                self.connection, self.id, object_type, project_id
            )
            .json()
            .get('subscriptions', [])
        )

        if to_dictionary:
            return objects

        from mstrio.distribution_services.subscription.subscription_manager import (
            dispatch_from_dict,
        )

        return [
            dispatch_from_dict(
                source=obj,
                connection=self.connection,
                project_id=project_id or obj.get('project', {}).get('id'),
            )
            for obj in objects
        ]
