from datetime import datetime
from enum import auto
from typing import Optional, Union

from mstrio.utils.enum_helper import AutoName, AutoUpperName
from mstrio.utils.helper import camel_to_snake, Dictable, exception_handler


class SendContentAs(AutoName):
    DATA = auto()
    DATA_AND_HISTORY_LIST = auto()
    DATA_AND_LINK_AND_HISTORY_LIST = auto()
    LINK_AND_HISTORY_LIST = auto()


class Orientation(AutoUpperName):
    PORTRAIT = auto()
    LANDSCAPE = auto()


class CacheType(AutoName):
    RESERVED = auto()
    SHORTCUT = auto()
    SHORTCUTWITHBOOKMARK = 'shortcut_and_bookmark'


class LegacyCacheType(AutoUpperName):
    """
    Available values when using environment with version 11.3.0100 or lower
    """
    RESERVED = auto()
    SHORTCUT = auto()
    SHORTCUTWITHBOOKMARK = auto()
    BOOKMARK = auto()


class ShortcutCacheFormat(AutoUpperName):
    RESERVED = auto()
    JSON = auto()
    BINARY = auto()
    BOTH = auto()


class ClientType(AutoUpperName):
    RESERVED = auto()
    BLACKBERRY = auto()
    PHONE = auto()
    TABLET = auto()
    ANDROID = auto()


class LibraryCacheTypes(AutoName):
    ANDROID = auto()
    ANDROID_AND_IOS = auto()
    IOS = auto()
    WEB = auto()


class DeliveryDictable(Dictable):

    VALIDATION_DICT = {}

    @classmethod
    def from_dict(cls, source, **kwargs):
        """Initialize Delivery object from dictionary."""
        obj = cls.__new__(cls)
        super(DeliveryDictable, obj).__init__()
        source = camel_to_snake(source)
        for key, value in source.items():
            if key == 'zip':
                setattr(obj, key, ZipSettings.from_dict(value))
            else:
                setattr(obj, key, value)
        return obj

    def validate(self):
        """Validate whether all obligatory properties of the Delivery object
            are present and whether all the properties present are of
            correct types."""
        for key, value in self.__dict__.items():
            vtype = self.VALIDATION_DICT[key][0]
            obligatory = self.VALIDATION_DICT[key][1]
            if value and not isinstance(value, vtype):
                exception_handler(
                    "{} has incorrect type {}. Correct type is {}.".format(
                        key, type(value), vtype
                    ),
                    TypeError
                )
            elif value is None and obligatory:
                exception_handler(f"{key} is obligatory and cannot be empty.", ValueError)


class ZipSettings(DeliveryDictable):
    """Optional compression settings

    Attributes:
        filename: Filename of the compressed content
        password: Optional password for the compressed file
        password_protect: Whether to password protect file or not
    """

    VALIDATION_DICT = {
        "filename": [str, False], "password": [str, False], "password_protect": [bool, False]
    }

    def __init__(
        self,
        filename: Optional[str] = None,
        password: Optional[str] = None,
        password_protect: bool = False
    ):
        self.filename = filename
        self.password = password if password_protect else None
        self.password_protect = password_protect
        self.validate()


