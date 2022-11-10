from enum import auto
from typing import Optional, Union

from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, exception_handler


class EmailFormat(AutoName):
    UU_ENCODED = auto()
    MIME = auto()
    UNSUPPORTED = auto()


class EmailEncoding(AutoName):
    QUOTED_PRINTABLE = auto()
    BASE64 = auto()
    ASCII_7BIT = auto()
    UNSUPPORTED = auto()


class EmailMessageSensitivity(AutoName):
    NORMAL = auto()
    PERSONAL = auto()
    PRIVATE = auto()
    CONFIDENTIAL = auto()
    UNSUPPORTED = auto()


class FtpProtocol(AutoName):
    FTP = auto()
    FTP_OVER_SSL_TLS_EXPLICIT = auto()
    FTP_OVER_SSL_TLS_IMPLICIT = auto()
    SFTP = auto()
    UNSUPPORTED = auto()


class FileEncoding(AutoName):
    ENCRYPT = auto()
    COMPRESS = auto()
    NO_ENCRYPT_COMPRESS = auto()


class PrinterPaperSource(AutoName):
    AUTOMATIC = auto()
    MANUAL = auto()
    UNSUPPORTED = auto()


class PrinterPaperSize(AutoName):
    LETTER = auto()
    LETTER_SMALL = auto()
    TABLOID = auto()
    LEDGER = auto()
    LEGAL = auto()
    STATEMENT = auto()
    EXECUTIVE = auto()
    A3 = auto()
    A4 = auto()
    A4_SMALL = auto()
    A5 = auto()
    B4 = auto()
    B5 = auto()
    FOLIO = auto()
    UNSUPPORTED = auto()


class PrinterBackupLocationType(AutoName):
    PRINTER = auto()
    FILE = auto()


class PdfOddEvenPages(AutoName):
    ODD_PAGES = auto()
    EVEN_PAGES = auto()
    ALL_PAGES = auto()
    UNSUPPORTED = auto()


class PdfApplicationPriority(AutoName):
    OTHER = auto()
    I_SERVER = auto()
    UNSUPPORTED = auto()


class FileSystem(Dictable):
    """File System Options

    Attributes:
        create_folder: Whether to create required folder in the path,
            default: True
        filename_append_time_stamp: Whether to append timestamp to the file
            name, default: True
        override_filename: Whether to override filename with same name,
            default: False
        append_to_file: Whether to append to the file, default: False
    """

    def __init__(
        self,
        create_folder: bool = True,
        filename_append_time_stamp: bool = True,
        override_filename: bool = False,
        append_to_file: bool = False
    ):
        self.create_folder = create_folder
        self.filename_append_time_stamp = filename_append_time_stamp
        self.override_filename = override_filename
        self.append_to_file = append_to_file


class ConnectionParameters(Dictable):
    """Connection Parameters

    Attributes:
        retries_count: Number of Retries, default: 5
        seconds_between_retries: Time between retries (Seconds), default: 3
        delivery_timeout_seconds: Delivery Timeout (Seconds), default: 10
    """

    def __init__(
        self,
        retries_count: int = 5,
        seconds_between_retries: int = 3,
        delivery_timeout_seconds: int = 10
    ):
        self.retries_count = retries_count
        self.seconds_between_retries = seconds_between_retries
        self.delivery_timeout_seconds = delivery_timeout_seconds


