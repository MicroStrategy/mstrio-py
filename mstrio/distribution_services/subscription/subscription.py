from enum import Enum
from pprint import pformat, pprint
from typing import List, Union

from mstrio.api import subscriptions
import mstrio.config as config
from mstrio.connection import Connection
from mstrio.distribution_services.subscription.content import Content
from mstrio.distribution_services.subscription.delivery import (CacheType, ClientType, Delivery,
                                                                Orientation, SendContentAs,
                                                                ShortcutCacheFormat, ZipSettings)
from mstrio.server.application import Application
from mstrio.utils import helper


class RecipientsTypes(Enum):
    CONTACT_GROUP = "CONTACT_GROUP"
    USER_GROUP = "USER_GROUP"
    CONTACT = "CONTACT"
    USER = "USER"
    PERSONAL_ADDRESS = "PERSONAL_ADDRESS"
    UNSUPPORTED = "UNSUPPORTED"


class Subscription:
    """Class representation of MicroStrategy Subscription object."""

    _API_PATCH = []
    _AVAILABLE_ATTRIBUTES = {}
    _RECIPIENTS_TYPES = [
        'CONTACT_GROUP', 'USER_GROUP', 'CONTACT', 'USER', 'PERSONAL_ADDRESS', 'UNSUPPORTED'
    ]
    _RECIPIENTS_INCLUDE = ['TO', 'CC', 'BCC', None]

    def __init__(self, connection, subscription_id, application_id=None, application_name=None):
        """Initialize Subscription object, populates it with I-Server data.
        Specify either `application_id` or `application_name`.
        When `application_id` is provided (not `None`), `application_name`
        is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            subscription_id: ID of the subscription to be initialized
            application_id: Application ID
            application_name: Application name
        """
        self.connection = connection
        self.application_id = self._app_id_check(connection, application_id, application_name)
        self.id = subscription_id
        self.__fetch()

    def alter(
        self,
        name: str = None,
        allow_delivery_changes: bool = None,
        allow_personalization_changes: bool = None,
        allow_unsubscribe: bool = None,
        send_now: bool = False,
        owner_id: str = None,
        schedules_ids: Union[str, List[str]] = None,
        contents: Content = None,
        recipients: Union[List[str], List[dict]] = None,
        delivery: Union[Delivery, dict] = None,
        delivery_mode: str = None,
        custom_msg=None,
        delivery_expiration_date: str = None,
        contact_security: bool = None,
        filename: str = None,
        compress: bool = None,
        space_delimiter: str = None,
        email_subject: str = None,
        email_message: str = None,
        email_send_content_as: str = None,
        overwrite_older_version: bool = None,
        zip_filename: str = None,
        zip_password_protect: bool = None,
        zip_password: str = None,
        file_burst_sub_folder: str = None,
        printer_copies: int = None,
        printer_range_start: int = None,
        printer_range_end: int = None,
        printer_collated: bool = None,
        printer_orientation: str = None,
        printer_use_print_range: bool = None,
        cache_type: str = None,
        shortcut_cache_format: str = None,
        mobile_client_type: str = None,
        device_id: str = None,
        do_not_create_update_caches: bool = None,
        re_run_hl: bool = None,
    ):
        """
        Alter subscription.

        Args:
            connection(Connection): a MicroStrategy connection object
            name(str): name of the subscription,
            application_id(str): application ID,
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
            schedules_ids (Union[str, List[str]]) = Schedules IDs,
            contents (Content): The content of the subscription.
            recipients (Union[List[str], List[dict]]): list of recipients IDs
                or dicts,
            delivery_mode(str, enum): the subscription delivery mode [EMAIL,
                FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP, SNAPSHOT,
                PERSONAL_VIEW, SHARED_LINK, UNSUPPORTED],
            delivery_expiration_date(str): expiration date of the subscription,
                format should be yyyy-MM-dd,
            contact_security(bool): whether to use contact security for each
                contact group member,
            filename(str): the filename that will be delivered when
                the subscription is executed,
            compress(bool): whether to compress the file
            space_delimiter(str): space delimiter,
            email_subject(str): email subject associated with the subscription,
            email_message(str): email body of subscription,
            email_send_content_as(str,enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version(bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename(str): filename of the compressed content,
            zip_password_protect(bool): whether to password protect zip file,
            zip_password(str): optional password for the compressed file
            file_burst_sub_folder(str): burst sub folder,
            printer_copies(int): the number of copies that should be printed,
            printer_range_start(int): the number indicating the first report
                page that should be printed,
            printer_range_end(int): the number indicating the last report
                page that should be printed,
            printer_collated(bool): whether the printing should be collated,
            printer_orientation(str,enum): [ PORTRAIT, LANDSCAPE ]
            printer_use_print_range(bool): whether print range should be used,
            cache_type(str,enum): [RESERVED, SHORTCUT, BOOKMARK,
                SHORTCUTWITHBOOKMARK]
            shortcut_cache_format(str,enum): [RESERVED, JSON, BINARY, BOTH]
            mobile_client_type(str,enum): [RESERVED, BLACKBERRY, PHONE, TABLET,
                ANDROID]
            device_id(str): the mobile target application,
            do_not_create_update_caches(bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            re_run_hl(bool): whether subscription will re-run against warehouse
        """

        def validate(body):
            for key, value in body.items():
                if key == 'send_now':
                    pass
                elif type(value) is not self._AVAILABLE_ATTRIBUTES.get(key):
                    helper.exception_handler(
                        "{} is not a valid type of {}, valid type is {}".format(
                            type(value), key, self._AVAILABLE_ATTRIBUTES.get(key)), TypeError)

        def is_changed(nested=None, **kwargs):
            for key, value in kwargs.items():
                if nested:
                    return value if value != nested and value is not None else nested
                else:
                    current_val = self.__dict__.get(key)
                    # if not current_val: we need to get
                    return value if value != current_val and value is not None else current_val

        # Schedules logic
        schedules_ids = schedules_ids if isinstance(schedules_ids, list) else [schedules_ids]
        schedules_ids = [s for s in schedules_ids if s is not None]
        schedules = [{
            'id': sch_id
        } for sch_id in schedules_ids] if schedules_ids else [{
            'id': trig['id']
        } for trig in self.schedules]

        # Content logic
        if contents:
            contents = contents if isinstance(contents, list) else [contents]
            content_type_msg = "Contents must be dictionaries or Content objects."
            contents = [
                content.to_dict(
                    camel_case=True) if isinstance(content, Content) else content if isinstance(
                        content, dict) else helper.exception_handler(content_type_msg, TypeError)
                for content in contents
            ]
        else:
            contents = self.contents

        # Delivery logic
        if delivery:
            temp_delivery = (Delivery.from_dict(delivery)
                             if isinstance(delivery, dict) else delivery)
        else:
            temp_delivery = self.__change_delivery_properties(
                delivery_mode, delivery_expiration_date, contact_security, email_subject,
                email_message, filename, compress, None, zip_password, zip_password_protect,
                space_delimiter, email_send_content_as, overwrite_older_version,
                file_burst_sub_folder, printer_copies, printer_range_start, printer_range_end,
                printer_collated, printer_orientation, printer_use_print_range, cache_type,
                shortcut_cache_format, mobile_client_type, device_id, do_not_create_update_caches,
                re_run_hl)
        delivery = temp_delivery.to_dict(camel_case=True)

        # Recipients logic
        recipients = is_changed(recipients=recipients)
        recipients = Subscription._validate_recipients(self.connection, contents, recipients,
                                                       self.application_id, delivery['mode'])

        body = {
            "name": is_changed(name=name),
            "allowDeliveryChanges": is_changed(allow_delivery_changes=allow_delivery_changes),
            "allowPersonalizationChanges":
                is_changed(allow_personalization_changes=allow_personalization_changes),
            "allowUnsubscribe": is_changed(allow_unsubscribe=allow_unsubscribe),
            "sendNow": send_now,
            'owner': {
                'id': is_changed(nested=self.owner['id'], owner_id=owner_id)
            },
            "schedules": schedules,
            "contents": contents,
            "recipients": recipients,
            "delivery": delivery,
        }

        validate(helper.camel_to_snake(body))
        body = helper.delete_none_values(body)

        response = subscriptions.update_subscription(self.connection, self.id, self.application_id,
                                                     body)

        if response.ok:
            response = response.json()
            response = helper.camel_to_snake(response)
            for key, value in response.items():
                self.__setattr__(key, value)
            if config.verbose:
                print(custom_msg if custom_msg else "Updated subscription '{}' with ID: {}."
                      .format(self.name, self.id))

    def list_properties(self):
        """Lists all properties of subscription."""
        return {
            key: self.__dict__[key]
            for key in sorted(self.__dict__, key=helper.sort_object_properties)
            if key not in ['connection', 'application_id', '_delivery']
        }

    def execute(self):
        """Executes a subscription with given name or GUID for given project.
        """
        self.alter(
            send_now=True,
            custom_msg="Executed subscription '{}' with ID '{}'.".format(self.name, self.id))

    def delete(self, force: bool = False) -> bool:
        """Delete a subscription. Returns True if deletion was successful.

        Args:
            force: If True, no additional prompt will be showed before deleting
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to delete subscription '{}' with ID: {}? [Y/N]: ".format(
                    self.name, self.id))
        if force or user_input == 'Y':
            response = subscriptions.remove_subscription(self.connection, self.id,
                                                         self.application_id)
            if response.ok and config.verbose:
                print("Deleted subscription '{}' with ID: {}.".format(self.name, self.id))
            return response.ok
        else:
            return False

    def available_bursting_attributes(self) -> List[str]:
        """Get a list of available attributes for bursting feature."""
        contents_bursting = {}
        for content in self.contents:
            c_id = content['id']
            c_type = content['type']
            response = subscriptions.bursting_attributes(self.connection, self.application_id,
                                                         c_id, c_type.upper())

            if response.ok:
                contents_bursting[content['id']] = response.json()['burstingAttributes']

        return contents_bursting

    def available_recipients(self) -> List[dict]:
        """List available recipients for subscription content."""
        body = {"contents": self.contents}
        delivery_type = self.delivery['mode']
        response = subscriptions.available_recipients(self.connection, self.application_id, body,
                                                      delivery_type)

        if response.ok and config.verbose:
            return response.json()['recipients']

    def add_recipient(self, recipients: Union[List[dict], dict, List[str],
                                              str] = [], recipient_id: str = None,
                      recipient_type: str = None, recipient_include_type: str = 'TO'):
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
        if len(recipients) > 0:
            recipients = recipients if isinstance(recipients, list) else [recipients]
        if recipient_id and recipient_type:
            recipients.append({
                "id": recipient_id,
                "type": recipient_type,
                "includeType": recipient_include_type
            })
        elif recipients == [] and recipient_id is None:
            msg = ("Specify either a recipient ID, type and include type or pass recipients "
                   "dictionaries")
            helper.exception_handler(msg, ValueError)
        elif len(recipients) >= 1 and recipient_id:
            msg = ("Specify either a recipient ID, type and include type or pass recipients "
                   "dictionaries")
            helper.exception_handler(msg, ValueError)

        all_recipients = self.recipients.copy()
        ready_recipients = []
        exisiting_recipients = [rec['id'] for rec in self.recipients]
        for recipient in recipients:
            not_dict_msg = """Wrong recipient format, expected format is
                              {"id": recipient_id,
                               "type": "CONTACT_GROUP" / "USER_GROUP" / "CONTACT" /
                                       "USER" / "PERSONAL_ADDRESS" / "UNSUPPORTED"
                               "includeType": "TO" / "CC" / "BCC" (optional)
                              }"""
            if isinstance(recipient, dict):
                if list(recipient.keys()) == ['id', 'type', 'includeType'] or list(
                        recipient.keys()) == ['id', 'type']:
                    rec_id = recipient['id']
                    if rec_id in exisiting_recipients:
                        helper.exception_handler(
                            "{} is already a recipient of subscription".format(rec_id),
                            UserWarning)
                    else:
                        ready_recipients.append(recipient)
                else:
                    helper.exception_handler(not_dict_msg, TypeError)
            if isinstance(recipient, str):
                if recipient in exisiting_recipients:
                    helper.exception_handler(
                        "{} is already a recipient of subscription".format(recipient), UserWarning)
                else:
                    ready_recipients.append(recipient)

        ready_recipients = self._validate_recipients(self.connection, self.contents,
                                                     ready_recipients, self.application_id,
                                                     self.delivery['mode'])

        if ready_recipients:
            all_recipients.extend(ready_recipients)
            self.alter(recipients=all_recipients)
        elif config.verbose:
            print("No recipients were added to the subscription.")

    def remove_recipient(self, recipients):
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
        exisiting_recipients = [rec['id'] for rec in self.recipients]

        if len(self.recipients) == 1:
            helper.exception_handler(
                "Subscription must have at last one recipient. Add new recipient before removing.")
        for recipient in recipients:
            rec_id = recipient['id'] if isinstance(recipient, dict) else recipient
            if rec_id not in exisiting_recipients:
                helper.exception_handler("{} is not a recipient of subscription".format(rec_id),
                                         UserWarning)
            else:
                all_recipients = [rec for rec in all_recipients if rec['id'] != rec_id]
        if len(all_recipients) == 0:
            helper.exception_handler(
                "You cannot remove all existing recipients. Add new recipient before removing.")
        elif len(self.recipients) - len(all_recipients) > 0:
            self.alter(recipients=all_recipients)
        elif len(self.recipients) == len(all_recipients) and config.verbose:
            print("No recipients were removed from the subscription.")

    def __change_delivery_properties(
            self, mode=None, expiration=None, contact_security=None, subject: str = None,
            message: str = None, filename: str = None, compress: bool = None,
            zip_settings: ZipSettings = None, password: str = None, password_protect: bool = None,
            space_delimiter: str = None, send_content_as: SendContentAs = None,
            overwrite_older_version: bool = None, burst_sub_folder: str = None, copies: int = None,
            range_start: int = None, range_end: int = None, collated: bool = None,
            orientation: Orientation = None, use_print_range: bool = None,
            cache_type: CacheType = None, shortcut_cache_format: ShortcutCacheFormat = None,
            client_type: ClientType = None, device_id: str = None,
            do_not_create_update_caches: bool = None, re_run_hl: bool = None):

        func = self.__change_delivery_properties
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        # create dict of properties to be changed
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        temp_delivery = self.delivery
        not_changed = {}
        obj_dict = self._delivery.VALIDATION_DICT
        obj_mode_dict = self._delivery.__dict__[temp_delivery['mode'].lower()].VALIDATION_DICT
        obj_mode_zip_dict = {
            "filename": str,
            "password": str,
            "password_protect": bool,
        }
        # if any not None values
        if properties:
            # check if key is in delivery dict
            for key, value in properties.items():
                if temp_delivery.get(key) != value and key in obj_dict.keys():
                    temp_delivery[key] = value
                elif key in obj_mode_dict.keys():
                    check = temp_delivery[temp_delivery['mode'].lower()]
                    if check.get(key) and check.get(
                            key) != value:  # if we have key and value is different
                        check[key] = value
                    elif not check.get(key):  # if we don't have key but it can be here
                        # if key == 'filename' and compress == False:
                        check[key] = value
                elif temp_delivery[temp_delivery['mode'].lower()].get('zip'):
                    if temp_delivery[temp_delivery['mode'].lower()].get('zip').get(
                            key) != value and key in obj_mode_zip_dict.keys():
                        temp_delivery[temp_delivery['mode'].lower()]['zip'][key] = value
                elif key in obj_mode_zip_dict.keys():
                    temp_delivery[temp_delivery['mode'].lower()]['zip'] = {}
                    temp_delivery[temp_delivery['mode'].lower()]['zip'][key] = value

        return Delivery.from_dict(temp_delivery)

    def __fetch(self):
        """Retrieve object metadata."""
        response = subscriptions.get_subscription(self.connection, self.id, self.application_id)

        if response.ok:
            response = response.json()
            response = helper.camel_to_snake(response)
            for key, value in response.items():
                self._AVAILABLE_ATTRIBUTES.update({key: type(value)})
                self.__setattr__(key, value)
                if key == "delivery":
                    self._delivery = Delivery.from_dict(value)

    @classmethod
    def from_dict(cls, connection, dictionary, application_id=None, application_name=None):
        """Initialize Subscription object from dictionary.
        Specify either `application_id` or `application_name`.
        When `application_id` is provided (not `None`), `application_name` is
        omitted."""

        obj = cls.__new__(cls)
        super(Subscription, obj).__init__()
        obj.connection = connection
        obj.application_id = Subscription._app_id_check(connection, application_id,
                                                        application_name)
        dictionary = helper.camel_to_snake(dictionary)
        for key, value in dictionary.items():
            obj._AVAILABLE_ATTRIBUTES.update({key: type(value)})
            obj.__setattr__(key, value)
            if key == 'delivery':
                obj._delivery = Delivery.from_dict(value)
        return obj

    @classmethod
    def __create(
        cls,
        connection: Connection,
        name: str,
        application_id: str = None,
        application_name: str = None,
        allow_delivery_changes: bool = None,
        allow_personalization_changes: bool = None,
        allow_unsubscribe: bool = None,
        send_now: bool = None,
        owner_id: str = None,
        schedules_ids: Union[str, List[str]] = None,
        contents: Content = None,
        recipients: Union[List[dict], List[str]] = None,
        delivery: Union[Delivery, dict] = None,
        delivery_mode: str = 'EMAIL',
        delivery_expiration_date: str = None,
        contact_security: bool = True,
        filename: str = None,
        compress: bool = False,
        space_delimiter: str = None,
        email_subject: str = None,
        email_message: str = None,
        email_send_content_as: str = 'data',
        overwrite_older_version: bool = False,
        zip_filename: str = None,
        zip_password_protect: bool = None,
        zip_password: str = None,
        file_burst_sub_folder: str = None,
        printer_copies: int = 1,
        printer_range_start: int = 0,
        printer_range_end: int = 0,
        printer_collated: bool = True,
        printer_orientation: str = "PORTRAIT",
        printer_use_print_range: bool = False,
        cache_type: str = "RESERVED",
        shortcut_cache_format: str = "RESERVED",
        mobile_client_type: str = "RESERVED",
        device_id: str = None,
        do_not_create_update_caches: bool = True,
        re_run_hl: bool = True,
    ):
        """Creates a subscription Create_Subscription_Outline.

        Args:
            connection(Connection): a MicroStrategy connection object
            name(str): name of the subscription,
            application_id(str): application ID,
            application_name(str): application name,
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
            schedules_ids (Union[str, List[str]]) = Schedules IDs,
            contents (Content): The content settings.
            recipients (List[dict],List[str]): list of recipients IDs or dicts,
            delivery(Union[Delivery,dict]): delivery object or dict
            delivery_mode(str, enum): the subscription delivery mode [EMAIL,
                FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP, SNAPSHOT,
                PERSONAL_VIEW, SHARED_LINK, UNSUPPORTED],
            delivery_expiration_date(str): expiration date of the subscription,
                format should be yyyy-MM-dd,
            contact_security(bool): whether to use contact security for each
                contact group member,
            filename(str): the filename that will be delivered when
                the subscription is executed,
            compress(bool): whether to compress the file,
            space_delimiter(str): space delimiter,
            email_subject(str): email subject associated with the subscription,
            email_message(str): email body of subscription,
            email_send_content_as(str,enum): [data, data_and_history_list,
                data_and_link_and_history_list, link_and_history_list],
            overwrite_older_version(bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            zip_filename(str): filename of the compressed content,
            zip_password_protect(bool): whether to password protect zip file,
            zip_password(str): optional password for the compressed file,
            file_burst_sub_folder(str): burst sub folder,
            printer_copies(int): the number of copies that should be printed,
            printer_range_start(int): the number indicating the first report
                page that should be printed,
            printer_range_end(int): the number indicating the last report
                page that should be printed,
            printer_collated(bool): whether the printing should be collated,
            printer_orientation(str,enum): [ PORTRAIT, LANDSCAPE ]
            printer_use_print_range(bool): whether print range should be used,
            cache_type(str,enum): [RESERVED, SHORTCUT, BOOKMARK,
                SHORTCUTWITHBOOKMARK]
            shortcut_cache_format(str,enum): [RESERVED, JSON, BINARY, BOTH]
            mobile_client_type(str,enum): [RESERVED, BLACKBERRY, PHONE, TABLET,
                ANDROID]
            device_id(str): the mobile target application,
            do_not_create_update_caches(bool): whether the current subscription
                will overwrite earlier versions of the same report or document
                in the history list,
            re_run_hl(bool): whether subscription will re-run against warehouse
        """
        name = name if len(name) <= 255 else helper.exception_handler(
            "Name too long. Max name length is 255 characters.")
        application_id = Subscription._app_id_check(connection, application_id, application_name)

        # Schedules logic
        schedules_ids = schedules_ids if isinstance(schedules_ids, list) else [schedules_ids]
        schedules = [{'id': sch_id} for sch_id in schedules_ids]

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
            temp_delivery = Delivery.from_dict(delivery) if isinstance(delivery,
                                                                       dict) else delivery
        else:
            temp_delivery = Delivery(delivery_mode, delivery_expiration_date, contact_security,
                                     email_subject, email_message, filename, compress, None,
                                     zip_password, zip_password_protect, space_delimiter,
                                     email_send_content_as, overwrite_older_version,
                                     file_burst_sub_folder, printer_copies, printer_range_start,
                                     printer_range_end, printer_collated, printer_orientation,
                                     printer_use_print_range, cache_type, shortcut_cache_format,
                                     mobile_client_type, device_id, do_not_create_update_caches,
                                     re_run_hl)
        delivery = temp_delivery.to_dict(camel_case=True)

        # Recipients logic
        recipients = Subscription._validate_recipients(connection, contents, recipients,
                                                       application_id, delivery['mode'])
        schedules_ids = schedules_ids if isinstance(schedules_ids, list) else [schedules_ids]

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

        body = helper.delete_none_values(body)
        response = subscriptions.create_subscription(connection, application_id, body)
        if config.verbose:
            unpacked_response = response.json()
            print("Created subscription '{}' with ID: '{}'.".format(name, unpacked_response['id']))
        return Subscription.from_dict(connection, response.json(), application_id)

    @staticmethod
    def _validate_recipients(connection, contents: Content, recipients, application_id,
                             delivery_mode):
        recipients = recipients if isinstance(recipients, list) else [recipients]
        body = {"contents": contents}
        available_recipients = subscriptions.available_recipients(connection, application_id, body,
                                                                  delivery_mode)
        available_recipients = available_recipients.json()['recipients']
        available_recipients_ids = [rec['id'] for rec in available_recipients]
        # Format recipients list if needed
        formatted_recipients = []
        if recipients:
            for recipient in recipients:
                if isinstance(recipient, dict):
                    if recipient['id'] in available_recipients_ids:
                        formatted_recipients.append(recipient)
                    else:
                        msg = (f"'{recipient['id']}' is not a valid recipient ID for selected "
                               "content and delivery mode. Available recipients: \n"
                               f"{pformat(available_recipients, indent=2)}")
                        helper.exception_handler(msg, ValueError)
                        pprint(available_recipients)
                elif isinstance(recipient, str):
                    if recipient in available_recipients_ids:
                        rec = helper.filter_list_of_dicts(available_recipients, id=recipient)
                        formatted_recipients.append(rec[0])
                    else:
                        msg = (f"'{recipient}' is not a valid recipient ID for selected content "
                               "and delivery mode. Available recipients: \n"
                               f"{pformat(available_recipients,indent=2)}")
                        helper.exception_handler(msg, ValueError)
                        pprint(available_recipients)
                else:
                    helper.exception_handler(
                        "Recipients must be a dictionaries or a strings, not a {}".format(
                            type(recipient)), exception_type=TypeError)
        return formatted_recipients

    @staticmethod
    def _app_id_check(connection, application_id, application_name):
        """Check if the application name exists and returns the application ID.

        Args:
            connection(object): MicroStrategy connection object
            application_id: Application ID
            application_name: Application name
        """
        if application_id is None and application_name is None:
            msg = ("Please specify either 'application_name' or 'application_id' "
                   "parameter in the constructor.")
            helper.exception_handler(msg)
        if application_id is None:
            app_loaded_list = Application._list_loaded_applications(connection, to_dictionary=True,
                                                                    name=application_name)
            try:
                application_id = app_loaded_list[0]['id']
            except IndexError:
                helper.exception_handler(
                    "There is no application with the given name: '{}'".format(application_name),
                    exception_type=ValueError)

        return application_id


class EmailSubscription(Subscription):
    """Class representation of MicroStrategy Email Subscription object."""

    def __init__(self, connection, subscription_id=None, application_id=None,
                 application_name=None):
        """Initialize EmailSubscription object, populates it with I-Server data
        if subscription_id is passed.
        Specify either `application_id` or `application_name`.
        When `application_id` is provided (not `None`), `application_name` is
        omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            subscription_id: ID of the subscription to be initialized
            application_id: Application ID
            application_name: Application name
        """
        if subscription_id:
            super().__init__(connection, subscription_id, application_id, application_name)

    @classmethod
    def create(cls, connection: Connection, name: str, schedules_ids: Union[str, List[str]],
               recipients: Union[List[str], List[dict]], application_id: str = None,
               application_name: str = None, allow_delivery_changes: bool = None,
               allow_personalization_changes: bool = None, allow_unsubscribe: bool = True,
               send_now: bool = None, owner_id: str = None, contents: Content = None,
               delivery_expiration_date: str = None, contact_security: bool = None,
               email_subject: str = None, email_message: str = None, filename: str = None,
               compress: bool = False, space_delimiter: str = None,
               email_send_content_as: str = 'data', overwrite_older_version: bool = False,
               zip_filename: str = None, zip_password_protect: bool = None,
               zip_password: str = None):
        """Creates a new email subscription.

        Args:
            connection(Connection): a MicroStrategy connection object
            name(str): name of the subscription,
            application_id(str): application ID,
            application_name(str): application name,
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
            schedules_ids(Union[str, List[str]]) = Schedules IDs,
            contents(Content): The content settings.
            recipients(Union[List[str], List[dict]]): list of recipients IDs
                or dicts,
            delivery_mode(str, enum): the subscription delivery mode[EMAIL,
                FILE, PRINTER, HISTORY_LIST, CACHE, MOBILE, FTP, SNAPSHOT,
                PERSONAL_VIEW, SHARED_LINK, UNSUPPORTED],
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
            connection=connection,
            name=name,
            application_id=application_id,
            application_name=application_name,
            allow_delivery_changes=allow_delivery_changes,
            allow_personalization_changes=allow_personalization_changes,
            allow_unsubscribe=allow_unsubscribe,
            send_now=send_now,
            owner_id=owner_id,
            schedules_ids=schedules_ids,
            contents=contents,
            recipients=recipients,
            delivery_mode='EMAIL',
            delivery_expiration_date=delivery_expiration_date,
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