class Delivery(DeliveryDictable):
    """Delivery settings object

    Attributes:
        mode: The subscription delivery mode (i.e. email, file, printer, etc.)
        expiration: Expiration date of the subscription, format should
            be yyyy-MM-dd
        contact_security: Whether to use contact security for each contact
            group member
        email: Email delivery properties object
        file: File delivery properties object
        printer: File delivery properties object
        ftp: FTP delivery properties object
        cache: Cache delivery properties
        mobile: Mobile delivery properties object
        history_list: HistoryList delivery properties
    """

    class DeliveryMode(AutoUpperName):
        EMAIL = auto()
        FILE = auto()
        PRINTER = auto()
        HISTORY_LIST = auto()
        CACHE = auto()
        MOBILE = auto()
        FTP = auto()
        SNAPSHOT = auto()
        PERSONAL_VIEW = auto()
        SHARED_LINK = auto()
        UNSUPPORTED = auto()

    class Email(DeliveryDictable):
        """Delivery properties for Email subscriptions

        Attributes:
            subject: The email subject associated with the subscription
            message: The email body of subscription
            filename: The filename that will be delivered when the subscription
                is executed
            space_delimiter: The space delimiter
            send_content_as: Send subscribed content as one of [data,
                data_and_history_list, data_and_link_and_history_list,
                link_and_history_list]
            overwrite_older_version: Whether the current subscription will
                overwrite earlier versions of the same report or document
                in the history list
            zip: Optional compression settings object
        """

        VALIDATION_DICT = {
            "subject": [str, True],
            "message": [str, False],
            "filename": [str, False],
            "space_delimiter": [str, False],
            "send_content_as": [str, False],
            "overwrite_older_version": [bool, False],
            "zip": [ZipSettings, False]
        }

        def __init__(
            self,
            subject: Optional[str] = None,
            message: Optional[str] = None,
            filename: Optional[str] = None,
            space_delimiter: Optional[str] = None,
            send_content_as: Optional[SendContentAs] = None,
            overwrite_older_version: bool = False,
            zip: Optional[ZipSettings] = None
        ):
            self.subject = subject
            self.message = message
            self.filename = filename
            self.space_delimiter = space_delimiter
            self.send_content_as = send_content_as
            self.overwrite_older_version = overwrite_older_version
            self.zip = zip
            self.validate()

        def validate(self):
            """Validate whether all obligatory properties of the Delivery
                object are present, whether all the properties present are
                of correct types and whether the message and subject do
                not exceed the charater limits."""
            if self.message and len(self.message) > 1000:
                exception_handler("Message too long. Max message length is 1000 characters.")
            if self.subject and len(self.subject) > 265:
                exception_handler("Subject too long. Max subject length is 265 characters.")
            super().validate()

    class File(DeliveryDictable):
        """Delivery properties for File subscriptions

        Attributes:
            filename: The filename that will be delivered when the subscription
                is executed
            space_delimiter: The space delimiter
            burst_sub_folder:The burst sub folder
            zip: Optional compression settings object
        """

        VALIDATION_DICT = {
            "filename": [str, False],
            "space_delimiter": [str, False],
            "burst_sub_folder": [str, False],
            "zip": [ZipSettings, False]
        }

        def __init__(
            self,
            filename: Optional[str] = None,
            space_delimiter: Optional[str] = None,
            burst_sub_folder: Optional[str] = None,
            zip: Optional[ZipSettings] = None
        ):
            self.filename = filename
            self.space_delimiter = space_delimiter
            self.burst_sub_folder = burst_sub_folder
            self.zip = zip

    class Printer(DeliveryDictable):
        """Delivery properties for Printer subscriptions

        Attributes:
            copies: The number of copies that should be printed
            range_start: The number indicating the first report page that
                should be printed
            range_end: The number indicating the last report page that should
                be printed
            collated: Whether the printing should be collated or not
            orientation: Whether orientation is portrait or landscape
            use_print_range: Whether a print range should be used
        """

        VALIDATION_DICT = {
            "copies": [int, False],
            "range_start": [int, False],
            "range_end": [int, False],
            "collated": [bool, False],
            "orientation": [str, False],
            "use_print_range": [bool, False]
        }

        def __init__(
            self,
            copies: Optional[int] = None,
            range_start: Optional[int] = None,
            range_end: Optional[int] = None,
            collated: bool = False,
            orientation: Orientation = Orientation.PORTRAIT.name,
            use_print_range: bool = False
        ):
            self.copies = copies
            self.range_start = range_start
            self.range_end = range_end
            self.collated = collated
            self.orientation = orientation
            self.use_print_range = use_print_range

    class Ftp(DeliveryDictable):
        """Delivery properties for FTP subscriptions

        Attributes:
            filename: The filename that will be delivered when the subscription
                is executed
            space_delimiter: The space delimiter
            zip: Optional compression settings object
        """

        VALIDATION_DICT = {
            "filename": [str, False], "space_delimiter": [str, False], "zip": [ZipSettings, False]
        }

        def __init__(
            self,
            space_delimiter: Optional[str] = None,
            filename: Optional[str] = None,
            zip: Optional[ZipSettings] = None
        ):
            self.space_delimiter = space_delimiter
            self.filename = filename
            self.zip = zip

    class Cache(DeliveryDictable):
        """Delivery properties for Cache subscriptions

        Attributes:
            cache_type: The cache type to use
            shortcut_cache_format: The shortcut cache format to use
            library_cache_types: Set of library cache types,
                available types can be web, android, ios
            reuse_dataset_cache: Whether to reuse dataset cache
            is_all_library_users: Whether for all library users
        """

        VALIDATION_DICT = {
            "library_cache_types": [list, False],
            "reuse_dataset_cache": [bool, False],
            "is_all_library_users": [bool, False],
        }

        def __init__(
            self,
            cache_type: CacheType = CacheType.RESERVED,
            shortcut_cache_format: ShortcutCacheFormat = ShortcutCacheFormat.RESERVED,
            library_cache_types: Optional[list[LibraryCacheTypes]] = None,
            reuse_dataset_cache: bool = False,
            is_all_library_users: bool = False
        ):
            self.cache_type = cache_type
            self.shortcut_cache_format = shortcut_cache_format
            self.library_cache_types = library_cache_types
            self.reuse_dataset_cache = reuse_dataset_cache
            self.is_all_library_users = is_all_library_users

    class Mobile(DeliveryDictable):
        """Delivery properties for Mobile subscriptions

        Attributes:
            client_type: The mobile client type
            device_id: The mobile target project
            do_not_create_update_caches: Whether the subscription will use
                a existing cache
            overwrite_older_version: Whether the current subscription will
                overwrite earlier versions of the same report or document in
                the history list
            re_run_hl: Whether the subscription will re-run against warehouse
        """

        VALIDATION_DICT = {
            "client_type": [str, False],
            "device_id": [str, False],
            "do_not_create_update_caches": [bool, False],
            "overwrite_older_version": [bool, False],
            "re_run_hl": [bool, False]
        }

        def __init__(
            self,
            client_type: ClientType = ClientType.RESERVED.name,
            device_id: Optional[str] = None,
            do_not_create_update_caches: bool = False,
            overwrite_older_version: bool = False,
            re_run_hl: bool = False
        ):
            self.client_type = client_type
            self.device_id = device_id
            self.do_not_create_update_caches = do_not_create_update_caches
            self.overwrite_older_version = overwrite_older_version
            self.re_run_hl = re_run_hl

    class HistoryList(DeliveryDictable):
        """Delivery properties for History List subscriptions

        Attributes:
            device_id: The mobile target project
            do_not_create_update_caches: Whether the subscription will use
                a existing cache
            overwrite_older_version: Whether the current subscription will
                overwrite earlier versions of the same report or document in
                the history list
            re_run_hl: Whether the subscription will re-run against warehouse
        """

        VALIDATION_DICT = {
            "device_id": [str, False],
            "do_not_create_update_caches": [bool, False],
            "overwrite_older_version": [bool, False],
            "re_run_hl": [bool, False]
        }

        def __init__(
            self,
            device_id: Optional[str] = None,
            do_not_create_update_caches: bool = False,
            overwrite_older_version: bool = False,
            re_run_hl: bool = False
        ):
            self.device_id = device_id
            self.do_not_create_update_caches = do_not_create_update_caches
            self.overwrite_older_version = overwrite_older_version
            self.re_run_hl = re_run_hl

    VALIDATION_DICT = {
        "mode": [str, True],
        "expiration": [str, False],
        "contact_security": [bool, False],
        "email": [Email, False],
        "file": [File, False],
        "printer": [Printer, False],
        "ftp": [Ftp, False],
        "cache": [Cache, False],
        "mobile": [Mobile, False],
        "history_list": [HistoryList, False]
    }

    def __init__(
        self,
        mode=DeliveryMode.EMAIL.value,
        expiration: str = None,
        contact_security: Optional[bool] = None,
        subject: Optional[str] = None,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        compress: bool = False,
        zip: Optional[ZipSettings] = None,
        password: Optional[str] = None,
        password_protect: bool = False,
        space_delimiter: Optional[str] = None,
        send_content_as: SendContentAs = SendContentAs.DATA,
        overwrite_older_version: bool = False,
        burst_sub_folder: Optional[str] = None,
        copies: Optional[int] = None,
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
        collated: bool = False,
        orientation: Orientation = Orientation.PORTRAIT.name,
        use_print_range: bool = False,
        client_type: ClientType = ClientType.RESERVED.name,
        device_id: Optional[str] = None,
        do_not_create_update_caches: bool = False,
        re_run_hl: bool = False,
        email: Optional[Email] = None,
        file: Optional[File] = None,
        cache_type: Union[CacheType, str] = CacheType.RESERVED,
        shortcut_cache_format: Union[ShortcutCacheFormat, str] = ShortcutCacheFormat.RESERVED,
        library_cache_types: list[Union[LibraryCacheTypes,
                                        str]] = [LibraryCacheTypes.WEB],  # noqa: E501
        reuse_dataset_cache: bool = False,
        is_all_library_users: bool = False,
        notification_enabled: bool = False,
        personal_notification_address_id: Optional[str] = None
    ):
        self.mode = mode
        if expiration:
            if not self._expiration_check(expiration):
                exception_handler(
                    "Expiration date must be later or equal to {}".format(
                        datetime.now().strftime("%Y-%m-%d")
                    ),
                    ValueError
                )
            else:
                self.expiration = expiration
        self.contact_security = contact_security

        if zip is None and compress:
            temp_zip = ZipSettings(filename, password, password_protect)
        elif zip is not None and compress:
            temp_zip = zip
        else:
            temp_zip = None

        if self.DeliveryMode(mode) == self.DeliveryMode.EMAIL:
            self.email = self.Email(
                subject,
                message,
                filename,
                space_delimiter,
                send_content_as,
                overwrite_older_version,
                temp_zip
            )
        elif self.DeliveryMode(mode) == self.DeliveryMode.FILE:
            self.file = self.File(filename, space_delimiter, burst_sub_folder, temp_zip)
        elif self.DeliveryMode(mode) == self.DeliveryMode.PRINTER:
            self.printer = self.Printer(
                copies, range_start, range_end, collated, orientation, use_print_range
            )
        elif self.DeliveryMode(mode) == self.DeliveryMode.FTP:
            self.ftp = self.Ftp(space_delimiter, filename, temp_zip)
        elif self.DeliveryMode(mode) == self.DeliveryMode.CACHE:
            self.cache = self.Cache(
                cache_type,
                shortcut_cache_format,
                library_cache_types,
                reuse_dataset_cache,
                is_all_library_users
            )
        elif self.DeliveryMode(mode) == self.DeliveryMode.MOBILE:
            self.mobile = self.Mobile(
                client_type,
                device_id,
                do_not_create_update_caches,
                overwrite_older_version,
                re_run_hl
            )
        elif self.DeliveryMode(mode) == self.DeliveryMode.HISTORY_LIST:
            self.history_list = self.HistoryList(
                device_id, do_not_create_update_caches, overwrite_older_version, re_run_hl
            )
        if notification_enabled:
            self.notification_enabled = notification_enabled
            self.personal_notification = {"address_id": personal_notification_address_id}

    @classmethod
    def from_dict(cls, source, **kwargs):
        """Initialize Delivery object from dictionary."""
        obj = cls.__new__(cls)
        super(Delivery, obj).__init__()
        source = camel_to_snake(source)
        for key, value in source.items():
            if not obj.change_mode(key, value):  # Change mode or set attr if its not mode param
                setattr(obj, key, value)
        return obj

    def change_mode(self, mode_name: str, mode_value) -> bool:
        """Change mode of the Delivery object.
        Return True on success, False if `mode_name` was invalid.
        """
        if mode_name == 'email':
            self.__setattr__(mode_name, self.Email.from_dict(mode_value))
        elif mode_name == 'file':
            self.__setattr__(mode_name, self.File.from_dict(mode_value))
        elif mode_name == 'mobile':
            self.__setattr__(mode_name, self.Mobile.from_dict(mode_value))
        elif mode_name == 'ftp':
            self.__setattr__(mode_name, self.Ftp.from_dict(mode_value))
        elif mode_name == 'cache':
            self.__setattr__(mode_name, self.Cache.from_dict(mode_value))
        elif mode_name == 'history_list':
            self.__setattr__(mode_name, self.HistoryList.from_dict(mode_value))
        else:
            return False
        return True

    def _expiration_check(self, date):
        now = datetime.now().date()
        date = datetime.strptime(date, '%Y-%m-%d').date()

        return date >= now