class EmailMimeSettings(Dictable):
    """MIME settings for MIME email format

    Attributes:
        plain_text_html_body_encoding: Indicates the encoding for plaintext and
            HTML body, EmailEncoding enum
        text_attachment_encoding: Indicates the encoding for text attachment,
            only quoted_printable and base64 are supported, EmailEncoding enum
        binary_attachment_encoding: Indicates the encoding for text attachment,
            only quoted_printable and base64 are supported, EmailEncoding enum
        message_sensitivity: Indicates the message sensitivity,
            EmailMessageSensitivity enum
        us_ascii_encoding: Whether to use US-ASCII for Subject,
            Attachments Names and Display Names, default: False
        non_us_ascii_quotes: Whether to use put quotes around non US-ASCII
            Display Names. Enable for Microsoft Outlook 98 and
            Microsoft Outlook 2000 email client only, default: False
        embed_html_attachments: Whether to embed HTML Attachments,
            default: False
        embed_all_attachments: Whether to embed All Attachments, default: False
        embed_adobe_flash_content: Whether to embed
            Adobe Flash Content, default: False
        html_table_position_only: Whether to use only table to position
            elements in HTML (Enabled for Microsoft Outlook 2007),
            default: False
        css_inline_style: Whether to use inline style CSS, default: False
    """

    _FROM_DICT_MAP = {
        "plain_text_html_body_encoding": EmailEncoding,
        "text_attachment_encoding": EmailEncoding,
        "binary_attachment_encoding": EmailEncoding,
        "message_sensitivity": EmailMessageSensitivity
    }

    def __init__(
        self,
        plain_text_html_body_encoding: Union[EmailEncoding, str],
        text_attachment_encoding: Union[EmailEncoding, str],
        binary_attachment_encoding: Union[EmailEncoding, str],
        message_sensitivity: Union[EmailMessageSensitivity, str],
        us_ascii_encoding: bool = False,
        non_us_ascii_quotes: bool = False,
        embed_html_attachments: bool = False,
        embed_all_attachments: bool = False,
        embed_adobe_flash_content: bool = False,
        html_table_position_only: bool = False,
        css_inline_style: bool = False
    ):
        self.plain_text_html_body_encoding = EmailEncoding(
            plain_text_html_body_encoding
        ) if isinstance(plain_text_html_body_encoding, str) else plain_text_html_body_encoding
        self.text_attachment_encoding = EmailEncoding(text_attachment_encoding) if isinstance(
            text_attachment_encoding, str
        ) else text_attachment_encoding
        self.binary_attachment_encoding = EmailEncoding(binary_attachment_encoding) if isinstance(
            binary_attachment_encoding, str
        ) else binary_attachment_encoding
        self.message_sensitivity = EmailMessageSensitivity(message_sensitivity) if isinstance(
            message_sensitivity, str
        ) else message_sensitivity
        self.us_ascii_encoding = us_ascii_encoding
        self.non_us_ascii_quotes = non_us_ascii_quotes
        self.embed_html_attachments = embed_html_attachments
        self.embed_all_attachments = embed_all_attachments
        self.embed_adobe_flash_content = embed_adobe_flash_content
        self.html_table_position_only = html_table_position_only
        self.css_inline_style = css_inline_style


class EmailSmartHostSettings(Dictable):
    """Smart host settings

    Attributes:
        server: Server Name or IP Address
        port: Port number, default: 25
        always_use_smart_host: Whether to always use smart host, default: 25
        smart_host_username: Smart Host Username
        smart_host_password: Smart Host Password
    """

    def __init__(
        self,
        server: Optional[str] = None,
        port: Optional[int] = None,
        always_use_smart_host: bool = False,
        smart_host_username: Optional[str] = None,
        smart_host_password: bool = False
    ):
        self.server = server
        self.port = port
        self.always_use_smart_host = always_use_smart_host
        self.smart_host_username = smart_host_username
        self.smart_host_password = smart_host_password


class EmailDeviceProperties(Dictable):
    """Device properties for email device type.

    Attributes:
        format: indicates the email format of the email device, EmailFormat enum
        mime_settings: MIME settings for MIME email format
        smart_host_settings: smart host settings
    """

    _FROM_DICT_MAP = {
        "format": EmailFormat,
        "mime_settings": EmailMimeSettings.from_dict,
        "smart_host_settings": EmailSmartHostSettings.from_dict
    }

    def __init__(
        self,
        format: Union[str, EmailFormat],
        mime_settings: Optional[Union[dict, EmailMimeSettings]] = None,
        smart_host_settings: Optional[Union[dict, EmailSmartHostSettings]] = None
    ):
        self.format = EmailFormat(format) if isinstance(format, str) else format
        self.mime_settings = EmailMimeSettings.from_dict(mime_settings) if isinstance(
            mime_settings, dict
        ) else mime_settings
        self.smart_host_settings = EmailSmartHostSettings.from_dict(
            smart_host_settings
        ) if isinstance(smart_host_settings, dict) else smart_host_settings


