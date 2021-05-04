from enum import Enum
from mstrio.utils.helper import camel_to_snake, exception_handler, Dictable
from datetime import datetime


class SendContentAs(Enum):
    DATA = "data"
    DATA_AND_HISTORY_LIST = "data_and_history_list"
    DATA_AND_LINK_AND_HISTORY_LIST = "data_and_link_and_history_list"
    LINK_AND_HISTORY_LIST = "link_and_history_list"


class Orientation(Enum):
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"


class CacheType(Enum):
    RESERVED = "RESERVED"
    SHORTCUT = "SHORTCUT"
    BOOKMARK = "BOOKMARK"
    SHORTCUTWITHBOOKMARK = "SHORTCUTWITHBOOKMARK"


class ShortcutCacheFormat(Enum):
    RESERVED = "RESERVED"
    JSON = "JSON"
    BINARY = "BINARY"
    BOTH = "BOTH"


class ClientType(Enum):
    RESERVED = "RESERVED"
    BLACKBERRY = "BLACKBERRY"
    PHONE = "PHONE"
    TABLET = "TABLET"
    ANDROID = "ANDROID"


class DeliveryDictable(Dictable):
    VALIDATION_DICT = {}

    @classmethod
    def from_dict(cls, dictionary):
        """Initialize Delivery object from dictionary."""
        obj = cls.__new__(cls)
        super(DeliveryDictable, obj).__init__()
        dictionary = camel_to_snake(dictionary)
        for key, value in dictionary.items():
            if key == 'zip':
                obj.__setattr__(key, ZipSettings.from_dict(value))
            else:
                obj.__setattr__(key, value)
        return obj

    def validate(self):
        for key, value in self.__dict__.items():
            vtype = self.VALIDATION_DICT[key][0]
            obligatory = self.VALIDATION_DICT[key][1]
            if value and not isinstance(value, vtype):
                exception_handler(
                    "{} has incorrect type {}. Correct type is {}.".format(
                        key, type(value), vtype), TypeError)
            elif value is None and obligatory:
                exception_handler("{} is obligatory and cannot be empty.".format(key), ValueError)


