import logging
from collections.abc import Callable
from datetime import datetime
from enum import auto
from functools import partial
from pprint import pformat
from typing import TYPE_CHECKING, Any

from mstrio import config
from mstrio.api import documents, reports, subscriptions
from mstrio.connection import Connection
from mstrio.distribution_services.schedule import Schedule
from mstrio.distribution_services.subscription.content import Content
from mstrio.distribution_services.subscription.delivery import (
    CacheType,
    ClientType,
    Delivery,
    LegacyCacheType,
    LibraryCacheTypes,
    Orientation,
    SendContentAs,
    ShortcutCacheFormat,
    ZipSettings,
)
from mstrio.distribution_services.subscription.subscription_status import (
    SubscriptionStatus,
)
from mstrio.helpers import NotSupportedError
from mstrio.modeling import Prompt
from mstrio.users_and_groups import User
from mstrio.utils import helper, time_helper
from mstrio.utils.entity import ChangeJournalMixin, EntityBase
from mstrio.utils.enum_helper import AutoUpperName
from mstrio.utils.helper import (
    get_args_from_func,
    get_default_args_from_func,
    get_response_json,
)
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import subscriptions as subscriptions_processors
from mstrio.utils.version_helper import is_server_min_version, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.project import Project


logger = logging.getLogger(__name__)


class RecipientsTypes(AutoUpperName):
    CONTACT_GROUP = auto()
    USER_GROUP = auto()
    CONTACT = auto()
    USER = auto()
    PERSONAL_ADDRESS = auto()
    UNSUPPORTED = auto()


