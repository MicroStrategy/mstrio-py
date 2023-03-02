from enum import auto
import logging
from pprint import pformat
from typing import Any, Optional

from mstrio import config
from mstrio.api import subscriptions
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
    ZipSettings
)
from mstrio.users_and_groups import User
from mstrio.utils import helper, time_helper
from mstrio.utils.entity import EntityBase
from mstrio.utils.exceptions import NotSupportedError
from mstrio.utils.enum_helper import AutoUpperName
from mstrio.utils.helper import (
    get_args_from_func, get_default_args_from_func, get_valid_project_id
)
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


class RecipientsTypes(AutoUpperName):
    CONTACT_GROUP = auto()
    USER_GROUP = auto()
    CONTACT = auto()
    USER = auto()
    PERSONAL_ADDRESS = auto()
    UNSUPPORTED = auto()


class Subscription(EntityBase):
    """Class representation of MicroStrategy Subscription object.

    Attributes:
        subscription_id: The ID of the Subscription
        connection: The MicroStrategy connection object
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
            "delivery"
        ): subscriptions.get_subscription
    }
    _FROM_DICT_MAP = {
        "owner": User.from_dict,
        "contents": (
            lambda source,
            connection: [Content.from_dict(content, connection) for content in source]
        ),
        "delivery": Delivery.from_dict,
        "schedules": (
            lambda source,
            connection: [Schedule.from_dict(content, connection) for content in source]
        ),
        "date_created": time_helper.DatetimeFormats.YMDHMS,
        "date_modified": time_helper.DatetimeFormats.YMDHMS,
    }
    _API_PATCH = [subscriptions.update_subscription]
    _RECIPIENTS_TYPES = RecipientsTypes
    _RECIPIENTS_INCLUDE = ['TO', 'CC', 'BCC', None]

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None
    ):
        """Initialize Subscription object, populates it with I-Server data.
        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): ID of the subscription to be initialized, only
                id or subscription_id have to be provided at once, if both
                are provided id will take precedence
            subscription_id (str, optional): ID of the subscription to be
                initialized
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True,
        )
        if id or subscription_id:
            subscription_id = id if id else subscription_id
        else:
            helper.exception_handler(
                msg='Must specify valid id or subscription_id', exception_type=ValueError
            )

        super().__init__(connection, subscription_id, project_id=project_id)

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
        self.owner = User.from_dict(kwargs.get('owner'),
                                    self.connection) if kwargs.get('owner') else None
        self.schedules = [
            Schedule.from_dict(schedule, self._connection) for schedule in kwargs.get('schedules')
        ] if kwargs.get('schedules') else None
        self.contents = [
            Content.from_dict(content, self._connection) for content in kwargs.get('contents')
        ] if kwargs.get('contents') else None
        self.recipients = kwargs.get('recipients', None)
        self.delivery = Delivery.from_dict(kwargs.get('delivery')
                                           ) if kwargs.get('delivery') else None
        self.project_id = project_id

    @method_version_handler('11.3.0000')
    def alter(
        self,  # NOSONAR
        name: Optional[str] = None,
        multiple_contents: Optional[bool] = None,
        allow_delivery_changes: Optional[bool] = None,
        allow_personalization_changes: Optional[bool] = None,
        allow_unsubscribe: Optional[bool] = None,
        send_now: bool = False,
        owner_id: Optional[str] = None,
        schedules: Optional[str | list[str] | Schedule | list[Schedule]] = None,
        contents: Optional[Content] = None,
        recipients: Optional[list[str] | list[dict]] = None,
        delivery: Optional[Delivery | dict] = None,
        delivery_mode: Optional[str] = None,
        custom_msg: Optional[str] = None,
        delivery_expiration_date: Optional[str] = None,
        contact_security: Optional[bool] = None,
        filename: Optional[str] = None,
        compress: Optional[bool] = None,
        space_delimiter: Optional[str] = None,
        email_subject: Optional[str] = None,
        email_message: Optional[str] = None,
        email_send_content_as: Optional[str] = None,
        overwrite_older_version: Optional[bool] = None,
        zip_filename: Optional[str] = None,
        zip_password_protect: Optional[bool] = None,
        zip_password: Optional[str] = None,
        file_burst_sub_folder: Optional[str] = None,
        printer_copies: Optional[int] = None,
        printer_range_start: Optional[int] = None,
        printer_range_end: Optional[int] = None,
        printer_collated: Optional[bool] = None,
        printer_orientation: Optional[str] = None,
        printer_use_print_range: Optional[bool] = None,
        cache_cache_type: Optional[str] = None,
        cache_shortcut_cache_format: Optional[str] = None,
        mobile_client_type: Optional[str] = None,
        device_id: Optional[str] = None,
        do_not_create_update_caches: Optional[bool] = None,
        re_run_hl: Optional[bool] = None,
        cache_library_cache_types: list[LibraryCacheTypes | str] = [LibraryCacheTypes.WEB],
        cache_reuse_dataset_cache: bool = False,
        cache_is_all_library_users: bool = False,
        delivery_notification_enabled: bool = False,
        delivery_personal_notification_address_id: Optional[str] = None
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
            contents (Content): The content of the subscription.
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
            mobile_client_type (str,enum): [RESERVED, BLACKBERRY, PHONE, TABLET,
                ANDROID]
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
        if self.delivery.mode in ['SNAPSHOT', 'PERSONAL_VIEW', 'SHARED_LINK', 'UNSUPPORTED']:
            helper.exception_handler(
                msg=f'{self.delivery.mode} subscription altering is not supported.',
                exception_type=NotSupportedError
            )
        # Schedules logic
        schedules = self.__validate_schedules(schedules=schedules)
        if not schedules:
            schedules = [{'id': sch.id} for sch in self.schedules]

        # Content logic
        if contents:
            contents = self.__validate_contents(contents)
        else:
            contents = [cont.to_dict() for cont in self.contents]

        # Delivery logic
        if delivery:
            temp_delivery = (
                Delivery.from_dict(delivery) if isinstance(delivery, dict) else delivery
            )
        else:
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
                client_type=mobile_client_type,
                device_id=device_id,
                do_not_create_update_caches=do_not_create_update_caches,
                re_run_hl=re_run_hl,
                cache_type=cache_cache_type,
                shortcut_cache_format=cache_shortcut_cache_format,
                library_cache_types=cache_library_cache_types,
                reuse_dataset_cache=cache_reuse_dataset_cache,
                is_all_library_users=cache_is_all_library_users,
                notification_enabled=delivery_notification_enabled,
                personal_notification_address_id=delivery_personal_notification_address_id
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
            self.recipients
        )

        body = {
            "name": self.__is_val_changed(name=name),
            "allowDeliveryChanges": self.__is_val_changed(
                allow_delivery_changes=allow_delivery_changes
            ),
            "multipleContents": self.__is_val_changed(multiple_contents=multiple_contents),
            "allowPersonalizationChanges": self.__is_val_changed(
                allow_personalization_changes=allow_personalization_changes
            ),
            "allowUnsubscribe": self.__is_val_changed(allow_unsubscribe=allow_unsubscribe),
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
                msg = custom_msg if custom_msg else msg
                logger.info(msg)

    def __is_val_changed(self, nested=None, **kwargs):
        for key, value in kwargs.items():
            if nested:
                return value if value != nested and value is not None else nested
            else:
                current_val = self.__dict__.get(key)
                # if not current_val: we need to get
                return value if value != current_val and value is not None else current_val

    @staticmethod
    def __validate_schedules(schedules: str | list[str] | Schedule | list[Schedule] = None):
        tmp_schedules = []
        schedules = schedules if isinstance(schedules, list) else [schedules]
        schedules = [s for s in schedules if s is not None]
        for schedule in schedules:
            if isinstance(schedule, Schedule):
                sch_id = schedule.id
            elif isinstance(schedule, str):
                sch_id = schedule
            tmp_schedules.append({'id': sch_id})

        return tmp_schedules

    @staticmethod
    def __validate_contents(contents: list[Content | dict] | Content | dict) -> list[dict]:
        contents = contents if isinstance(contents, list) else [contents]
        content_type_msg = "Contents must be dictionaries or Content objects."
        return [
            content.to_dict(camel_case=True) if isinstance(content, Content) else content if
            isinstance(content, dict) else helper.exception_handler(content_type_msg, TypeError)
            for content in contents
        ]

    def execute(self):
        """Executes a subscription with given name or GUID for given project.
        """
        self.alter(
            send_now=True, custom_msg=f"Executed subscription '{self.name}' with ID '{self.id}'."
        )

    @method_version_handler('11.2.0203')
    def delete(self, force: bool = False) -> bool:
        """Delete a subscription. Returns True if deletion was successful.

        Args:
            force: If True, no additional prompt will be shown before deleting
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to delete subscription '{}' with ID: {}? [Y/N]: ".format(
                    self.name, self.id
                )
            )
        if force or user_input == 'Y':
            response = subscriptions.remove_subscription(self.connection, self.id, self.project_id)
            if response.ok and config.verbose:
                logger.info(f"Deleted subscription '{self.name}' with ID: {self.id}.")
            return response.ok
        else:
            return False

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
        recipient_id: Optional[str] = None,
        recipient_type: Optional[str] = None,
        recipient_include_type: str = 'TO'
    ):
        """Adds recipient to subscription. You can either specify id, type and
        include_type of single recipient, or just pass recipients list as a
        list of dictionaries.

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
                    "includeType": recipient_include_type
                }
            )
        elif (recipients == [] and recipient_id is None) or (len(recipients) >= 1
                                                             and recipient_id):
            msg = (
                "Specify either a recipient ID, type and include type or pass recipients "
                "dictionaries"
            )
            helper.exception_handler(msg, ValueError)

        all_recipients = self.recipients.copy()
        ready_recipients = self.__prepare_recipients(recipients)

        ready_recipients = self._validate_recipients(
            connection=self.connection,
            contents=self.contents,
            recipients=ready_recipients,
            project_id=self.project_id,
            delivery_mode=self.delivery.mode,
            current_recipients=self.recipients
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
                "Subscription must have at last one recipient. Add new recipient before removing."
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
                "You cannot remove all existing recipients. Add new recipient before removing."
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
                if list(recipient.keys()) in [['id', 'type', 'includeType'], ['id', 'type']]:
                    __already_recipient(recipient['id'])
                else:
                    helper.exception_handler(not_dict_msg, TypeError)
            if isinstance(recipient, str):
                __already_recipient(recipient)
        return ready_recipients

    def __change_delivery_properties(  # NOSONAR
        self,  # NOSONAR
        mode: Optional[str] = None,
        expiration: Optional[str] = None,
        contact_security: Optional[bool] = None,
        subject: Optional[str] = None,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        compress: Optional[bool] = None,
        zip_settings: Optional[ZipSettings] = None,
        zip_filename: Optional[str] = None,
        zip_password: Optional[str] = None,
        zip_password_protect: Optional[bool] = None,
        space_delimiter: Optional[str] = None,
        send_content_as: Optional[SendContentAs] = None,
        overwrite_older_version: Optional[bool] = None,
        burst_sub_folder: Optional[str] = None,
        copies: Optional[int] = None,
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
        collated: Optional[bool] = None,
        orientation: Optional[Orientation] = None,
        use_print_range: Optional[bool] = None,
        cache_type: Optional[CacheType] = None,
        shortcut_cache_format: Optional[ShortcutCacheFormat] = None,
        client_type: Optional[ClientType] = None,
        device_id: Optional[str] = None,
        do_not_create_update_caches: Optional[bool] = None,
        re_run_hl: Optional[bool] = None,
        library_cache_types: list[LibraryCacheTypes | str] = [LibraryCacheTypes.WEB],
        reuse_dataset_cache: bool = False,
        is_all_library_users: bool = False,
        notification_enabled: bool = False,
        personal_notification_address_id: Optional[str] = None,
    ):

        func = self.__change_delivery_properties
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        # create dict of properties to be changed
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        # 'zip_settings' is 'zip' in object
        if 'zip_settings' in properties.keys():
            properties['zip'] = properties.pop('zip_settings')

        obj_dict = self.delivery.VALIDATION_DICT
        obj_mode_dict = self.delivery.__dict__[self.delivery.mode.lower()].VALIDATION_DICT
        obj_mode_zip_dict = {
            "zip_filename": str,
            "zip_password": str,
            "zip_password_protect": bool,
        }

        if properties:  # at this point only not None values in properties
            for key, value in properties.items():
                if key in obj_dict.keys():  # Highest level parameters. Mainly mode type and object
                    # Change mode or set attr if it's not mode param
                    if not self.delivery.change_mode(key, value):
                        self.delivery.__setattr__(key, value)
                elif key in obj_mode_dict.keys():  # parameters of a particular mode e.g. of email
                    helper.rsetattr(self.delivery, f'{self.delivery.mode.lower()}.{key}', value)
                elif key in obj_mode_zip_dict.keys():  # zip settings
                    key = key[4:]
                    if not helper.rgetattr(
                            self.delivery, f'{self.delivery.mode.lower()}.zip', None):
                        helper.rsetattr(
                            self.delivery, f'{self.delivery.mode.lower()}.zip', ZipSettings()
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
        project_id: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> "Subscription":
        """Initialize Subscription object from dictionary.
        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted"""
        if source.get('project_id') and not project_id:
            project_id = source['project_id']
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
        )
        _source = {
            **source,
            "project_id": project_id,
        }
        obj: Subscription = super().from_dict(_source, connection)

        return obj

    @classmethod
    @method_version_handler('11.3.0000')
    def __create(  # NOSONAR
            cls,  # NOSONAR
            connection: Connection,
            name: str,
            contents: Content | dict,
            project_id: Optional[str] = None,
            project_name: Optional[str] = None,
            multiple_contents: Optional[bool] = None,
            allow_delivery_changes: Optional[bool] = None,
            allow_personalization_changes: Optional[bool] = None,
            allow_unsubscribe: Optional[bool] = None,
            send_now: Optional[bool] = None,
            owner_id: Optional[str] = None,
            schedules: Optional[str | list[str] | Schedule | list[Schedule]] = None,
            recipients: Optional[list[dict] | list[str]] = None,
            delivery: Optional[Delivery | dict] = None,
            delivery_mode: str = Delivery.DeliveryMode.EMAIL,
            delivery_expiration_date: Optional[str] = None,
            contact_security: bool = True,
            filename: Optional[str] = None,
            compress: bool = False,
            space_delimiter: Optional[str] = None,
            email_subject: Optional[str] = None,
            email_message: Optional[str] = None,
            email_send_content_as: str = SendContentAs.DATA,
            overwrite_older_version: bool = False,
            zip_filename: Optional[str] = None,
            zip_password_protect: Optional[bool] = None,
            zip_password: Optional[str] = None,
            file_burst_sub_folder: Optional[str] = None,
            printer_copies: int = 1,
            printer_range_start: int = 0,
            printer_range_end: int = 0,
            printer_collated: bool = True,
            printer_orientation: str = Orientation.PORTRAIT,
            printer_use_print_range: bool = False,
            cache_cache_type: CacheType | str = CacheType.RESERVED,
            cache_shortcut_cache_format: ShortcutCacheFormat | str = ShortcutCacheFormat.RESERVED,
            mobile_client_type: str = ClientType.RESERVED,
            device_id: Optional[str] = None,
            do_not_create_update_caches: bool = True,
            re_run_hl: bool = True,
            cache_library_cache_types: list[LibraryCacheTypes | str] = [LibraryCacheTypes.WEB],
            cache_reuse_dataset_cache: bool = False,
            cache_is_all_library_users: bool = False,
            delivery_notification_enabled: bool = False,
            delivery_personal_notification_address_id: Optional[str] = None):
        """Creates a subscription Create_Subscription_Outline.

        Args:
            connection (Connection): a MicroStrategy connection object
            name (str): name of the subscription,
            contents (Content): The content settings.
            project_id (str): project ID,
            project_name (str): project name,
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
            delivery_expiration_date (str): expiration date of the subscription,
                format should be yyyy-MM-dd,
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
            mobile_client_type (str,enum):
                [RESERVED, BLACKBERRY, PHONE, TABLET, ANDROID]
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
        if connection._iserver_version <= '11.3.0100':
            cache_cache_type = LegacyCacheType[cache_cache_type.name]
        else:
            cache_cache_type = CacheType[cache_cache_type.name]
        name = name if len(name) <= 255 else helper.exception_handler(
            "Name too long. Max name length is 255 characters."
        )
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )

        if not schedules:
            msg = "Please specify 'schedules' parameter."
            helper.exception_handler(msg)

        schedules = cls.__validate_schedules(schedules=schedules)

        # Content logic
        contents = contents if isinstance(contents, list) else [contents]
        content_type_msg = "Contents must be dictionaries or Content objects."
        contents = [
            content.to_dict(camel_case=True) if isinstance(content, Content) else content if
            isinstance(content, dict) else helper.exception_handler(content_type_msg, TypeError)
            for content in contents
        ]

        # Delivery logic
        if delivery:
            temp_delivery = Delivery.from_dict(delivery
                                               ) if isinstance(delivery, dict) else delivery
        else:
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
                personal_notification_address_id=delivery_personal_notification_address_id
            )
        delivery = temp_delivery.to_dict(camel_case=True)

        # Recipients logic
        recipients = cls._validate_recipients(
            connection, contents, recipients, project_id, delivery['mode']
        )

        # Create body
        body = {
            "name": name,
            "allowDeliveryChanges": allow_delivery_changes,
            "allowPersonalizationChanges": allow_personalization_changes,
            "allowUnsubscribe": allow_unsubscribe,
            "sendNow": send_now,
            "owner": {
                "id": owner_id
            },
            "schedules": schedules,
            "contents": contents,
            "recipients": recipients,
            "delivery": delivery
        }

        body = helper.delete_none_values(body, recursion=True)
        response = subscriptions.create_subscription(connection, project_id, body)
        if config.verbose:
            unpacked_response = response.json()
            logger.info(f"Created subscription '{name}' with ID: '{unpacked_response['id']}'.")
        return cls.from_dict(response.json(), connection, project_id)

    @staticmethod
    def _validate_recipients(
        connection: "Connection",
        contents: list[Content | dict],
        recipients: list[str] | list[dict] | str,
        project_id: str,
        delivery_mode: str,
        current_recipients: Optional[list[dict]] = None
    ):

        def __not_available(recipient):
            if recipient in available_recipients_ids:
                rec = helper.filter_list_of_dicts(available_recipients, id=recipient)
                formatted_recipients.append(rec[0])
            else:
                msg = (
                    f"'{recipient}' is not a valid recipient ID for selected content "
                    "and delivery mode. Available recipients: \n"
                    f"{pformat(available_recipients,indent=2)}"
                )
                helper.exception_handler(msg, ValueError)

        recipients = recipients if isinstance(recipients, list) else [recipients]
        body = {
            "contents": [
                cont.to_dict() if isinstance(cont, Content) else cont for cont in contents
            ]
        }
        available_recipients = subscriptions.available_recipients(
            connection, project_id, body, delivery_mode
        )
        if not current_recipients:
            current_recipients = []
        available_recipients = available_recipients.json()['recipients'] + current_recipients
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
                    helper.exception_handler(
                        "Recipients must be a dictionaries or a strings, not a {}".format(
                            type(recipient)
                        ),
                        exception_type=TypeError
                    )
        return formatted_recipients