class FtpServerSettings(Dictable):
    """FTP Server Settings

    Attributes:
        protocol: FTP Protocol, FtpProtocol enum
        host: FTP Host IP Address
        port: Port number
        path: FTP Path
        passive_mode: Whether to use Passive Mode for connection, default: True
        max_connections: Maximum connection, default: -1
        ascii_mode: Whether to use ASCII Mode File Type for connection,
            default: True
        user_name: FTP Account Username
        password: FTP Account Password
    """

    _FROM_DICT_MAP = {
        "protocol": FtpProtocol,
    }

    def __init__(
        self,
        protocol: Union[FtpProtocol, str],
        port: int,
        path: str,
        host: Optional[str] = None,
        passive_mode: bool = True,
        max_connections: int = -1,
        ascii_mode: bool = True,
        user_name: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.protocol = FtpProtocol(protocol) if isinstance(protocol, str) else protocol
        self.host = host
        self.port = port
        self.path = path
        self.passive_mode = passive_mode
        self.max_connections = max_connections
        self.ascii_mode = ascii_mode
        self.user_name = user_name
        self.password = password


class FtpDeviceProperties(Dictable):
    """Device properties for ftp device type.

    Attributes:
        server_settings: FTP Server Settings, FtpServerSettings class
        file_system: File System Options, FileSystem class
    """

    _FROM_DICT_MAP = {
        "server_settings": FtpServerSettings.from_dict,
        "file_system": FileSystem.from_dict,
    }

    def __init__(
        self,
        server_settings: Union[FtpServerSettings, dict],
        file_system: Union[FileSystem, dict]
    ):
        self.server_settings = FtpServerSettings.from_dict(server_settings) if isinstance(
            server_settings, dict
        ) else server_settings
        self.file_system = FileSystem.from_dict(file_system) if isinstance(
            file_system, dict
        ) else file_system


class IOSDeviceProperties(Dictable):
    """Device properties for ipad and iphone device types.

    Attributes:
        app_id: Application ID
        server: Push notification server name, default: 'gateway.push.apple.com'
        port: Port number, default: 2195
        provider_certificate: Provider Certificate file location on server
        feedback_service_server: Feedback Service server name,
            default: 'feedback.push.apple.com'
        feedback_service_port: Feedback Service Port number, default: 2195
    """

    def __init__(
        self,
        app_id: str = '',
        server: Optional[str] = None,
        port: Optional[int] = None,
        provider_certificate: Optional[str] = None,
        feedback_service_server: Optional[str] = None,
        feedback_service_port: Optional[int] = None
    ):
        self.app_id = app_id
        self.server = server
        self.port = port
        self.provider_certificate = provider_certificate
        self.feedback_service_server = feedback_service_server
        self.feedback_service_port = feedback_service_port


class AndroidDeviceProperties(Dictable):
    """Device properties for android device type.

    Attributes:
        package_name: Mobile Application Package name
        server: Firebase cloud messaging service server name/IP address
        port: Firebase cloud messaging service Port number, default: 0
        auth_key: Firebase cloud messaging service Authentication Key
        collapse_key: Firebase cloud messaging service Collapse Key
        delay_with_idle: Whether to use Delay with idle
        notification_active_hours: Notification active for hours, 1 to 99999
        use_proxy: Whether to use Proxy for Firebase cloud messaging
        proxy_server: Firebase cloud messaging proxy service server
            name/IP address
        proxy_port: Firebase cloud messaging proxy service Port number
    """

    def __init__(
        self,
        package_name: str,
        server: Optional[str] = None,
        port: Optional[int] = None,
        auth_key: Optional[str] = None,
        collapse_key: Optional[str] = None,
        delay_with_idle: bool = False,
        notification_active_hours: Optional[int] = None,
        use_proxy: bool = False,
        proxy_server: Optional[str] = None,
        proxy_port: Optional[int] = None
    ):
        self.package_name = package_name
        self.server = server
        self.port = port
        self.auth_key = auth_key
        self.collapse_key = collapse_key
        self.delay_with_idle = delay_with_idle
        self.notification_active_hours = notification_active_hours
        self.use_proxy = use_proxy
        self.proxy_server = proxy_server
        self.proxy_port = proxy_port


class FileLocation(Dictable):
    """File Location Setting

    Attributes:
        file_path: File Location
        append_user_path: Whether to allow and append user entered path,
            default: False
        use_backup_location: Whether to use backup location, default: False
        backup_file_path: Backup File Location
    """

    def __init__(
        self,
        file_path: str,
        append_user_path: bool = False,
        use_backup_location: bool = False,
        backup_file_path: Optional[str] = None
    ):
        self.file_path = file_path
        self.append_user_path = append_user_path
        self.use_backup_location = use_backup_location
        self.backup_file_path = backup_file_path


class FileProperties(Dictable):
    """File related properties

    Attributes:
        read_only: Whether to enable read only access for file, default: True
        archive: Whether to archive the file, default: False
        index: Whether to index the file, default: False
        file_encoding: File Encoding, FileEncoding enum
        unix_access_rights: UNIX access rights
    """

    _FROM_DICT_MAP = {
        "file_encoding": FileEncoding,
    }

    def __init__(
        self,
        read_only: bool = True,
        archive: bool = False,
        index: bool = False,
        file_encoding: Optional[Union[FileEncoding, str]] = None,
        unix_access_rights: Optional[str] = None
    ):
        self.read_only = read_only
        self.archive = archive
        self.index = index
        self.file_encoding = FileEncoding(file_encoding
                                          ) if isinstance(file_encoding, str) else file_encoding
        self.unix_access_rights = unix_access_rights


class UnixWindowsSharity(Dictable):
    """Unix to Windows Sharity settings

    Attributes:
        sharity_enabled: Whether to enable delivery from Intelligence
            Server running on UNIX to Windows, default: False
        server_username: IServer Username used for Sharity
        server_password: IServer Password used for Sharity
        server_mount_root: IServer Mount root folder path for Sharity
    """

    def __init__(
        self,
        sharity_enabled: bool = False,
        server_username: Optional[str] = None,
        server_password: Optional[str] = None,
        server_mount_root: Optional[str] = None
    ):
        self.sharity_enabled = sharity_enabled
        self.server_username = server_username
        self.server_password = server_password
        self.server_mount_root = server_mount_root


class FileDeviceProperties(Dictable):
    """Device properties for file device type.

    Attributes:
        file_location: File Location Setting, FileLocation class
        file_system: File System Options, FileSystem class
        connection_parameters: Connection Parameters,
            ConnectionParameters class
        file_properties: File related properties, FileProperties class
        unix_windows_sharity: Unix to Windows Sharity settings,
            UnixWindowsSharity class
    """

    _FROM_DICT_MAP = {
        "file_location": FileLocation.from_dict,
        "file_system": FileSystem.from_dict,
        "connection_parameters": ConnectionParameters.from_dict,
        "file_properties": FileProperties.from_dict,
        "unix_windows_sharity": UnixWindowsSharity.from_dict,
    }

    def __init__(
        self,
        file_location: Union[FileLocation, dict],
        file_system: Union[FileSystem, dict],
        connection_parameters: Union[ConnectionParameters, dict],
        file_properties: Union[FileProperties, dict],
        unix_windows_sharity: Union[UnixWindowsSharity, dict]
    ):
        self.file_location = FileLocation.from_dict(file_location) if isinstance(
            file_location, dict
        ) else file_location
        self.file_system = FileSystem.from_dict(file_system) if isinstance(
            file_system, dict
        ) else file_system
        self.connection_parameters = ConnectionParameters.from_dict(
            connection_parameters
        ) if isinstance(connection_parameters, dict) else connection_parameters
        self.file_properties = FileProperties.from_dict(file_properties) if isinstance(
            file_properties, dict
        ) else file_properties
        self.unix_windows_sharity = UnixWindowsSharity.from_dict(
            unix_windows_sharity
        ) if isinstance(unix_windows_sharity, dict) else unix_windows_sharity


class PrinterLocation(Dictable):
    """Printer Location.

    Attributes:
        location: Printer Location
        user_defined_location: Whether to allow user defined location,
            default: False
    """

    def __init__(self, location: Optional[str] = None, user_defined_location: bool = False):
        self.location = location
        self.user_defined_location = user_defined_location


class PrinterPdfSettings(Dictable):
    """PDF printing settings.

    Attributes:
        post_script_level: Post Script Level, 0 to 9
        odd_even_pages: Indicates the odd or even printing of pages,
            PdfOddEvenPages enum
        reverse_pages: Whether to use reverse pages, default: False
        application_priority: Indicates the which application should get the
            priority when another application is using Adobe and IServer is
            trying to print PDF documents, PdfApplicationPriority enum
    """

    _FROM_DICT_MAP = {
        "odd_even_pages": PdfOddEvenPages,
        "application_priority": PdfApplicationPriority,
    }

    def __init__(
        self,
        post_script_level: int = 2,
        reverse_pages: bool = False,
        odd_even_pages: Optional[Union[PdfOddEvenPages, str]] = None,
        application_priority: Optional[Union[PdfApplicationPriority, str]] = None
    ):
        self.post_script_level = (
            post_script_level if 0 <= post_script_level <= 9 else exception_handler(
                'Please provide appropriate value for post_script_level (from 0 to 9)', ValueError
            )
        )
        self.odd_even_pages = PdfOddEvenPages(odd_even_pages) if isinstance(
            odd_even_pages, str
        ) else odd_even_pages
        self.reverse_pages = reverse_pages
        self.application_priority = PdfApplicationPriority(application_priority) if isinstance(
            application_priority, str
        ) else application_priority


class PrinterProperties(Dictable):
    """Printer Properties.

    Attributes:
        pdf_setting: PDF printing settings, PrinterPdfSettings class
        quality: Print Quality
        scale: Scale in %, default: 100
        paper_source: Paper Source, PrinterPaperSource class
        paper_size: Paper Size, PrinterPaperSize class
    """

    _FROM_DICT_MAP = {
        "pdf_setting": PrinterPdfSettings.from_dict,
        "paper_source": PrinterPaperSource,
        "paper_size": PrinterPaperSize,
    }

    def __init__(
        self,
        pdf_setting: Union[PrinterPdfSettings, dict],
        quality: Optional[str] = None,
        scale: int = 100,
        paper_source: Optional[Union[PrinterPaperSource, str]] = None,
        paper_size: Optional[Union[PrinterPaperSize, str]] = None
    ):
        self.pdf_setting = PrinterPdfSettings.from_dict(pdf_setting) if isinstance(
            pdf_setting, dict
        ) else pdf_setting
        self.quality = quality
        self.scale = scale
        self.paper_source = PrinterPaperSource(paper_source) if isinstance(
            paper_source, str
        ) else paper_source
        self.paper_size = PrinterPaperSize(paper_size
                                           ) if isinstance(paper_size, str) else paper_size


class BackupPrinterProperties(Dictable):
    """Printer Backup Setting.

    Attributes:
        print_on_backup: Whether to print on Backup printer if
            primary printer fails, default: False
        backup_location_type: Backup device type,
            PrinterBackupLocationType class
        backup_printer_location: Backup Printer Location
        backup_file_location: Backup File Location
    """

    _FROM_DICT_MAP = {
        "backup_location_type": PrinterBackupLocationType,
    }

    def __init__(
        self,
        print_on_backup: bool = False,
        backup_location_type: Optional[Union[PrinterBackupLocationType, str]] = None,
        backup_printer_location: Optional[str] = None,
        backup_file_location: Optional[str] = None
    ):
        self.print_on_backup = print_on_backup
        self.backup_location_type = PrinterBackupLocationType(backup_location_type) if isinstance(
            backup_file_location, str
        ) else backup_location_type
        self.backup_printer_location = backup_printer_location
        self.backup_file_location = backup_file_location


class PrinterDeviceProperties(Dictable):
    """Device properties for printer device type.

    Attributes:
        printer_location: Printer Location, PrinterLocation class
        printer_properties: Printer Properties, PrinterProperties class
        connection_parameters: Connection Parameters, ConnectionParameters class
        backup_printer_properties: Printer Backup Setting,
            BackupPrinterProperties class
        temp_file_location: Temp File Location during print execution
    """

    _FROM_DICT_MAP = {
        "printer_location": PrinterLocation.from_dict,
        "printer_properties": PrinterProperties.from_dict,
        "connection_parameters": ConnectionParameters.from_dict,
        "backup_printer_properties": BackupPrinterProperties.from_dict,
    }

    def __init__(
        self,
        printer_location: Union[PrinterLocation, dict],
        printer_properties: Union[PrinterProperties, dict],
        connection_parameters: Union[ConnectionParameters, dict],
        backup_printer_properties: Union[BackupPrinterProperties, dict],
        temp_file_location: Optional[str] = None
    ):
        self.printer_location = PrinterLocation.from_dict(printer_location) if isinstance(
            printer_location, dict
        ) else printer_location
        self.printer_properties = PrinterProperties.from_dict(printer_properties) if isinstance(
            printer_properties, dict
        ) else printer_properties
        self.connection_parameters = ConnectionParameters.from_dict(
            connection_parameters
        ) if isinstance(connection_parameters, dict) else connection_parameters
        self.backup_printer_properties = BackupPrinterProperties.from_dict(
            backup_printer_properties
        ) if isinstance(backup_printer_properties, dict) else backup_printer_properties
        self.temp_file_location = temp_file_location