class Subscription(EntityBase, ChangeJournalMixin):
    """Class representation of Strategy One Subscription object.

    Attributes:
        subscription_id: The ID of the Subscription
        connection: The Strategy One connection object
        project_id: The ID of the project the Subscription belongs to
    """

    _API_GETTERS = {
        (
            "id",
            "name",
            "multiple_contents",
            "editable",
            "date_created",
            "date_modified",
            "owner",
            "schedules",
            "contents",
            "recipients",
            "delivery",
        ): subscriptions.get_subscription,
        "status": subscriptions_processors.get_subscription_status,
        "last_run": subscriptions_processors.get_subscription_last_run,
    }

    @staticmethod
    def _parse_status(source: dict, connection: 'Connection'):
        """Parse Subscription Status from the API response."""

        return SubscriptionStatus.from_dict(source, connection) if source else None

    _FROM_DICT_MAP = {
        "owner": User.from_dict,
        "contents": (
            lambda source, connection: [
                Content.from_dict(content, connection) for content in source
            ]
        ),
        "delivery": Delivery.from_dict,
        "schedules": (
            lambda source, connection: [
                Schedule.from_dict(content, connection) for content in source
            ]
        ),
        "date_created": time_helper.DatetimeFormats.YMDHMS,
        "date_modified": time_helper.DatetimeFormats.YMDHMS,
        "last_run": time_helper.DatetimeFormats.YMDHMS,
        "status": _parse_status,
    }
    _API_PATCH = [subscriptions.update_subscription]
    _RECIPIENTS_TYPES = RecipientsTypes
    _RECIPIENTS_INCLUDE = ['TO', 'CC', 'BCC', None]
    _API_GET_PROMPTS = staticmethod(subscriptions.get_subscription_prompts)

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        subscription_id: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Initialize Subscription object, populates it with I-Server data.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): ID of the subscription to be initialized, only
                id or subscription_id have to be provided at once, if both
                are provided `id` will take precedence
            subscription_id (str, optional): ID of the subscription to be
                initialized
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )

        subscription_id = id or subscription_id
        if not subscription_id:
            helper.exception_handler(
                msg='Must specify valid id or subscription_id',
                exception_type=ValueError,
            )

        super().__init__(connection, subscription_id, project_id=proj_id)

    def _init_variables(self, project_id, **kwargs):
        super()._init_variables(**kwargs)
        self.subscription_id = kwargs.get('id')
        self.multiple_contents = kwargs.get('multiple_contents')
        self.editable = kwargs.get('editable')
        self.allow_delivery_changes = kwargs.get('allow_delivery_changes')
        self.allow_personalization_changes = kwargs.get('allow_personalization_changes')
        self.allow_unsubscribe = kwargs.get('allow_unsubscribe')
        self.date_created = time_helper.map_str_to_datetime(
            "date_created", kwargs.get("date_created"), self._FROM_DICT_MAP
        )
        self.date_modified = time_helper.map_str_to_datetime(
            "date_modified", kwargs.get("date_modified"), self._FROM_DICT_MAP
        )
        self._last_run = time_helper.map_str_to_datetime(
            'last_run', kwargs.get('last_run'), self._FROM_DICT_MAP
        )
        self.owner = (
            User.from_dict(kwargs.get('owner'), self.connection)
            if kwargs.get('owner')
            else None
        )
        self.schedules = (
            [
                Schedule.from_dict(schedule, self._connection)
                for schedule in kwargs.get('schedules')
            ]
            if kwargs.get('schedules')
            else None
        )
        self.contents = (
            [
                Content.from_dict(content, self._connection)
                for content in kwargs.get('contents')
            ]
            if kwargs.get('contents')
            else None
        )
        self.recipients = kwargs.get('recipients')
        self.delivery = (
            Delivery.from_dict(kwargs.get('delivery'))
            if kwargs.get('delivery')
            else None
        )
        self.project_id = project_id
        self._status = kwargs.get('status')
        self._prompts = None

    @method_version_handler('11.3.0000')
    def alter(
        self,  # NOSONAR
        name: str | None = None,
        multiple_contents: bool | None = None,
        allow_delivery_changes: bool | None = None,
        allow_personalization_changes: bool | None = None,
        allow_unsubscribe: bool | None = None,
        send_now: bool = False,
        owner_id: str | None = None,
        schedules: str | list[str] | Schedule | list[Schedule] | None = None,
        contents: Content | list[Content] | None = None,
        recipients: list[str] | list[dict] | None = None,
        delivery: Delivery | dict | None = None,
        delivery_mode: str | None = None,
        custom_msg: str | None = None,
        delivery_expiration_date: str | None = None,
        delivery_expiration_timezone: str | None = None,
        contact_security: bool | None = None,
        filename: str | None = None,
        compress: bool | None = None,
        space_delimiter: str | None = None,
        email_subject: str | None = None,
        email_message: str | None = None,
        email_send_content_as: str | None = None,
        overwrite_older_version: bool | None = None,
        zip_filename: str | None = None,
        zip_password_protect: bool | None = None,
        zip_password: str | None = None,
        file_burst_sub_folder: str | None = None,
        printer_copies: int | None = None,
        printer_range_start: int | None = None,
        printer_range_end: int | None = None,
        printer_collated: bool | None = None,
        printer_orientation: str | None = None,
        printer_use_print_range: bool | None = None,
        cache_cache_type: str | None = None,
        cache_shortcut_cache_format: str | None = None,
        mobile_client_type: str | None = None,
        device_id: str | None = None,
        do_not_create_update_caches: bool | None = None,
        re_run_hl: bool | None = None,
        cache_library_cache_types: list[LibraryCacheTypes | str] = None,
        cache_reuse_dataset_cache: bool = False,
        cache_is_all_library_users: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: str | None = None,
    ):
        """
        Alter subscription.

        Args:
            name (str): name of the subscription,
            multiple_contents (bool, optional): whether multiple contents are
                allowed
            allow_delivery_changes (bool): whether the recipients can change
                the delivery of the subscription,
            allow_personalization_changes (bool): whether the recipients can
                personalize the subscription,
            allow_unsubscribe (bool): whether the recipients can unsubscribe
                from the subscription,
            send_now (bool): indicates whether to execute the subscription
                immediately,
            owner_id (str): ID of the subscription owner, by default logged in
                user ID,
            schedules (str | list[str] | Schedule | list[Schedule]):
                Schedules IDs or Schedule objects,
            contents (Content | list[Content]): The content of the subscription.
            recipients (list[str] | list[dict]): list of recipients IDs
                or dicts,
            delivery (Delivery, dict, optional): delivery settings
            delivery_mode (str, enum): the subscription delivery mode [EMAIL,
                FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP, SNAPSHOT,
                PERSONAL_VIEW, SHARED_LINK, UNSUPPORTED],
            custom_msg (str, optional): customized message displayed when
                Subscription has been successfully altered
            delivery_expiration_date (str): expiration date of the subscription,
                format should be yyyy-MM-dd,
            delivery_expiration_timezone (str, optional): expiration timezone
                of the subscription
            contact_security (bool): whether to use contact security for each
                contact group member,
            filename (str): the filename that will be delivered when
                the subscription is executed,
            compress (bool): whether to compress the file
            space_delimiter (str): space delimiter,
            email_subject (str): email subject associated with the subscription,
            email_message (str): email body of subscription,
            email_send_content_as (str,enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename (str): filename of the compressed content,
            zip_password_protect (bool): whether to password protect zip file,
            zip_password (str): optional password for the compressed file
            file_burst_sub_folder (str): burst sub folder,
            printer_copies (int): the number of copies that should be printed,
            printer_range_start (int): the number indicating the first report
                page that should be printed,
            printer_range_end (int): the number indicating the last report
                page that should be printed,
            printer_collated (bool): whether the printing should be collated,
            printer_orientation (str,enum): [ PORTRAIT, LANDSCAPE ]
            printer_use_print_range (bool): whether print range should be used,
            cache_cache_type (str,enum): [RESERVED, SHORTCUT,
                SHORTCUTWITHBOOKMARK]
            cache_shortcut_cache_format (str,enum): [RESERVED, JSON, BINARY,
                BOTH]
            mobile_client_type (str,enum): [PHONE, TABLET]
            device_id (str): the mobile target project,
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            re_run_hl (bool): whether subscription will re-run against warehouse
            cache_library_cache_types (list[LibraryCacheTypes | str], optional):
                Set of library cache types, available types can be
                web, android, ios
            cache_reuse_dataset_cache (bool): Whether to reuse dataset cache
            cache_is_all_library_users (bool): Whether for all library users
            delivery_notification_enabled (bool): Whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                Notification details
        """

        # TODO Potentially remove if new subscription types are supported
        cache_library_cache_types = cache_library_cache_types or [LibraryCacheTypes.WEB]
        if self.delivery.mode in [
            'SNAPSHOT',
            'PERSONAL_VIEW',
            'SHARED_LINK',
            'UNSUPPORTED',
        ]:
            helper.exception_handler(
                msg=f'{self.delivery.mode} subscription altering is not supported.',
                exception_type=NotSupportedError,
            )
        # Schedules logic
        schedules = self.__validate_schedules(schedules=schedules)
        if not schedules:
            schedules = [{'id': sch.id} for sch in self.schedules]

        # Content logic
        if contents:
            contents = self.__validate_contents(contents)
        else:
            # Even if contents are not changed, they must be executed with
            # any stored prompt answers
            contents = self.__get_reprompted_contents()

        # Delivery logic
        delivery_expiration_timezone = self.__validate_expiration_time_zone(
            self.connection,
            delivery_expiration_timezone,
        )
        if delivery:
            temp_delivery = (
                Delivery.from_dict(delivery) if isinstance(delivery, dict) else delivery
            )
        else:
            personal_notification_address_id = delivery_personal_notification_address_id

            temp_delivery = self.__change_delivery_properties(
                delivery_mode,
                delivery_expiration_date,
                contact_security,
                email_subject,
                email_message,
                filename,
                compress,
                None,
                zip_filename,
                zip_password,
                zip_password_protect,
                space_delimiter,
                email_send_content_as,
                overwrite_older_version,
                file_burst_sub_folder,
                printer_copies,
                printer_range_start,
                printer_range_end,
                printer_collated,
                printer_orientation,
                printer_use_print_range,
                expiration_time_zone=delivery_expiration_timezone,
                mobile_client_type=mobile_client_type,
                device_id=device_id,
                do_not_create_update_caches=do_not_create_update_caches,
                re_run_hl=re_run_hl,
                cache_type=cache_cache_type,
                shortcut_cache_format=cache_shortcut_cache_format,
                library_cache_types=cache_library_cache_types,
                reuse_dataset_cache=cache_reuse_dataset_cache,
                is_all_library_users=cache_is_all_library_users,
                notification_enabled=delivery_notification_enabled,
                personal_notification_address_id=personal_notification_address_id,
            )
        delivery = temp_delivery.to_dict(camel_case=True)

        # Recipients logic
        recipients = self.__is_val_changed(recipients=recipients)
        recipients = Subscription._validate_recipients(
            self.connection,
            contents,
            recipients,
            self.project_id,
            delivery['mode'],
            self.recipients,
        )

        body = {
            "name": self.__is_val_changed(name=name),
            "allowDeliveryChanges": self.__is_val_changed(
                allow_delivery_changes=allow_delivery_changes
            ),
            "multipleContents": self.__is_val_changed(
                multiple_contents=multiple_contents
            ),
            "allowPersonalizationChanges": self.__is_val_changed(
                allow_personalization_changes=allow_personalization_changes
            ),
            "allowUnsubscribe": self.__is_val_changed(
                allow_unsubscribe=allow_unsubscribe
            ),
            "sendNow": send_now,
            'owner': {
                'id': self.__is_val_changed(nested=self.owner.id, owner_id=owner_id)
            },
            "schedules": schedules,
            "contents": contents,
            "recipients": recipients,
            "delivery": delivery,
        }

        body = helper.delete_none_values(body, recursion=True)

        response = subscriptions.update_subscription(
            self.connection, self.id, self.project_id, body
        )

        if response.ok:
            response = response.json()
            response = helper.camel_to_snake(response)
            self._set_object_attributes(**response)
            if config.verbose:
                msg = f"Updated subscription '{self.name}' with ID: {self.id}."
                msg = custom_msg or msg
                logger.info(msg)

    def __is_val_changed(self, nested=None, **kwargs):
        for key, value in kwargs.items():
            if nested:
                return value if value != nested and value is not None else nested
            current_val = self.__dict__.get(key)
            # if not current_val: we need to get
            return value if value != current_val and value is not None else current_val

    @staticmethod
    def __validate_schedules(
        schedules: str | list[str] | Schedule | list[Schedule] = None,
    ):
        schedules = schedules if isinstance(schedules, list) else [schedules]
        schedules = [
            {'id': schedule.id if isinstance(schedule, Schedule) else schedule}
            for schedule in schedules
            if schedule is not None
        ]
        return schedules

    @staticmethod
    def __validate_contents(
        contents: list[Content | dict] | Content | dict,
    ) -> list[dict]:
        contents = contents if isinstance(contents, list) else [contents]
        content_type_msg = "Contents must be dictionaries or Content objects."
        return [
            (
                content.to_dict(camel_case=True)
                if isinstance(content, Content)
                else (
                    content
                    if isinstance(content, dict)
                    else helper.exception_handler(content_type_msg, TypeError)
                )
            )
            for content in contents
        ]

    def execute(self) -> None:
        """Executes a subscription with given name or GUID for given project."""
        subscriptions.send_subscription(self.connection, self.id, self.project_id)
        if config.verbose:
            logger.info(f"Executed subscription '{self.name}' with ID: {self.id}.")

    @method_version_handler('11.2.0203')
    def delete(self, force: bool = False) -> bool:
        """Delete a subscription. Returns True if deletion was successful.

        Args:
            force (bool, optional): If True, no additional prompt will be shown
                before deleting the subscription. Defaults to False.
        """
        message = (
            f"Are you sure you want to delete subscription "
            f"'{self.name}' with ID: {self.id}? [Y/N]: "
        )
        if not force and input(message) != 'Y':
            return False

        response = subscriptions.remove_subscription(
            self.connection, self.id, self.project_id
        )
        if config.verbose:
            logger.info(f"Deleted subscription '{self.name}' with ID: {self.id}.")
        return response.ok

    @method_version_handler('11.3.0000')
    def available_bursting_attributes(self) -> dict:
        """Get a list of available attributes for bursting feature."""
        contents_bursting = {}
        for content in self.contents:
            response = subscriptions.bursting_attributes(
                self.connection,
                self.project_id,
                content.id,
                content.type.upper(),
            )
            if response.ok:
                contents_bursting[content.id] = response.json()['burstingAttributes']

        return contents_bursting

    @method_version_handler('11.3.0000')
    def available_recipients(self) -> list[dict]:
        """List available recipients for subscription content."""
        body = {"contents": [content.to_dict() for content in self.contents]}
        delivery_type = self.delivery.mode
        response = subscriptions.available_recipients(
            self.connection, self.project_id, body, delivery_type
        )

        if response.ok and config.verbose:
            return response.json()['recipients']

    @method_version_handler('11.3.0000')
    def add_recipient(
        self,
        recipients: list[dict] | dict | list[str] | str = None,
        recipient_id: str | None = None,
        recipient_type: str | None = None,
        recipient_include_type: str = 'TO',
    ):
        """Adds recipient to subscription. You can either specify id, type and
        include_type of single recipient, or just pass recipients list as a
        list of dictionaries.

        Note:
            When providing recipient ID remember to also provide its type.

        Args:
            recipients: list of ids or dicts containing recipients, dict format:
                {"id": recipient_id,
                 "type": "CONTACT_GROUP" / "USER_GROUP" / "CONTACT" /
                         "USER" / "PERSONAL_ADDRESS" / "UNSUPPORTED"
                 "includeType": "TO" / "CC" / "BCC"}
            recipient_id: id of the recipient
            recipient_type: type of the recipient
            recipient_include_type: include type of the recipient one of the
                following: "TO" / "CC" / "BCC", by default "TO"
        """
        if recipients:
            recipients = recipients if isinstance(recipients, list) else [recipients]
        else:
            recipients = []
        if recipient_id and recipient_type:
            recipients.append(
                {
                    "id": recipient_id,
                    "type": recipient_type,
                    "includeType": recipient_include_type,
                }
            )
        elif (recipients == [] and recipient_id is None) or (
            len(recipients) >= 1 and recipient_id
        ):
            msg = (
                "Specify either a recipient ID, type and include type or pass "
                "recipients dictionaries"
            )
            helper.exception_handler(msg, ValueError)
        elif recipients == [] and recipient_id and recipient_type is None:
            msg = "When providing recipient ID remember to also provide its type."
            helper.exception_handler(msg, ValueError)

        all_recipients = self.recipients.copy()
        ready_recipients = self.__prepare_recipients(recipients)

        ready_recipients = self._validate_recipients(
            connection=self.connection,
            contents=self.contents,
            recipients=ready_recipients,
            project_id=self.project_id,
            delivery_mode=self.delivery.mode,
            current_recipients=self.recipients,
        )

        if ready_recipients:
            all_recipients.extend(ready_recipients)
            self.alter(recipients=all_recipients)
        elif config.verbose:
            logger.info('No recipients were added to the subscription.')

    @method_version_handler('11.3.0000')
    def remove_recipient(self, recipients: list[str] | list[dict]):
        """Removes recipient from given subscription in given project.

        Args:
            recipients: list of ids or dicts containing recipients, dict format:
                {"id": recipient_id,
                 "type": "CONTACT_GROUP" / "USER_GROUP" / "CONTACT" /
                         "USER" / "PERSONAL_ADDRESS" / "UNSUPPORTED"
                 "includeType": "TO" / "CC" / "BCC"}
        """
        all_recipients = self.recipients
        recipients = recipients if isinstance(recipients, list) else [recipients]
        existing_recipients = [rec['id'] for rec in self.recipients]

        if len(self.recipients) == 1:
            helper.exception_handler(
                "Subscription must have at last one recipient. Add new recipient "
                "before removing.",
                exception_type=ValueError,
            )
        for recipient in recipients:
            rec_id = recipient['id'] if isinstance(recipient, dict) else recipient
            if rec_id not in existing_recipients:
                helper.exception_handler(
                    f"{rec_id} is not a recipient of subscription", UserWarning
                )
            else:
                all_recipients = [rec for rec in all_recipients if rec['id'] != rec_id]
        if len(all_recipients) == 0:
            helper.exception_handler(
                "You cannot remove all existing recipients. Add new recipient before "
                "removing.",
                exception_type=ValueError,
            )
        elif len(self.recipients) - len(all_recipients) > 0:
            self.alter(recipients=all_recipients)
        elif len(self.recipients) == len(all_recipients) and config.verbose:
            logger.info('No recipients were removed from the subscription.')

    def __prepare_recipients(self, recipients):
        existing_recipients = [rec['id'] for rec in self.recipients]
        ready_recipients = []

        def __already_recipient(recipient):
            if recipient in existing_recipients:
                helper.exception_handler(
                    f"{recipient} is already a recipient of subscription", UserWarning
                )
            else:
                ready_recipients.append(recipient)

        for recipient in recipients:
            not_dict_msg = """Wrong recipient format, expected format is
                              {"id": recipient_id,
                               "type": "CONTACT_GROUP" / "USER_GROUP" / "CONTACT" /
                                       "USER" / "PERSONAL_ADDRESS" / "UNSUPPORTED"
                               "includeType": "TO" / "CC" / "BCC" (optional)
                              }"""
            if isinstance(recipient, dict):
                if list(recipient.keys()) in [
                    ['id', 'type', 'includeType'],
                    ['id', 'type'],
                ]:
                    __already_recipient(recipient['id'])
                else:
                    helper.exception_handler(not_dict_msg, TypeError)
            if isinstance(recipient, str):
                __already_recipient(recipient)
        return ready_recipients

    def __change_delivery_properties(  # NOSONAR
        self,  # NOSONAR
        mode: str | None = None,
        expiration: str | None = None,
        contact_security: bool | None = None,
        subject: str | None = None,
        message: str | None = None,
        filename: str | None = None,
        compress: bool | None = None,
        zip_settings: ZipSettings | None = None,
        zip_filename: str | None = None,
        zip_password: str | None = None,
        zip_password_protect: bool | None = None,
        space_delimiter: str | None = None,
        send_content_as: SendContentAs | None = None,
        overwrite_older_version: bool | None = None,
        burst_sub_folder: str | None = None,
        copies: int | None = None,
        range_start: int | None = None,
        range_end: int | None = None,
        collated: bool | None = None,
        orientation: Orientation | None = None,
        use_print_range: bool | None = None,
        expiration_time_zone: str | None = None,
        cache_type: CacheType | None = None,
        shortcut_cache_format: ShortcutCacheFormat | None = None,
        mobile_client_type: ClientType | None = None,
        device_id: str | None = None,
        do_not_create_update_caches: bool | None = None,
        re_run_hl: bool | None = None,
        library_cache_types: list[LibraryCacheTypes | str] = None,
        reuse_dataset_cache: bool = False,
        is_all_library_users: bool = False,
        notification_enabled: bool = False,
        personal_notification_address_id: str | None = None,
    ):
        library_cache_types = library_cache_types or [LibraryCacheTypes.WEB]
        func = self.__change_delivery_properties
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
        local = locals()
        # create dict of properties to be changed
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        # 'zip_settings' is 'zip' in object
        if 'zip_settings' in properties:
            properties['zip'] = properties.pop('zip_settings')

        obj_dict = self.delivery.VALIDATION_DICT
        obj_mode_dict = self.delivery.__dict__[
            self.delivery.mode.lower()
        ].VALIDATION_DICT
        obj_mode_zip_dict = {
            "zip_filename": str,
            "zip_password": str,
            "zip_password_protect": bool,
        }

        if properties:  # at this point only not None values in properties
            for key, value in properties.items():
                if (
                    key in obj_dict
                ):  # Highest level parameters. Mainly mode type and object
                    # Change mode or set attr if it's not mode param
                    if not self.delivery.change_mode(key, value):
                        self.delivery.__setattr__(key, value)
                elif (
                    key in obj_mode_dict
                ):  # parameters of a particular mode e.g. of email
                    helper.rsetattr(
                        self.delivery, f'{self.delivery.mode.lower()}.{key}', value
                    )
                elif key in obj_mode_zip_dict:  # zip settings
                    key = key[4:]
                    if not helper.rgetattr(
                        self.delivery, f'{self.delivery.mode.lower()}.zip', None
                    ):
                        helper.rsetattr(
                            self.delivery,
                            f'{self.delivery.mode.lower()}.zip',
                            ZipSettings(),
                        )
                    helper.rsetattr(
                        self.delivery, f'{self.delivery.mode.lower()}.zip.{key}', value
                    )
        return self.delivery

    @classmethod
    def from_dict(
        cls,
        source: dict[str, Any],
        connection: "Connection" = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> "Subscription":
        """Initialize Subscription object from dictionary.

        Args:
            source: (dict) A dictionary containing subscription data.
            connection: (Connection) A Strategy connection object.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            A Subscription object.
        """

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id or source.get('project_id'),
            project_name,
        )

        _source = {
            **source,
            "project_id": proj_id,
        }
        obj: Subscription = super().from_dict(_source, connection)

        return obj

    @staticmethod
    def _check_is_content_prompted(
        connection: 'Connection', content: dict, project_id: str | None = None
    ) -> bool:
        def check_prompts(
            inst_id: str,
            get_prompts_func: Callable,
            get_status_func: Callable,
            c_id: str,
            c_type: str,
        ) -> bool:
            prompts = get_response_json(get_prompts_func())
            if any(prompt.get('required') for prompt in prompts):
                if not inst_id:
                    err_msg = (
                        f"The content of type '{c_type.capitalize()}' with ID '{c_id}' "
                        f"has unanswered prompts. "
                        f"Please use the `{c_type.capitalize()}.answer_prompts()` "
                        f"method to answer them. "
                        f"After that, pass the `{c_type.capitalize()}.instance_id` "
                        f"to the subscription content."
                    )
                    raise ValueError(err_msg)

                status = get_response_json(get_status_func()).get('status')
                if status == 2:
                    err_msg = (
                        f"{c_type.capitalize()}.instance_id: {inst_id} "
                        f"has unanswered prompts. "
                        f"You can use the `{c_type.capitalize()}.answer_prompts()`"
                        f" method to answer them."
                    )
                    raise ValueError(err_msg)

                return True
            return False

        content_type = content.get('type')
        content_id = content.get('id')
        instance_id = (
            content.get('personalization', {}).get('prompt', {}).get('instanceId')
        )

        common_args = {
            'connection': connection,
        }

        if content_type == 'report':
            common_args.update({'report_id': content_id})
            return check_prompts(
                inst_id=instance_id,
                get_prompts_func=partial(
                    reports.get_report_prompts,
                    **common_args,
                    closed=False,
                ),
                get_status_func=partial(
                    reports.get_report_status,
                    **common_args,
                    project_id=project_id,
                    instance_id=instance_id,
                ),
                c_id=content_id,
                c_type=content_type,
            )
        elif content_type in ['document', 'dossier']:
            common_args.update(
                {
                    'document_id': content_id,
                    'project_id': project_id,
                }
            )
            return check_prompts(
                inst_id=instance_id,
                get_prompts_func=partial(
                    documents.get_prompts,
                    **common_args,
                    closed=False,
                ),
                get_status_func=partial(
                    documents.get_document_status,
                    **common_args,
                    instance_id=instance_id,
                ),
                c_id=content_id,
                c_type=content_type,
            )
        return False

    @classmethod
    @method_version_handler('11.3.0000')
    def __create(  # NOSONAR
        cls,  # NOSONAR
        connection: Connection,
        name: str,
        contents: Content | dict,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        multiple_contents: bool | None = None,
        allow_delivery_changes: bool | None = None,
        allow_personalization_changes: bool | None = None,
        allow_unsubscribe: bool | None = None,
        send_now: bool | None = None,
        owner_id: str | None = None,
        schedules: str | list[str] | Schedule | list[Schedule] | None = None,
        recipients: list[dict] | list[str] | None = None,
        delivery: Delivery | dict | None = None,
        delivery_mode: str = Delivery.DeliveryMode.EMAIL,
        delivery_expiration_date: str | None = None,
        delivery_expiration_timezone: str | None = None,
        contact_security: bool = True,
        filename: str | None = None,
        compress: bool = False,
        space_delimiter: str | None = None,
        email_subject: str | None = None,
        email_message: str | None = None,
        email_send_content_as: str = SendContentAs.DATA,
        overwrite_older_version: bool = False,
        zip_filename: str | None = None,
        zip_password_protect: bool | None = None,
        zip_password: str | None = None,
        file_burst_sub_folder: str | None = None,
        printer_copies: int = 1,
        printer_range_start: int = 0,
        printer_range_end: int = 0,
        printer_collated: bool = True,
        printer_orientation: str = Orientation.PORTRAIT,
        printer_use_print_range: bool = False,
        cache_cache_type: CacheType | str = CacheType.RESERVED,
        cache_shortcut_cache_format: (
            ShortcutCacheFormat | str
        ) = ShortcutCacheFormat.RESERVED,
        mobile_client_type: str = ClientType.PHONE,
        device_id: str | None = None,
        do_not_create_update_caches: bool = True,
        re_run_hl: bool = True,
        cache_library_cache_types: list[LibraryCacheTypes | str] = None,
        cache_reuse_dataset_cache: bool = False,
        cache_is_all_library_users: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: str | None = None,
    ):
        """Creates a subscription Create_Subscription_Outline.

        Args:
            connection (Connection): a Strategy One connection object
            name (str): name of the subscription,
            contents (Content): The content settings.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            multiple_contents (bool, optional): whether multiple contents are
                allowed
            allow_delivery_changes (bool): whether the recipients can change
                the delivery of the subscription,
            allow_personalization_changes (bool): whether the recipients can
                personalize the subscription,
            allow_unsubscribe (bool): whether the recipients can unsubscribe
                from the subscription,
            send_now (bool): indicates whether to execute the subscription
                immediately,
            owner_id (str): ID of the subscription owner, by default logged in
                user ID,
            schedules (str | list[str] | Schedule | List[Schedule]):
                Schedules IDs or Schedule objects,
            recipients (list[dict], list[str]): list of recipients IDs or dicts,
            delivery (Delivery | dict): delivery object or dict
            delivery_mode (str, enum): the subscription delivery mode [EMAIL,
                FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP, SNAPSHOT,
                PERSONAL_VIEW, SHARED_LINK, UNSUPPORTED],
            delivery_expiration_date (str, optional): expiration date of the
                subscription, format should be yyyy-MM-dd,
            delivery_expiration_timezone (str, optional): expiration timezone
                of the subscription, example value 'Europe/London'
            contact_security (bool): whether to use contact security for each
                contact group member,
            filename (str): the filename that will be delivered when
                the subscription is executed,
            compress (bool): whether to compress the file,
            space_delimiter (str): space delimiter,
            email_subject (str): email subject associated with the subscription,
            email_message (str): email body of subscription,
            email_send_content_as (str,enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename (str): filename of the compressed content,
            zip_password_protect (bool): whether to password protect zip file,
            zip_password (str): optional password for the compressed file,
            file_burst_sub_folder (str): burst sub folder,
            printer_copies (int): the number of copies that should be printed,
            printer_range_start (int): the number indicating the first report
                page that should be printed,
            printer_range_end (int): the number indicating the last report
                page that should be printed,
            printer_collated (bool): whether the printing should be collated,
            printer_orientation (str,enum): [ PORTRAIT, LANDSCAPE ]
            printer_use_print_range (bool): whether print range should be used,
            cache_cache_type (str,enum): [RESERVED, SHORTCUT,
                SHORTCUTWITHBOOKMARK]
            cache_shortcut_cache_format (str,enum):
                [RESERVED, JSON, BINARY, BOTH]
            mobile_client_type (str,enum): [PHONE, TABLET]
            device_id (str): the mobile target project,
            do_not_create_update_caches (bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            re_run_hl (bool): whether subscription will re-run against warehouse
            cache_library_cache_types (list[LibraryCacheTypes | str], optional):
                Set of library cache types, available types can be
                web, android, ios
            cache_reuse_dataset_cache (bool): Whether to reuse dataset cache
            cache_is_all_library_users (bool): Whether for all library users
            delivery_notification_enabled (bool): Whether notification is
                enabled, notification applies to cache
            delivery_personal_notification_address_id (str, optional):
                Notification details
        """
        cache_library_cache_types = cache_library_cache_types or [LibraryCacheTypes.WEB]

        cache_cache_type = (
            LegacyCacheType[cache_cache_type.name]
            if not is_server_min_version(connection, '11.3.0100')
            else CacheType[cache_cache_type.name]
        )

        name = (
            name
            if len(name) <= 255
            else helper.exception_handler(
                "Name too long. Max name length is 255 characters."
            )
        )
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )

        if not schedules:
            msg = "Please specify 'schedules' parameter."
            helper.exception_handler(msg)

        schedules = cls.__validate_schedules(schedules=schedules)

        # Content logic
        contents = cls.__validate_contents(contents)

        for content in contents:
            cls._check_is_content_prompted(connection, content, proj_id)

        # Delivery logic
        delivery_expiration_timezone = cls.__validate_expiration_time_zone(
            connection,
            delivery_expiration_timezone,
        )
        if delivery:
            temp_delivery = (
                Delivery.from_dict(delivery) if isinstance(delivery, dict) else delivery
            )
        else:
            personal_notification_address_id = delivery_personal_notification_address_id

            temp_delivery = Delivery(
                delivery_mode,
                delivery_expiration_date,
                contact_security,
                email_subject,
                email_message,
                filename,
                compress,
                None,
                zip_password,
                zip_password_protect,
                space_delimiter,
                email_send_content_as,
                overwrite_older_version,
                file_burst_sub_folder,
                printer_copies,
                printer_range_start,
                printer_range_end,
                printer_collated,
                printer_orientation,
                printer_use_print_range,
                mobile_client_type,
                device_id,
                do_not_create_update_caches,
                re_run_hl,
                cache_type=cache_cache_type,
                shortcut_cache_format=cache_shortcut_cache_format,
                library_cache_types=cache_library_cache_types,
                reuse_dataset_cache=cache_reuse_dataset_cache,
                is_all_library_users=cache_is_all_library_users,
                notification_enabled=delivery_notification_enabled,
                personal_notification_address_id=personal_notification_address_id,
                expiration_time_zone=delivery_expiration_timezone,
            )
        delivery = temp_delivery.to_dict(camel_case=True)

        # Recipients logic
        recipients = cls._validate_recipients(
            connection, contents, recipients, proj_id, delivery['mode']
        )

        # Create body
        body = {
            "multipleContents": len(contents) > 1,
            "name": name,
            "allowDeliveryChanges": allow_delivery_changes,
            "allowPersonalizationChanges": allow_personalization_changes,
            "allowUnsubscribe": allow_unsubscribe,
            "sendNow": send_now,
            "owner": {"id": owner_id},
            "schedules": schedules,
            "contents": contents,
            "recipients": recipients,
            "delivery": delivery,
        }

        body = helper.delete_none_values(body, recursion=True)
        response = subscriptions.create_subscription(connection, proj_id, body)
        unpacked_response = response.json()
        if config.verbose:
            logger.info(
                f"Created subscription '{name}' with ID: '{unpacked_response['id']}'."
            )
        return cls.from_dict(unpacked_response, connection, proj_id)

    @staticmethod
    def _validate_recipients(
        connection: "Connection",
        contents: list[Content | dict],
        recipients: list[str] | list[dict] | str,
        project_id: str,
        delivery_mode: str,
        current_recipients: list[dict] | None = None,
    ):
        def __not_available(recipient):
            if recipient not in available_recipients_ids:
                msg = (
                    f"'{recipient}' is not a valid recipient ID for selected content "
                    "and delivery mode. Available recipients: \n"
                    f"{pformat(available_recipients, indent=2)}"
                )
                helper.exception_handler(msg, ValueError)

            rec = helper.filter_list_of_dicts(available_recipients, id=recipient)
            formatted_recipients.append(rec[0])

        recipients = recipients or []
        recipients = recipients if isinstance(recipients, list) else [recipients]
        body = {
            "contents": [
                cont.to_dict() if isinstance(cont, Content) else cont
                for cont in contents
            ]
        }
        available_recipients = subscriptions.available_recipients(
            connection, project_id, body, delivery_mode
        ).json()['recipients'] + (current_recipients or [])
        available_recipients_ids = [rec['id'] for rec in available_recipients]
        # Format recipients list if needed
        formatted_recipients = []
        if recipients:
            for recipient in recipients:
                if isinstance(recipient, dict):
                    __not_available(recipient['id'])
                elif isinstance(recipient, str):
                    __not_available(recipient)
                else:
                    recipient_type = type(recipient)

                    helper.exception_handler(
                        "Recipients must be a dictionaries or a strings, "
                        f"not a {recipient_type}",
                        exception_type=TypeError,
                    )
        return formatted_recipients

    @staticmethod
    def __validate_expiration_time_zone(connection, expiration_time_zone):
        if connection._iserver_version < '11.3.1000' and expiration_time_zone:
            if config.verbose:
                logger.info(
                    'delivery_expiration_timezone argument is available from '
                    'iServer Version 11.3.1000'
                )
        else:
            return expiration_time_zone

    def _is_valid_delivery_mode(self) -> bool:
        valid_modes = [
            'EMAIL',
            'HISTORY_LIST',
            'CACHE',
            'FTP',
            'FILE',
            'MOBILE',
        ]
        # Get subscription delivery mode from API to avoid max depth recursion
        sub_mode = (
            subscriptions.get_subscription(
                connection=self.connection,
                subscription_id=self.id,
                project_id=self.project_id,
            )
            .json()
            .get('delivery', {})
            .get('mode')
        )
        return sub_mode in valid_modes

    def __get_reprompted_contents(self) -> list[dict]:
        """Re-prompt contents to obtain their representation for alter().
        Returns:
            list[dict]: list of content dicts to be included in REST payload
        """

        from mstrio.modeling.prompt import Prompt
        from mstrio.project_objects.document import Document
        from mstrio.project_objects.report import Report

        contents: list[dict] = [cont.to_dict() for cont in self.contents]
        if not any(ct.personalization.prompt for ct in self.contents):
            return contents
        prompts_data = subscriptions.get_subscription_prompts(
            self.connection,
            self.id,
            self.project_id,
        ).json()['prompts']
        for content in contents:
            content_type = content.get('type')
            dict_update = {
                'enabled': True,
            }
            if content_type == 'report':
                rep = Report(self.connection, content['id'])
                rep.answer_prompts(Prompt.bulk_from_dict(prompts_data), True)
                dict_update['instanceId'] = rep.instance_id
            elif content_type in ['document', 'dossier']:
                doc = Document(self.connection, content['id'])
                doc.answer_prompts(prompts_data, True)
                dict_update['instanceId'] = doc.instance_id
            content['personalization'].update({'prompt': dict_update})
        return contents

    @property
    @method_version_handler(version='11.4.0600')
    def status(self) -> SubscriptionStatus | None:
        if not self._is_valid_delivery_mode():
            msg = (
                f"Subscription with delivery mode: "
                f"{self.delivery.mode} is not supported."
            )
            raise NotSupportedError(msg)
        self.fetch('status')
        return self._status

    @property
    @method_version_handler(version='11.4.0600')
    def last_run(self) -> datetime | None:
        if not self._is_valid_delivery_mode():
            msg = (
                f"Subscription with delivery mode: "
                f"{self.delivery.mode} is not supported."
            )
            raise NotSupportedError(msg)
        return self._last_run

    def fetch(self, attr: str | None = None) -> None:
        if not self._is_valid_delivery_mode():
            self._API_GETTERS = {
                k: v
                for k, v in self._API_GETTERS.items()
                if k not in ['status', 'last_run']
            }
        super().fetch(attr)

    def answer_prompts(
        self,
        prompt_answers: list["Prompt"],
        force: bool = False,
    ) -> bool:
        """Answer prompts of the object.

        Args:
            prompt_answers (list[Prompt]): List of Prompt class objects
                answering the prompts of the object.
            force (bool): If True, then the object's existing prompt will be
                overwritten by ones from the prompt_answers list, and additional
                input from the user won't be asked. Otherwise, the user will be
                asked for input if the prompt is not answered, or if prompt was
                already answered.

        Returns:
            bool: True if prompts were answered successfully, False otherwise.
        """
        from mstrio.project_objects import Document, Report

        new_contents = []
        for content_obj in self.contents:
            selected_obj = None
            if content_obj.type == Content.Type.REPORT:
                selected_obj = Report(self.connection, content_obj.id)
            elif content_obj.type in [
                Content.Type.DOCUMENT,
                Content.Type.DASHBOARD,
            ]:
                selected_obj = Document(self.connection, content_obj.id)
            else:
                raise NotSupportedError(
                    f"Answering prompts is not supported for content type "
                    f"'{content_obj.type}'."
                )

            selected_obj.answer_prompts(prompt_answers, force=force)
            new_contents.append(
                Content(
                    id=selected_obj.id,
                    type=content_obj.type,
                    personalization=Content.Properties(
                        format_type=content_obj.personalization.format_type,
                        prompt=Content.Properties.Prompt(
                            enabled=True,
                            instance_id=selected_obj.instance_id,
                        ),
                    ),
                )
            )

        self.alter(contents=new_contents)
        return True

    @property
    @method_version_handler('11.5.0900')
    def prompts(self) -> dict:
        """Prompts of the report."""
        if self._prompts is None:
            prompts = (
                subscriptions.get_subscription_prompts(
                    connection=self.connection,
                    subscription_id=self.id,
                    project_id=self.project_id,
                )
                .json()
                .get('prompts', [])
            )
            self._prompts = [
                Prompt.from_dict(source=prompt, connection=self.connection)
                for prompt in prompts
            ]
        return self._prompts
