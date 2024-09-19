import logging
from dataclasses import dataclass

from mstrio import config
from mstrio.api import applications
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.helper import Dictable, delete_none_values, find_object_with_name
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler('11.3.1200')
def list_applications(
    connection: Connection,
    to_dictionary: dict = False,
    limit: int | None = None,
    name: str | None = None,
) -> list['Application'] | list[dict]:
    """Get list of available Applications.

    Args:
        connection (Connection): MicroStrategy connection object returned by
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
class Application(Entity, CopyMixin, DeleteMixin, TranslationMixin):
    """Python representation of a MicroStrategy Application object"""

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
                    -1: use Dossier/Document
                    -2: use Bot
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
                        -dossier
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

                my_content: bool | None = None
                subscriptions: bool | None = None
                new_dossier: bool | None = None
                edit_dossier: bool | None = None
                add_library_server: bool | None = None
                data_search: bool | None = None
                hyper_intelligence: bool | None = None
                font_size: bool | None = None
                undo_and_redo: bool | None = None
                insights: bool | None = None
                content_discovery: bool | None = None
                mobile_account_panel_user_name: bool | None = None
                mobile_account_panel_preferences_my_language: bool | None = None
                mobile_account_panel_preferences_my_time_zone: bool | None = None
                mobile_account_panel_preferences_face_id_login: bool | None = None
                mobile_account_panel_preferences_take_a_tour: bool | None = None
                mobile_account_panel_preferences_refresh_view_automatically: (
                    bool | None
                ) = None
                mobile_account_panel_preferences_smart_download: bool | None = None
                mobile_account_panel_preferences_automatically_add_to_library: (
                    bool | None
                ) = None
                mobile_account_panel_advanced_settings_app_settings: bool | None = None
                mobile_account_panel_advanced_settings_security_settings: (
                    bool | None
                ) = None
                mobile_account_panel_advanced_settings_logging: bool | None = None
                mobile_account_panel_help_and_legal: bool | None = None
                mobile_account_panel_help_and_legal_help: bool | None = None
                mobile_account_panel_help_and_legal_legal: bool | None = None
                mobile_account_panel_help_and_legal_report_a_problem: bool | None = None
                mobile_account_panel_log_out: bool | None = None
                filter_summary: bool | None = None
                share_panel_share: bool | None = None
                share_panel_export_to_excel: bool | None = None
                share_panel_export_to_pdf: bool | None = None
                share_panel_download: bool | None = None
                share_panel_subscribe: bool | None = None
                share_panel_annotate_and_share: bool | None = None
                web_account_panel_user_name: bool | None = None
                web_account_panel_my_library: bool | None = None
                web_account_panel_manage_library: bool | None = None
                web_account_panel_preference: bool | None = None
                web_account_panel_preference_my_language: bool | None = None
                web_account_panel_preference_my_time_zone: bool | None = None
                web_account_panel_switch_workspace: bool | None = None
                web_account_panel_take_a_tour: bool | None = None
                web_account_panel_help: bool | None = None
                web_account_panel_log_out: bool | None = None
                mobile_downloads: bool | None = None
                table_of_contents_header: bool | None = None
                table_of_contents_content_info: bool | None = None
                table_of_contents_chapter_and_page: bool | None = None
                switch_library_server: bool | None = None
                create_new_content_dossier: bool | None = None
                create_new_content_report: bool | None = None
                layout_tile_view: bool | None = None
                layout_list_view: bool | None = None
                ai_assistant: bool | None = None
                share_panel_manage_access: bool | None = None
                bot_window_share_panel: bool | None = None
                bot_window_share_panel_share_bot: bool | None = None
                bot_window_share_panel_embed_bot: bool | None = None
                bot_window_share_panel_manage_access: bool | None = None
                bot_window_edit_bot: bool | None = None
                create_new_content_bot: bool | None = None
                dashboard_view_mode: bool | None = None
                content_info_content_creator: bool | None = None
                content_info_timestamp: bool | None = None
                content_info_description: bool | None = None
                content_info_project: bool | None = None
                content_info_path: bool | None = None
                content_info_object_id: bool | None = None
                content_info_info_window: bool | None = None
                control_filter_summary: bool | None = None
                hide_filter_summary: bool | None = None
                sidebars_unpin: bool | None = None
                table_of_contents_unpin: bool | None = None
                filter_panel_unpin: bool | None = None
                comments_panel_unpin: bool | None = None
                ai_assistant_unpin: bool | None = None
                table_of_contents_allow_close: bool | None = None
                filter_panel_allow_close: bool | None = None
                comments_panel_allow_close: bool | None = None
                ai_assistant_allow_close: bool | None = None

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

        @dataclass
        class Content(Dictable):
            """Content settings of the application.

            Attributes:
                share_dossier (EmailDetails): settings for sharing a dossier
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

            share_dossier: EmailDetails | None = None
            share_bookmark: EmailDetails | None = None
            share_bot: EmailDetails | None = None
            member_added: EmailDetails | None = None
            user_mention: EmailDetails | None = None

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
        branding_image: str | None = None
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
            connection (object): MicroStrategy connection object returned
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
        application_palettes: list[str] | None = None,
        application_default_palette: str | None = None,
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
            connection (Connection): MicroStrategy connection object returned by
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
            application_palettes (list[str], optional): list of customized
                application palettes
            application_default_palette (str, optional): default application
                palette
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
        applications.create_application(connection=connection, body=body)
        if config.verbose:
            logger.info(f'Application "{name}" has been created.')
        # The endpoint returns nothing, so we need to return app manually
        return Application(connection=connection, name=name)

    def alter(
        self,
        home_screen: 'Application.HomeSettings | None' = None,
        name: str | None = None,
        description: str | None = None,
        managed: bool | None = None,
        general: 'Application.GeneralSettings | None' = None,
        platforms: list[str] | None = None,
        application_palettes: list[str] | None = None,
        application_default_palette: str | None = None,
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
            managed (bool, optional): whether the application is managed
            general (Application.GeneralSettings, optional): general settings
                of the application
            platforms (list[str], optional): list of platforms for the
                application
                Available values:
                    -web
                    -mobile
                    -desktop
            application_palettes (list[str], optional): list of customized
                application palettes
            application_default_palette (str, optional): default application
                palette
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
        body = {
            'objectVersion': self.version,
            'name': name or self.name,
            'description': description or self.description,
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
            if 'content' in self._email_settings:
                temp.content = Application.EmailSettings.Content(
                    share_dossier=(
                        self._email_settings.get('content').get('SHARE_DOSSIER')
                        if 'SHARE_DOSSIER' in self._email_settings.get('content')
                        else None
                    ),
                    share_bookmark=(
                        self._email_settings.get('content').get('SHARE_BOOKMARK')
                        if 'SHARE_BOOKMARK' in self._email_settings.get('content')
                        else None
                    ),
                    share_bot=(
                        self._email_settings.get('content').get('SHARE_BOT')
                        if 'SHARE_BOT' in self._email_settings.get('content')
                        else None
                    ),
                    member_added=(
                        self._email_settings.get('content').get('MEMBER_ADDED')
                        if 'MEMBER_ADDED' in self._email_settings.get('content')
                        else None
                    ),
                    user_mention=(
                        self._email_settings.get('content').get('USER_MENTION')
                        if 'USER_MENTION' in self._email_settings.get('content')
                        else None
                    ),
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
