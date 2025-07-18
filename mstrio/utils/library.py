import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import documents, library, objects
from mstrio.api.schedules import get_contents_schedule
from mstrio.helpers import IServerError
from mstrio.distribution_services.schedule import Schedule
from mstrio.users_and_groups import User, UserGroup, UserOrGroup
from mstrio.utils.helper import get_response_json
from mstrio.utils.version_helper import method_version_handler
from mstrio.object_management.library_shortcut import LibraryShortcut

if TYPE_CHECKING:
    from mstrio.utils.entity import Entity


REPORT_PROPERTIES_PROPERTY_SET_ID = "70A27C6E239911D5BF2200B0D02A21E0"
ALLOW_HTML_EXECUTION_PROPERTY_INDEX = 12


logger = logging.getLogger(__name__)


class LibraryMixin:
    """Mixin class for methods related to publishing objects to Library.
    Must be used with Entity or its subclasses. The class must:
        - populate its `instance_id` field,
        - be able to fetch its `recipients` field.

    """

    def _validate_user_or_group(self: "Entity", recipient_id: str) -> str | None:
        valid = False
        for cls in (User, UserGroup):
            try:
                cls(self.connection, id=recipient_id)
                valid = True
                break
            except IServerError:
                continue
        if not valid:
            if config.verbose:
                logger.info(
                    f'{recipient_id} is not a valid value for User or UserGroup ID'
                )
            return None
        return recipient_id

    def _recipients_to_ids(self, recipients: list[UserOrGroup | str]) -> list[str]:
        """Convert a list of str, User and UserGroup objects to a list of
        recipient (User or UserGroup) IDs and validate the ID strings.

        Args:
            recipients (list[UserOrGroup | str]): List of User or UserGroup
            references (objects or strs).
        Returns:
            list[str]: List of user IDs.
        """
        recipient_ids = []
        for recipient in recipients:
            if isinstance(recipient, str):
                if self._validate_user_or_group(recipient):
                    recipient_ids.append(recipient)
            elif isinstance(recipient, (User, UserGroup)):
                recipient_ids.append(recipient.id)
            else:
                raise ValueError(
                    'Please provide a list of User, UserGroup or str elements.'
                )
        return recipient_ids

    def publish(
        self: "Entity",
        recipients: UserOrGroup | str | list[UserOrGroup | str] | None = None,
    ):
        """Publish the document for authenticated user. If `recipients`
        parameter is specified publishes the document for the given users.

        Args:
            recipients(UserOrGroup | list[UserOrGroup | str] | str, optional):
                list of users or user groups to publish the document to
                (can be a list of IDs and User and UserGroup elements)
        """
        if not isinstance(recipients, list) and recipients is not None:
            recipients = [recipients]

        if recipients is None:
            recipients = [self.connection.user_id]
        recipients = self._recipients_to_ids(recipients)

        body = {'id': self.id, 'recipients': recipients}
        library.publish_document(self.connection, body)
        self.fetch(attr='recipients')

    def unpublish(
        self: "Entity",
        recipients: UserOrGroup | str | list[UserOrGroup | str] | None = None,
    ):
        """Unpublish the document for all users it was previously published to.
        If `recipients` parameter is specified unpublishes the document for the
        given users or user groups.

        Args:
            recipients(UserOrGroup | list[UserOrGroup | str] | str, optional):
                list of users or user groups to unpublish the document from
                (can be a list of IDs and User and UserGroup elements)
        """

        if recipients is None:
            library.unpublish_document(self.connection, id=self.id)
        else:
            if not isinstance(recipients, list):
                recipients = [recipients]
            recipients = self._recipients_to_ids(recipients)

            for recipient_id in recipients:
                library.unpublish_document_for_user(
                    self.connection, document_id=self.id, recipient_id=recipient_id
                )

        self.fetch(attr='recipients')

    @method_version_handler('11.3.0600')
    def list_available_schedules(
        self: "Entity",
        to_dictionary: bool = False,
        name: str | None = None,
        limit: int | None = None,
    ) -> list["Schedule"] | list[dict]:
        """Get a list of schedules available for the object instance.

        Args:
            to_dictionary (bool, optional): If True returns a list of
                dictionaries, otherwise returns a list of Schedules.
                False by default.
            name (str, optional): If specified, filters the schedules to those
                with the specified substring in their name.
            limit (int, optional): If specified, limits the number of schedules
                returned.

        Returns:
            List of Schedule objects or list of dictionaries.
        """
        schedules_list: list[dict] = (
            get_response_json(
                get_contents_schedule(
                    connection=self.connection,
                    project_id=self.connection.project_id,
                    body={'id': self.id, 'type': 'document'},
                )
            )
        ).get('schedules')

        if name:
            schedules_list = [
                schedule for schedule in schedules_list if name in schedule['name']
            ]
        if limit is not None:
            schedules_list = schedules_list[:limit]

        if to_dictionary:
            return schedules_list
        else:
            return [
                Schedule.from_dict(connection=self.connection, source=schedule_id)
                for schedule_id in schedules_list
            ]

    def share_to(self: "Entity", users: UserOrGroup | list[UserOrGroup]):
        """Shares the document to the listed users' libraries.

        Args:
            users(UserOrGroup | list[UserOrGroup]): list of users or user
                groups to publish the document to (can be a list of IDs or a
                list of User and UserGroup elements).
        """
        self.publish(users)

    def is_html_js_execution_enabled(self: "Entity") -> bool | None:
        """Check whether HTML and JavaScript execution is enabled
        for the document.

        Returns:
            bool: True if HTML and JavaScript execution is enabled,
                False otherwise.
        """
        res = get_response_json(
            objects.get_property_set(
                self.connection,
                id=self.id,
                obj_type=self._OBJECT_TYPE.value,
                property_set_id=REPORT_PROPERTIES_PROPERTY_SET_ID,
            )
        )
        prop_in_list = [
            prop for prop in res if prop['id'] == ALLOW_HTML_EXECUTION_PROPERTY_INDEX
        ]
        try:
            prop = bool(prop_in_list[0]['value'])
        except IndexError:
            raise AttributeError(
                "This object does not support HTML/JS execution property"
            )

        return prop

    def set_html_js_execution_enabled(self: "Entity", enabled: bool) -> None:
        """Enable or disable HTML and JavaScript execution for the document.

        Args:
            enabled (bool): True to enable HTML and JavaScript execution,
                False to disable.
        """

        body = [
            {
                "properties": [
                    {"value": int(enabled), "id": ALLOW_HTML_EXECUTION_PROPERTY_INDEX}
                ],
                "id": REPORT_PROPERTIES_PROPERTY_SET_ID,
            }
        ]
        objects.update_property_set(
            self.connection, id=self.id, obj_type=self._OBJECT_TYPE.value, body=body
        )

    def get_library_shortcut(self: "Entity") -> "LibraryShortcut":
        response: dict = documents.get_document_shortcut(
            connection=self.connection,
            document_id=self.id,
            instance_id=self.instance_id,
        ).json()
        return LibraryShortcut.from_dict(connection=self.connection, source=response)
