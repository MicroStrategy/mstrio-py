import logging
from dataclasses import dataclass

from mstrio import config
from mstrio.api import applications
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.project_objects.palette import Palette
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.helper import Dictable, delete_none_values, find_object_with_name
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler('11.3.1200')
def list_applications(
    connection: Connection,
    to_dictionary: bool = False,
    limit: int | None = None,
    name: str | None = None,
) -> list['Application'] | list[dict]:
    """Get list of available Applications.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        to_dictionary (bool, optional): if True, return Applications as a
            list of dicts
        limit (int, optional): Limit the number of elements returned
        name (str, optional):  filter for applications with names containing
            this value

    Returns:
        List of Application objects or list of dictionaries containing
        application properties.
    """
    response = (
        applications.get_applications(connection=connection).json().get('applications')
    )
    if name:
        response = [app for app in response if name in app.get('name')]
    if limit:
        response = response[:limit]
    if to_dictionary:
        return response
    else:
        return [
            Application.from_dict(source=obj, connection=connection) for obj in response
        ]


@class_version_handler('11.3.1200')
class Application(Entity, CopyMixin, DeleteMixin):
    """Python representation of a Strategy One Application object"""

    @dataclass
    class GeneralSettings(Dictable):
        """General settings of the application.

        Attributes:
            disable_advanced_settings (bool): if True, hides advanced settings
                menu item
            disable_preferences (bool): if True, hides preferences menu item
            network_timeout (int): network timeout time in seconds
            cache_clear_mode (int): cache clear mode
                Possible values:
                    1: automatic
                    2: on close
            clear_cache_on_logout (bool): if True, clears cache on logout
            max_log_size (int): maximum log size
            log_level (int): log level
                Possible values:
                    0: all
                    10: info
                    12: warning
                    14: severe
                    16: off
            update_interval (int): update interval in minutes
        """

        disable_advanced_settings: bool | None = None
        disable_preferences: bool | None = None
        network_timeout: int | None = None
        cache_clear_mode: int | None = None
        clear_cache_on_logout: bool | None = None
        max_log_size: int | None = None
        log_level: int | None = None
        update_interval: int | None = None

    @dataclass
    class HomeSettings(Dictable):
        """Home Screen settings of the application.

        Attributes:
            mode (str): home screen mode
                Possible values:
                    -0: use Library (default)
                    -1: use Dashboard/Document
                    -2: use Agent
            home_document (HomeDocument): home document settings
            home_library (HomeLibrary): home library settings
            theme (Theme): theme settings
        """

        @dataclass
        class HomeDocument(Dictable):
            """Home Screen as Document settings of the application.

            Attributes:
                url (str): URL of the document
                home_document_type (str): home document type
                    Possible values:
                        -dashboard
                        -document
                icons (list[str]): list of icons to be shown on the home screen
                    toolbar
                    Possible values:
                        -comments
                        -notifications
                        -options
                        -table_of_contents
                        -bookmarks
                        -reset
                        -filters
                        -share
                        -data_search
                        -hyper_intelligence
                        -font_size
                toolbar_mode (str): toolbar mode
                    Possible values:
                        -0: show toolbar (default)
                        -1: toolbar will be collapsed by default and expanded
                            by tapping the top right corner icon
                toolbar_enabled (bool): whether the toolbar is enabled
            """

            url: str | None = None
            home_document_type: str | None = None
            icons: list[str] | None = None
            toolbar_mode: str | None = None
            toolbar_enabled: bool | None = None

        @dataclass
        class HomeLibrary(Dictable):
            """Home Screen as Library settings of the application.

            Attributes:
                content_bundle_ids (list[str]): list of content bundle IDs that
                    the application is limited to
                show_all_contents (bool): whether to show all library contents
                    if the content groups are specified in the application
                icons (list[str]): list of icons to be shown on the home screen
                    toolbar
                    Possible values:
                        -comments
                        -notifications
                        -options
                        -table_of_contents
                        -bookmarks
                        -reset
                        -filters
                        -share
                        -data_search
                        -hyper_intelligence
                        -font_size
                customized_items (CustomizedItems): customized settings
                customized_item_properties (dict): extra properties of the items
                    that were customized
                toolbar_mode (str): toolbar mode
                    Possible values:
                        -0: show toolbar (default)
                        -1: toolbar will be collapsed by default and expanded
                            by tapping the top right corner icon
                sidebars (list[str]): menus to be shown in the library sidebar
                    Possible values:
                        -all
                        -favorites
                        -recents
                        -default_groups
                        -my_groups
                        -options
                toolbar_enabled (bool): whether the toolbar is enabled
                default_groups_name (str): customized name for default groups
            """

            @dataclass
            class CustomizedItems(Dictable):
                """Customized items settings of the application."""

                def __init__(
                    self,
                    my_content: bool | None = None,
                    subscriptions: bool | None = None,
                    new_dashboard: bool | None = None,
                    edit_dashboard: bool | None = None,
                    add_library_server: bool | None = None,
                    data_search: bool | None = None,
                    hyper_intelligence: bool | None = None,
                    font_size: bool | None = None,
                    undo_and_redo: bool | None = None,
                    insights: bool | None = None,
                    content_discovery: bool | None = None,
                    mobile_account_panel_user_name: bool | None = None,
                    mobile_account_panel_preferences_my_language: bool | None = None,
                    mobile_account_panel_preferences_my_time_zone: bool | None = None,
                    mobile_account_panel_preferences_face_id_login: bool | None = None,
                    mobile_account_panel_preferences_take_a_tour: bool | None = None,
                    mobile_account_panel_preferences_refresh_view_automatically: (
                        bool | None
                    ) = None,
                    mobile_account_panel_preferences_smart_download: bool | None = None,
                    mobile_account_panel_preferences_automatically_add_to_library: (
                        bool | None
                    ) = None,
                    mobile_account_panel_advanced_settings_app_settings: (
                        bool | None
                    ) = None,
                    mobile_account_panel_advanced_settings_security_settings: (
                        bool | None
                    ) = None,
                    mobile_account_panel_advanced_settings_logging: bool | None = None,
                    mobile_account_panel_help_and_legal: bool | None = None,
                    mobile_account_panel_help_and_legal_help: bool | None = None,
                    mobile_account_panel_help_and_legal_legal: bool | None = None,
                    mobile_account_panel_help_and_legal_report_a_problem: (
                        bool | None
                    ) = None,
                    mobile_account_panel_log_out: bool | None = None,
                    filter_summary: bool | None = None,
                    share_panel_share: bool | None = None,
                    share_panel_export_to_excel: bool | None = None,
                    share_panel_export_to_pdf: bool | None = None,
                    share_panel_download: bool | None = None,
                    share_panel_subscribe: bool | None = None,
                    share_panel_annotate_and_share: bool | None = None,
                    web_account_panel_user_name: bool | None = None,
                    web_account_panel_my_library: bool | None = None,
                    web_account_panel_manage_library: bool | None = None,
                    web_account_panel_preference: bool | None = None,
                    web_account_panel_preference_my_language: bool | None = None,
                    web_account_panel_preference_my_time_zone: bool | None = None,
                    web_account_panel_switch_workspace: bool | None = None,
                    web_account_panel_take_a_tour: bool | None = None,
                    web_account_panel_help: bool | None = None,
                    web_account_panel_log_out: bool | None = None,
                    mobile_downloads: bool | None = None,
                    table_of_contents_header: bool | None = None,
                    table_of_contents_content_info: bool | None = None,
                    table_of_contents_chapter_and_page: bool | None = None,
                    switch_library_server: bool | None = None,
                    create_new_content_dashboard: bool | None = None,
                    create_new_content_report: bool | None = None,
                    layout_tile_view: bool | None = None,
                    layout_list_view: bool | None = None,
                    ai_assistant: bool | None = None,
                    share_panel_manage_access: bool | None = None,
                    bot_window_share_panel: bool | None = None,
                    bot_window_share_panel_share_bot: bool | None = None,
                    bot_window_share_panel_embed_bot: bool | None = None,
                    bot_window_share_panel_manage_access: bool | None = None,
                    bot_window_edit_bot: bool | None = None,
                    create_new_content_bot: bool | None = None,
                    dashboard_view_mode: bool | None = None,
                    content_info_content_creator: bool | None = None,
                    content_info_timestamp: bool | None = None,
                    content_info_description: bool | None = None,
                    content_info_project: bool | None = None,
                    content_info_path: bool | None = None,
                    content_info_object_id: bool | None = None,
                    content_info_info_window: bool | None = None,
                    control_filter_summary: bool | None = None,
                    hide_filter_summary: bool | None = None,
                    sidebars_unpin: bool | None = None,
                    table_of_contents_unpin: bool | None = None,
                    filter_panel_unpin: bool | None = None,
                    comments_panel_unpin: bool | None = None,
                    ai_assistant_unpin: bool | None = None,
                    table_of_contents_allow_close: bool | None = None,
                    filter_panel_allow_close: bool | None = None,
                    comments_panel_allow_close: bool | None = None,
                    ai_assistant_allow_close: bool | None = None,
                    use_application_name_as_library_title: bool | None = None,
                    **kwargs,
                ):
                    self.my_content = my_content
                    self.subscriptions = subscriptions
                    self.new_dossier = new_dashboard
                    self.edit_dossier = edit_dashboard
                    self.add_library_server = add_library_server
                    self.data_search = data_search
                    self.hyper_intelligence = hyper_intelligence
                    self.font_size = font_size
                    self.undo_and_redo = undo_and_redo
                    self.insights = insights
                    self.content_discovery = content_discovery
                    self.mobile_account_panel_user_name = mobile_account_panel_user_name
                    self.mobile_account_panel_preferences_my_language = (
                        mobile_account_panel_preferences_my_language
                    )
                    self.mobile_account_panel_preferences_my_time_zone = (
                        mobile_account_panel_preferences_my_time_zone
                    )
                    self.mobile_account_panel_preferences_face_id_login = (
                        mobile_account_panel_preferences_face_id_login
                    )
                    self.mobile_account_panel_preferences_take_a_tour = (
                        mobile_account_panel_preferences_take_a_tour
                    )
                    self.mobile_account_panel_preferences_refresh_view_automatically = (
                        mobile_account_panel_preferences_refresh_view_automatically
                    )
                    self.mobile_account_panel_preferences_smart_download = (
                        mobile_account_panel_preferences_smart_download
                    )
                    self.mobile_account_panel_preferences_automatically_add_to_library = (  # noqa: E501
                        mobile_account_panel_preferences_automatically_add_to_library
                    )
                    self.mobile_account_panel_advanced_settings_app_settings = (
                        mobile_account_panel_advanced_settings_app_settings
                    )
                    self.mobile_account_panel_advanced_settings_security_settings = (
                        mobile_account_panel_advanced_settings_security_settings
                    )
                    self.mobile_account_panel_advanced_settings_logging = (
                        mobile_account_panel_advanced_settings_logging
                    )
                    self.mobile_account_panel_help_and_legal = (
                        mobile_account_panel_help_and_legal
                    )
                    self.mobile_account_panel_help_and_legal_help = (
                        mobile_account_panel_help_and_legal_help
                    )
                    self.mobile_account_panel_help_and_legal_legal = (
                        mobile_account_panel_help_and_legal_legal
                    )
                    self.mobile_account_panel_help_and_legal_report_a_problem = (
                        mobile_account_panel_help_and_legal_report_a_problem
                    )
                    self.mobile_account_panel_log_out = mobile_account_panel_log_out
                    self.filter_summary = filter_summary
                    self.share_panel_share = share_panel_share
                    self.share_panel_export_to_excel = share_panel_export_to_excel
                    self.share_panel_export_to_pdf = share_panel_export_to_pdf
                    self.share_panel_download = share_panel_download
                    self.share_panel_subscribe = share_panel_subscribe
                    self.share_panel_annotate_and_share = share_panel_annotate_and_share
                    self.web_account_panel_user_name = web_account_panel_user_name
                    self.web_account_panel_my_library = web_account_panel_my_library
                    self.web_account_panel_manage_library = (
                        web_account_panel_manage_library
                    )
                    self.web_account_panel_preference = web_account_panel_preference
                    self.web_account_panel_preference_my_language = (
                        web_account_panel_preference_my_language
                    )
                    self.web_account_panel_preference_my_time_zone = (
                        web_account_panel_preference_my_time_zone
                    )
                    self.web_account_panel_switch_workspace = (
                        web_account_panel_switch_workspace
                    )
                    self.web_account_panel_take_a_tour = web_account_panel_take_a_tour
                    self.web_account_panel_help = web_account_panel_help
                    self.web_account_panel_log_out = web_account_panel_log_out
                    self.mobile_downloads = mobile_downloads
                    self.table_of_contents_header = table_of_contents_header
                    self.table_of_contents_content_info = table_of_contents_content_info
                    self.table_of_contents_chapter_and_page = (
                        table_of_contents_chapter_and_page
                    )
                    self.switch_library_server = switch_library_server
                    self.create_new_content_dossier = create_new_content_dashboard
                    self.create_new_content_report = create_new_content_report
                    self.layout_tile_view = layout_tile_view
                    self.layout_list_view = layout_list_view
                    self.ai_assistant = ai_assistant
                    self.share_panel_manage_access = share_panel_manage_access
                    self.bot_window_share_panel = bot_window_share_panel
                    self.bot_window_share_panel_share_bot = (
                        bot_window_share_panel_share_bot
                    )
                    self.bot_window_share_panel_embed_bot = (
                        bot_window_share_panel_embed_bot
                    )
                    self.bot_window_share_panel_manage_access = (
                        bot_window_share_panel_manage_access
                    )
                    self.bot_window_edit_bot = bot_window_edit_bot
                    self.create_new_content_bot = create_new_content_bot
                    self.dashboard_view_mode = dashboard_view_mode
                    self.content_info_content_creator = content_info_content_creator
                    self.content_info_timestamp = content_info_timestamp
                    self.content_info_description = content_info_description
                    self.content_info_project = content_info_project
                    self.content_info_path = content_info_path
                    self.content_info_object_id = content_info_object_id
                    self.content_info_info_window = content_info_info_window
                    self.control_filter_summary = control_filter_summary
                    self.hide_filter_summary = hide_filter_summary
                    self.sidebars_unpin = sidebars_unpin
                    self.table_of_contents_unpin = table_of_contents_unpin
                    self.filter_panel_unpin = filter_panel_unpin
                    self.comments_panel_unpin = comments_panel_unpin
                    self.ai_assistant_unpin = ai_assistant_unpin
                    self.table_of_contents_allow_close = table_of_contents_allow_close
                    self.filter_panel_allow_close = filter_panel_allow_close
                    self.comments_panel_allow_close = comments_panel_allow_close
                    self.ai_assistant_allow_close = ai_assistant_allow_close
                    self.use_application_name_as_library_title = (
                        use_application_name_as_library_title
                    )

                    possible_new_args = [
                        'new_dossier',
                        'edit_dossier',
                        'create_new_content_dossier',
                    ]
                    if kwargs and not all(
                        key in possible_new_args for key in kwargs.keys()
                    ):
                        raise KeyError(
                            f"Invalid kwargs keys: {list(kwargs.keys())} "
                            f"provided to '{self.__class__.__name__}' class. "
                            f"Possible kwargs keys: {possible_new_args}"
                        )

                    if new_dossier := kwargs.get('new_dossier'):
                        Application._check_replaced_properties(
                            new_dashboard, new_dossier, 'new_dashboard', 'new_dossier'
                        )
                        self.new_dossier = new_dossier

                    if edit_dossier := kwargs.get('edit_dossier'):
                        Application._check_replaced_properties(
                            edit_dashboard,
                            edit_dossier,
                            'edit_dashboard',
                            'edit_dossier',
                        )
                        self.edit_dossier = edit_dossier

                    if create_new_content_dossier := kwargs.get(
                        'create_new_content_dossier'
                    ):
                        Application._check_replaced_properties(
                            create_new_content_dashboard,
                            create_new_content_dossier,
                            'create_new_content_dashboard',
                            'create_new_content_dossier',
                        )
                        self.create_new_content_dossier = create_new_content_dossier

            _FROM_DICT_MAP = {
                'customized_items': CustomizedItems.from_dict,
            }

            content_bundle_ids: list[str] | None = None
            show_all_contents: bool | None = None
            icons: list[str] | None = None
            customized_items: CustomizedItems | None = None
            customized_item_properties: dict | None = None
            toolbar_mode: str | None = None
            sidebars: list[str] | None = None
            toolbar_enabled: bool | None = None
            default_groups_name: str | None = None

        @dataclass
        class Theme(Dictable):
            """Theme settings of the application.

            Attributes:
                logos (Logos): logos settings
                color (Color): color settings
            """

            @dataclass
            class Logos(Dictable):
                """Logos settings of the application.

                Attributes:
                    web (Logo): web logo settings
                    favicon (Logo): favorite icon settings
                    mobile (Logo): mobile logo settings
                """

                @dataclass
                class Logo(Dictable):
                    """Details of a logo.

                    Attributes:
                        type (str): type of the logo
                        value (str): value of the logo
                    """

                    type: str | None = None
                    value: str | None = None

                _FROM_DICT_MAP = {
                    'web': Logo.from_dict,
                    'favicon': Logo.from_dict,
                    'mobile': Logo.from_dict,
                }

                web: Logo | None = None
                favicon: Logo | None = None
                mobile: Logo | None = None

            @dataclass
            class Color(Dictable):
                """Color settings of the application.

                Attributes:
                    selected_theme (str): selected theme
                        Possible values:
                            -useSystemSettings
                            -light
                            -dark
                            -red
                            -green
                            -blue
                            -darkBlue
                            -yellow
                            -custom
                    formatting (Formatting): formatting settings
                    enable_for_bots (bool): whether the theme is enabled for
                        bots
                """

                @dataclass
                class Formatting(Dictable):
                    """Formatting settings of the application.
                    All color values are in hex format.

                    Attributes:
                        toolbar_fill (str): toolbar background color
                        toolbar_color (str): toolbar icon/text color
                        sidebar_fill (str): sidebar background color
                        sidebar_color (str): sidebar text color
                        sidebar_active_fill (str): active sidebar background
                            color
                        sidebar_active_color (str): active sidebar text color
                        panel_fill (str): panel background color
                        panel_color (str): panel text color
                        accent_fill (str): accent fill color
                        notification_badge_fill (str): notification badge color
                        button_color (str): button color
                        canvas_fill (str): canvas background color
                    """

                    toolbar_fill: str | None = None
                    toolbar_color: str | None = None
                    sidebar_fill: str | None = None
                    sidebar_color: str | None = None
                    sidebar_active_fill: str | None = None
                    sidebar_active_color: str | None = None
                    panel_fill: str | None = None
                    panel_color: str | None = None
                    accent_fill: str | None = None
                    notification_badge_fill: str | None = None
                    button_color: str | None = None
                    canvas_fill: str | None = None

                _FROM_DICT_MAP = {
                    'formatting': Formatting.from_dict,
                }

                selected_theme: str | None = None
                formatting: Formatting | None = None
                enable_for_bots: bool | None = None

            _FROM_DICT_MAP = {
                'logos': Logos.from_dict,
                'color': Color.from_dict,
            }

            logos: Logos | None = None
            color: Color | None = None

        _FROM_DICT_MAP = {
            'home_document': HomeDocument.from_dict,
            'home_library': HomeLibrary.from_dict,
            'theme': Theme.from_dict,
        }

        mode: str | None = None
        home_document: HomeDocument | None = None
        home_library: HomeLibrary | None = None
        theme: Theme | None = None

    @dataclass
    class EmailSettings(Dictable):
        """Email settings of the application.

        Attributes:
            enabled (bool): whether to enable custom email settings
            host_portal (str): the host web portal in the button link
            show_branding_image (bool): if True, shows branding image
            show_browser_button (bool): if True, shows browser button
            show_mobile_button (bool): if True, shows mobile button
            show_button_description (bool): if True, shows the email button
                description
            show_reminder (bool): if True, shows reminder section
            show_sent_by (bool): if True, shows sent by section
            sent_by_text (str): text in the sent by section
            show_social_media (bool): if True, shows social media section
            content (Content): content settings
            sender (Sender): sender settings
            branding_image (str): url of the branding image
            button (Button): button settings
            reminder (Reminder): reminder settings
            social_media (SocialMedia): social media settings
        """

        class Content(Dictable):
            """Content settings of the application.

            Attributes:
                share_dashboard (EmailDetails): settings for sharing a dashboard
                share_bookmark (EmailDetails): settings for sharing a dossier
                    with bookmark
                share_bot (EmailDetails): settings for sharing a bot
                member_added (EmailDetails): settings for inviting a recipient
                    to a discussion
                user_mention (EmailDetails): settings for mentioning a recipient
                    in a comment or discussion
            """

            @dataclass
            class EmailDetails(Dictable):
                """Email details settings of the application.

                Attributes:
                    subject (str): email subject
                    body (str): email body
                """

                subject: str | None = None
                body: str | None = None

            _FROM_DICT_MAP = {
                'share_dossier': EmailDetails.from_dict,
                'share_bookmark': EmailDetails.from_dict,
                'share_bot': EmailDetails.from_dict,
                'member_added': EmailDetails.from_dict,
                'user_mention': EmailDetails.from_dict,
            }

            def __init__(
                self,
                share_dashboard: EmailDetails | None = None,
                share_bookmark: EmailDetails | None = None,
                share_bot: EmailDetails | None = None,
                member_added: EmailDetails | None = None,
                user_mention: EmailDetails | None = None,
                **kwargs,
            ):
                self.share_dossier = share_dashboard
                self.share_bookmark = share_bookmark
                self.share_bot = share_bot
                self.member_added = member_added
                self.user_mention = user_mention

                if kwargs and not all(
                    key in ['share_dossier'] for key in kwargs.keys()
                ):
                    raise KeyError(
                        f"Invalid kwargs keys: {list(kwargs.keys())} provided "
                        f"to '{self.__class__.__name__}' class. Possible "
                        f"kwargs keys: ['share_dossier']"
                    )
                if share_dossier := kwargs.get('share_dossier'):
                    Application._check_replaced_properties(
                        share_dashboard,
                        share_dossier,
                        'share_dashboard',
                        'share_dossier',
                    )
                    self.share_dossier = share_dossier

        @dataclass
        class Sender(Dictable):
            """Sender settings of the application.

            Attributes:
                address (str): sender email address
                display_name (str): sender display name
            """

            address: str | None = None
            display_name: str | None = None

        @dataclass
        class Button(Dictable):
            """Button settings of the application.

            Attributes:
                browser_button_style (ButtonStyle): browser button style
                mobile_button_style (ButtonStyle): mobile button style
                mobile_button_link_type (str): mobile button link type
                    Possible values:
                        -default
                        -app_scheme
                        -universal_link
                mobile_button_scheme (str): mobile button scheme
                description (str): button description
            """

            @dataclass
            class ButtonStyle(Dictable):
                """Button style settings of the application.

                Attributes:
                    background_color (str): button background color
                    font_color (str): button text color
                    text (str): button border color
                """

                background_color: str | None = None
                font_color: str | None = None
                text: str | None = None

            _FROM_DICT_MAP = {
                'browser_button_style': ButtonStyle.from_dict,
                'mobile_button_style': ButtonStyle.from_dict,
            }

            browser_button_style: ButtonStyle | None = None
            mobile_button_style: ButtonStyle | None = None
            mobile_button_link_type: str | None = None
            mobile_button_scheme: str | None = None
            description: str | None = None

        @dataclass
        class Reminder(Dictable):
            """Reminder settings of the application.

            Attributes:
                text (str): reminder text
                link_text (str): reminder link text
            """

            text: str | None = None
            link_text: str | None = None

        @dataclass
        class SocialMedia(Dictable):
            """Social media settings of the application.

            Attributes:
                show_facebook (bool): whether to show the Facebook link
                facebook_link (str): Facebook link
                show_twitter (bool): whether to show the Twitter link
                twitter_link (str): Twitter link
                show_linked_in (bool): whether to show the LinkedIn link
                linked_in_link (str): LinkedIn link
                show_youtube (bool): whether to show the YouTube link
                youtube_link (str): YouTube link
            """

            show_facebook: bool | None = None
            facebook_link: str | None = None
            show_twitter: bool | None = None
            twitter_link: str | None = None
            show_linked_in: bool | None = None
            linked_in_link: str | None = None
            show_you_tube: bool | None = None
            you_tube_link: str | None = None

        _FROM_DICT_MAP = {
            'content': Content.from_dict,
            'sender': Sender.from_dict,
            'button': Button.from_dict,
            'reminder': Reminder.from_dict,
            'social_media': SocialMedia.from_dict,
        }

        enabled: bool | None = None
        host_portal: str | None = None
        show_branding_image: bool | None = None
        show_browser_button: bool | None = None
        show_mobile_button: bool | None = None
        show_button_description: bool | None = None
        show_reminder: bool | None = None
        show_sent_by: bool | None = None
        sent_by_text: str | None = None
        show_social_media: bool | None = None
        content: Content | None = None
        sender: Sender | None = None
        branding_image: dict[str, str] | None = None
        button: Button | None = None
        reminder: Reminder | None = None
        social_media: SocialMedia | None = None

    @dataclass
    class AiSettings(Dictable):
        """AI settings of the application.

        Attributes:
            feedback (bool): if True, AI assistance feedback is enabled
            learning (bool): if True, AI assistance learning is enabled
            disclaimer (str): AI assistance disclaimer
        """

        feedback: bool | None = None
        learning: bool | None = None
        disclaimer: str | None = None

    @dataclass
    class AuthModes(Dictable):
        """Authentication modes of the application.

        Attributes:
            available_modes (list[int]): available authentication modes
                Possible values:
                    1: Standard
                    16: LDAP
                    1048576: SAML
                    4194304: OIDC
            default_mode (int): default authentication mode
        """

        available_modes: list[int] | None = None
        default_mode: int | None = None

    @dataclass
    class Environments(Dictable):
        """Environments of the application.

        Attributes:
            current (str): name of the current library environment
            other (list[EnvironmentLink]): list of other environments
        """

        @dataclass
        class EnvironmentLink(Dictable):
            """Environment link settings of the application.

            Attributes:
                name (str): name of the environment
                url (str): URL of the environment
            """

            name: str | None = None
            url: str | None = None

        _FROM_DICT_MAP = {
            'other': [EnvironmentLink.from_dict],
        }

        current: str | None = None
        other: list[EnvironmentLink] | None = None

    _OBJECT_TYPE = ObjectTypes.APPLICATION
    _API_DELETE = staticmethod(applications.delete_application)
    _API_GETTERS = {
        **Entity._API_GETTERS,
        (
            'managed',
            'property_groups',
            'access_granted',
            'general',
            'home_screen',
            'platforms',
            'application_palettes',
            'application_default_palette',
            'show_builtin_palettes',
            'is_default',
            'use_config_palettes',
            'email_settings',
            'ai_settings',
            'auth_modes',
            'environments',
            'application_nuggets',
            'object_names',
            'object_acl',
            'access_granted',
        ): applications.get_application,
    }

    def __init__(
        self, connection: Connection, name: str | None = None, id: str | None = None
    ) -> None:
        """Initialize Application object by passing name or id.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Application
            id (string, optional): ID of Application
        """
        if not id:
            if not name:
                raise ValueError("Please specify either 'name' or 'id'.")
            app = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_applications,
            )
            id = app['id']
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.managed = kwargs.get('managed')
        self.property_groups = kwargs.get('property_groups')
        self.access_granted = kwargs.get('access_granted')
        self._general = kwargs.get('general')
        self._home_screen = kwargs.get('home_screen')
        self.platforms = kwargs.get('platforms')
        self.application_palettes = kwargs.get('application_palettes')
        self.application_default_palette = kwargs.get('application_default_palette')
        self.show_builtin_palettes = kwargs.get('show_builtin_palettes')
        self.is_default = kwargs.get('is_default')
        self.use_config_palettes = kwargs.get('use_config_palettes')
        self._email_settings = kwargs.get('email_settings')
        self._ai_settings = kwargs.get('ai_settings')
        self._auth_modes = kwargs.get('auth_modes')
        self._environments = kwargs.get('environments')
        self.application_nuggets = kwargs.get('application_nuggets')
        self.object_names = kwargs.get('object_names')
        self.object_acl = kwargs.get('object_acl')
        self.access_granted = kwargs.get('access_granted')

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        home_screen: 'Application.HomeSettings',
        description: str | None = None,
        managed: bool | None = None,
        general: 'Application.GeneralSettings | None' = None,
        platforms: list[str] | None = None,
        application_palettes: list[str] | list[Palette] | None = None,
        application_default_palette: str | Palette | None = None,
        show_builtin_palettes: bool | None = None,
        is_default: bool | None = None,
        use_config_palettes: bool | None = None,
        email_settings: 'Application.EmailSettings | None' = None,
        ai_settings: 'Application.AiSettings | None' = None,
        auth_modes: 'Application.AuthModes | None' = None,
        environments: 'Application.Environments | None' = None,
        application_nuggets: list[str] | None = None,
    ) -> 'Application':
        """Create a new application.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            name (str): name of the application
            home_screen (Application.HomeSettings): home screen settings of the
                application
            description (str, optional): description of the application
            managed (bool, optional): whether the application is managed
            general (Application.GeneralSettings, optional): general settings
                of the application
            platforms (list[str], optional): list of platforms for the
                application
                Available values:
                    -web
                    -mobile
                    -desktop
            application_palettes (list[str] or list[Palette], optional): list
                of customized application palettes
            application_default_palette (str or Palette, optional): default
                application palette
            show_builtin_palettes (bool, optional): whether to show built-in
                palettes
            is_default (bool, optional): whether the application configuration
                is default
            use_config_palettes (bool, optional): whether to use default
                configuration of palettes
            email_settings (Application.EmailSettings, optional): email settings
                of the application
            ai_settings (Application.AiSettings, optional): AI settings of the
                application
            auth_modes (Application.AuthModes, optional): authentication modes
                of the application
            environments (Application.Environments, optional): environments of
                the application
            application_nuggets (list[str], optional): list of application
                nuggets

        Returns:
            The created Application object.
        """
        if isinstance(application_default_palette, Palette):
            application_default_palette = application_default_palette.id
        if application_palettes:
            application_palettes = [
                palette.id if isinstance(palette, Palette) else palette
                for palette in application_palettes
            ]
        body = {
            'name': name,
            'description': description,
            'managed': managed,
            'general': general.to_dict() if general else None,
            'homeScreen': home_screen.to_dict(),
            'platforms': platforms,
            'applicationPalettes': application_palettes,
            'applicationDefaultPalette': application_default_palette,
            'showBuiltinPalettes': show_builtin_palettes,
            'isDefault': is_default,
            'useConfigPalettes': use_config_palettes,
            'emailSettings': email_settings.to_dict() if email_settings else None,
            'aiSettings': ai_settings.to_dict() if ai_settings else None,
            'authModes': auth_modes.to_dict() if auth_modes else None,
            'environments': environments.to_dict() if environments else None,
            'applicationNuggets': application_nuggets,
            'objectNames': [],
            'objectAcl': [],
        }
        body['homeScreen']['homeLibrary']['customizedItems'] = (
            (home_screen.home_library.customized_items.to_dict(camel_case=False))
            if home_screen.home_library.customized_items
            else None
        )
        body['homeScreen']['homeLibrary']['customizedItemProperties'] = (
            home_screen.home_library.customized_item_properties
            if home_screen.home_library.customized_item_properties
            else None
        )
        if home_screen.home_document.home_document_type == 'dashboard':
            body['homeScreen']['homeDocument']['homeDocumentType'] = 'dossier'
        if email_settings and email_settings.content:
            body['emailSettings']['content'] = {
                'SHARE_DOSSIER': body['emailSettings']['content']['shareDossier'],
                'SHARE_BOOKMARK': body['emailSettings']['content']['shareBookmark'],
                'SHARE_BOT': body['emailSettings']['content']['shareBot'],
                'MEMBER_ADDED': body['emailSettings']['content']['memberAdded'],
                'USER_MENTION': body['emailSettings']['content']['userMention'],
            }
        body = delete_none_values(
            source=body,
            recursion=True,
            whitelist_attributes=['objectNames', 'objectAcl'],
        )
        try:
            applications.create_application(connection=connection, body=body)
        except IServerError as err:
            if "type 'Palette' does not exist in the metadata" in str(err):
                raise AttributeError(
                    "Application cannot be created: at least one palette parameter "
                    "is either invalid or refers to project-level palette. "
                    "Please select a valid configuration-level palette(s) instead."
                ) from err
            raise err

        if config.verbose:
            logger.info(f'Application "{name}" has been created.')
        # The endpoint returns nothing, so we need to return app manually
        return Application(connection=connection, name=name)

    def alter(
        self,
        home_screen: 'Application.HomeSettings | None' = None,
        name: str | None = None,
        description: str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
        managed: bool | None = None,
        general: 'Application.GeneralSettings | None' = None,
        platforms: list[str] | None = None,
        application_palettes: list[str] | list[Palette] | None = None,
        application_default_palette: str | Palette | None = None,
        show_builtin_palettes: bool | None = None,
        is_default: bool | None = None,
        use_config_palettes: bool | None = None,
        email_settings: 'Application.EmailSettings | None' = None,
        ai_settings: 'Application.AiSettings | None' = None,
        auth_modes: 'Application.AuthModes | None' = None,
        environments: 'Application.Environments | None' = None,
        application_nuggets: list[str] | None = None,
    ) -> None:
        """Alter an application.

        Args:
            home_screen (Application.HomeSettings, optional): home screen
                settings of the application
            name (str, optional): name of the application
            description (str, optional): description of the application
            comments (str, optional): long description of the application
            owner: (str, User, optional): owner of the application object
            managed (bool, optional): whether the application is managed
            general (Application.GeneralSettings, optional): general settings
                of the application
            platforms (list[str], optional): list of platforms for the
                application
                Available values:
                    -web
                    -mobile
                    -desktop
            application_palettes (list[str] or list[Palette], optional): list
                of customized application palettes
            application_default_palette (str or Palette, optional): default
                application palette
            show_builtin_palettes (bool, optional): whether to show built-in
                palettes
            is_default (bool, optional): whether the application configuration
                is default
            use_config_palettes (bool, optional): whether to use default
                configuration of palettes
            email_settings (Application.EmailSettings, optional): email settings
                of the application
            ai_settings (Application.AiSettings, optional): AI settings of the
                application
            auth_modes (Application.AuthModes, optional): authentication modes
                of the application
            environments (Application.Environments, optional): environments of
                the application
            application_nuggets (list[str], optional): list of application
                nuggets
        """
        if not home_screen:
            home_screen = self.home_screen
        if isinstance(application_default_palette, Palette):
            application_default_palette = application_default_palette.id
        if application_palettes:
            application_palettes = [
                palette.id if isinstance(palette, Palette) else palette
                for palette in application_palettes
            ]
        if isinstance(owner, User):
            owner = owner.id
        body = {
            'objectVersion': self.version,
            'name': name or self.name,
            'description': description or self.description,
            'comments': comments or self.comments,
            'ownerId': owner or self.owner['id'],
            'managed': managed or self.managed,
            'general': (
                (general or self.general).to_dict()
                if (general or self.general)
                else None
            ),
            'homeScreen': home_screen.to_dict(),
            'platforms': platforms or self.platforms,
            'applicationPalettes': application_palettes
            or self.application_palettes
            or [],
            'applicationDefaultPalette': application_default_palette
            or self.application_default_palette
            or '',
            'showBuiltinPalettes': show_builtin_palettes or self.show_builtin_palettes,
            'isDefault': is_default or self.is_default,
            'useConfigPalettes': use_config_palettes or self.use_config_palettes,
            'emailSettings': (
                (email_settings or self.email_settings).to_dict()
                if (email_settings or self.email_settings)
                else None
            ),
            'aiSettings': (
                (ai_settings or self.ai_settings).to_dict()
                if (ai_settings or self.ai_settings)
                else None
            ),
            'authModes': (
                (auth_modes or self.auth_modes).to_dict()
                if (auth_modes or self.auth_modes)
                else None
            ),
            'environments': (
                (environments or self.environments).to_dict()
                if (environments or self.environments)
                else None
            ),
            'applicationNuggets': application_nuggets or self.application_nuggets or [],
            'accessGranted': self.access_granted,
            'objectNames': self.object_names or [],
            'objectAcl': self.object_acl or [],
        }
        if home_screen:
            body['homeScreen']['homeLibrary']['customizedItems'] = (
                (home_screen.home_library.customized_items.to_dict(camel_case=False))
                if home_screen.home_library.customized_items
                else None
            )
            body['homeScreen']['homeLibrary']['customizedItemProperties'] = (
                home_screen.home_library.customized_item_properties or None
            )
            if home_screen.home_document.home_document_type == 'dashboard':
                body['homeScreen']['homeDocument']['homeDocumentType'] = 'dossier'
        if body['emailSettings'] is not None and body['emailSettings'].get('content'):
            body['emailSettings']['content'] = {
                'SHARE_DOSSIER': body['emailSettings']['content']['shareDossier'],
                'SHARE_BOOKMARK': body['emailSettings']['content']['shareBookmark'],
                'SHARE_BOT': body['emailSettings']['content']['shareBot'],
                'MEMBER_ADDED': body['emailSettings']['content']['memberAdded'],
                'USER_MENTION': body['emailSettings']['content']['userMention'],
            }
        body = delete_none_values(
            source=body,
            recursion=True,
            whitelist_attributes=[
                'objectNames',
                'objectAcl',
                'applicationNuggets',
                'applicationPalettes',
            ],
        )
        applications.update_application(
            connection=self.connection, id=self.id, body=body
        )
        if config.verbose:
            logger.info(
                'Application has been altered successfully. Your changes are not '
                'saved locally. Refresh the object to see the changes.'
            )

    @staticmethod
    def _check_replaced_properties(
        dashboard_property, dossier_property, dashboard_name, dossier_name
    ):
        if dashboard_property is not None and dashboard_property != dossier_property:
            raise KeyError(
                f"You provided both '{dashboard_name}' and '{dossier_name}' "
                f"with different values. Please use only {dashboard_name}."
            )

    @property
    def general(self) -> GeneralSettings | None:
        """General settings of the application."""
        if not self._general:
            self.fetch('general')
        if self._general:
            return Application.GeneralSettings.from_dict(source=self._general)
        return None

    @property
    def home_screen(self) -> HomeSettings | None:
        """Home Screen settings of the application."""
        if not self._home_screen:
            self.fetch('home_screen')
        if self._home_screen:
            return Application.HomeSettings.from_dict(source=self._home_screen)
        return None

    @property
    def email_settings(self) -> EmailSettings | None:
        """Email settings of the application."""
        if not self._email_settings:
            self.fetch('email_settings')
        if self._email_settings:
            temp = Application.EmailSettings.from_dict(source=self._email_settings)
            content = self._email_settings.get('content')
            # Initialize Content class only if content is not empty.
            # Otherwise, keep it None.
            if content:
                temp.content = Application.EmailSettings.Content(
                    share_dashboard=content.get('SHARE_DOSSIER'),
                    share_bookmark=content.get('SHARE_BOOKMARK'),
                    share_bot=content.get('SHARE_BOT'),
                    member_added=content.get('MEMBER_ADDED'),
                    user_mention=content.get('USER_MENTION'),
                )
            return temp
        return None

    @property
    def ai_settings(self) -> AiSettings | None:
        """AI settings of the application."""
        if not self._ai_settings:
            self.fetch('ai_settings')
        if self._ai_settings:
            return Application.AiSettings.from_dict(source=self._ai_settings)
        return None

    @property
    def auth_modes(self) -> AuthModes | None:
        """Authentication modes of the application."""
        if not self._auth_modes:
            self.fetch('auth_modes')
        if self._auth_modes:
            return Application.AuthModes.from_dict(source=self._auth_modes)
        return None

    @property
    def environments(self) -> Environments | None:
        """Environments of the application."""
        if not self._environments:
            self.fetch('environments')
        if self._environments:
            return Application.Environments.from_dict(source=self._environments)
        return None