class ZipSettings(DeliveryDictable):
    """Optional compression settings

    Attributes:
        filename: Filename of the compressed content
        password: Optional password for the compressed file
        password_protect: Whether to password protect file or not
    """
    VALIDATION_DICT = {
        "filename": [str, False],
        "password": [str, False],
        "password_protect": [bool, False]
    }

    def __init__(self, filename: str = None, password: str = None, password_protect: bool = False):
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

    class DeliveryMode(Enum):
        EMAIL = "EMAIL"
        FILE = "FILE"
        PRINTER = "PRINTER"
        HISTORY_LIST = "HISTORY_LIST"
        CACHE = "CACHE"
        MOBILE = "MOBILE"
        FTP = "FTP",
        SNAPSHOT = "SNAPSHOT",
        PERSONAL_VIEW = "PERSONAL_VIEW"
        SHARED_LINK = "SHARED_LINK"
        UNSUPPORTED = "UNSUPPORTED"

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

        def __init__(self, subject: str = None, message: str = None, filename: str = None,
                     space_delimiter: str = None, send_content_as: SendContentAs = None,
                     overwrite_older_version: bool = False, zip: ZipSettings = None):
            self.subject = subject
            self.message = message
            self.filename = filename
            self.space_delimiter = space_delimiter
            self.send_content_as = send_content_as
            self.overwrite_older_version = overwrite_older_version
            self.zip = zip
            self.validate()

        def validate(self):
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

        def __init__(self, filename: str = None, space_delimiter: str = None,
                     burst_sub_folder: str = None, zip: ZipSettings = None):
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

        def __init__(self, copies: int = None, range_start: int = None, range_end: int = None,
                     collated: bool = False, orientation: Orientation = Orientation.PORTRAIT.name,
                     use_print_range: bool = False):
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
            "filename": [str, False],
            "space_delimiter": [str, False],
            "zip": [ZipSettings, False]
        }

        def __init__(self, space_delimiter: str = None, filename: str = None,
                     zip: ZipSettings = None):
            self.space_delimiter = space_delimiter
            self.filename = filename
            self.zip = zip

    class Cache(DeliveryDictable):
        """Delivery properties for Cache subscriptions

        Attributes:
            cache_type: The cache type to use
            shortcut_cache_format: The shortcut cache format to use
        """
        VALIDATION_DICT = {
            "cache_type": [str, False],
            "shortcut_cache_format": [str, False],
        }

        def __init__(
                self, cache_type: CacheType = CacheType.RESERVED.name,
                shortcut_cache_format: ShortcutCacheFormat = ShortcutCacheFormat.RESERVED.name):
            self.cache_type = cache_type
            self.shortcut_cache_format = shortcut_cache_format

    class Mobile(DeliveryDictable):
        """Delivery properties for Mobile subscriptions

        Attributes:
            client_type: The mobile client type
            device_id: The mobile target application
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

        def __init__(self, client_type: ClientType = ClientType.RESERVED.name,
                     device_id: str = None, do_not_create_update_caches: bool = False,
                     overwrite_older_version: bool = False, re_run_hl: bool = False):
            self.client_type = client_type
            self.device_id = device_id
            self.do_not_create_update_caches = do_not_create_update_caches
            self.overwrite_older_version = overwrite_older_version
            self.re_run_hl = re_run_hl

    class HistoryList(DeliveryDictable):
        """Delivery properties for History List subscriptions

        Attributes:
            device_id: The mobile target application
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

        def __init__(self, device_id: str = None, do_not_create_update_caches: bool = False,
                     overwrite_older_version: bool = False, re_run_hl: bool = False):
            self.device_id = device_id
            self.do_not_create_update_caches = do_not_create_update_caches
            self.overwrite_older_version = overwrite_older_version
            self.re_run_hl = re_run_hl

    VALIDATION_DICT = {
        "mode": [str, True],
        "expiration": [str, False],
        "contactSecurity": [bool, False],
        "email": [Email, False],
        "file": [File, False],
        "printer": [Printer, False],
        "ftp": [Ftp, False],
        "cache": [Cache, False],
        "mobile": [Mobile, False],
        "history_list": [HistoryList, False]
    }

    def __init__(self, mode=DeliveryMode.EMAIL.value, expiration=None,
                 contact_security: bool = None, subject: str = None, message: str = None,
                 filename: str = None, compress: bool = False, zip: ZipSettings = None,
                 password: str = None, password_protect: bool = False, space_delimiter: str = None,
                 send_content_as: SendContentAs = SendContentAs.DATA,
                 overwrite_older_version: bool = False, burst_sub_folder: str = None,
                 copies: int = None, range_start: int = None, range_end: int = None,
                 collated: bool = False, orientation: Orientation = Orientation.PORTRAIT.name,
                 use_print_range: bool = False, cache_type: CacheType = CacheType.RESERVED.name,
                 shortcut_cache_format: ShortcutCacheFormat = ShortcutCacheFormat.RESERVED.name,
                 client_type: ClientType = ClientType.RESERVED.name, device_id: str = None,
                 do_not_create_update_caches: bool = False, re_run_hl: bool = False,
                 email: Email = None, file: File = None):
        self.mode = mode
        if expiration:
            if not self._expiration_check(expiration):
                exception_handler(
                    "Expiration date must be later or equal to {}".format(
                        datetime.now().strftime("%Y-%m-%d")), ValueError)
            else:
                self.expiration = expiration
        self.contact_security = contact_security
        temp_zip = ZipSettings(
            filename, password, password_protect
        ) if zip is None and compress else zip if zip is not None and compress else None

        self.email = self.Email(
            subject, message, filename, space_delimiter, send_content_as, overwrite_older_version,
            temp_zip) if self.DeliveryMode(mode) == self.DeliveryMode.EMAIL else None
        self.file = self.File(
            filename, space_delimiter, burst_sub_folder,
            temp_zip) if self.DeliveryMode(mode) == self.DeliveryMode.FILE else None
        self.printer = self.Printer(
            copies, range_start, range_end, collated, orientation,
            use_print_range) if self.DeliveryMode(mode) == self.DeliveryMode.PRINTER else None
        self.ftp = self.Ftp(space_delimiter, filename,
                            temp_zip) if self.DeliveryMode(mode) == self.DeliveryMode.FTP else None
        self.cache = self.Cache(
            cache_type,
            shortcut_cache_format) if self.DeliveryMode(mode) == self.DeliveryMode.CACHE else None
        self.mobile = self.Mobile(
            client_type, device_id, do_not_create_update_caches, overwrite_older_version,
            re_run_hl) if self.DeliveryMode(mode) == self.DeliveryMode.MOBILE else None
        self.history_list = self.HistoryList(
            device_id, do_not_create_update_caches, overwrite_older_version,
            re_run_hl) if self.DeliveryMode(mode) == self.DeliveryMode.HISTORY_LIST else None

    @classmethod
    def from_dict(cls, dictionary):
        """Initialize Delivery object from dictionary."""
        obj = cls.__new__(cls)
        super(Delivery, obj).__init__()
        dictionary = camel_to_snake(dictionary)
        for key, value in dictionary.items():
            if key == 'email':
                obj.__setattr__(key, cls.Email.from_dict(value))
            elif key == 'file':
                obj.__setattr__(key, cls.File.from_dict(value))
            elif key == 'mobile':
                obj.__setattr__(key, cls.Mobile.from_dict(value))
            elif key == 'ftp':
                obj.__setattr__(key, cls.Ftp.from_dict(value))
            elif key == 'cache':
                obj.__setattr__(key, cls.Cache.from_dict(value))
            elif key == 'history_list':
                obj.__setattr__(key, cls.HistoryList.from_dict(value))
            else:
                obj.__setattr__(key, value)

        return obj

    def _expiration_check(self, date):
        now = datetime.now().date()
        date = datetime.strptime(date, '%Y-%m-%d').date()

        return date >= now
