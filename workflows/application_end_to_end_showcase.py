"""This is the demo script to show how to manage applications. 
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.applications import Application, list_applications

conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# list applications with different conditions
# Note: No Applications exist in a default environment
list_of_all_apps = list_applications(connection=conn)
list_of_several_apps = list_applications(connection=conn, limit=5)
list_of_apps_name_filtered = list_applications(connection=conn, name='Strategy')
list_of_all_apps_as_dicts = list_applications(connection=conn, to_dictionary=True)
print(list_of_all_apps)

# Create an Application with customized settings for:
# General Settings, Email Settings, AI Settings, and Auth Modes
# For Home Screen both Library and Document settings are customized
# and the custom Theme settings are set
app = Application.create(
    connection=conn,
    name='Application Validation Scripts',
    description='This is a demo application created by the validation script.',
    home_screen=Application.HomeSettings(
        mode=0,
        home_document=Application.HomeSettings.HomeDocument(
            url='app/B7CA92F04B9FAE8D941C3E9B7E0CD754/DA0B39F911E7A94B00000080AF11FAC4',
            home_document_type='document',
            icons=[
                'table_of_contents',
                'bookmarks',
                'share',
                'options',
            ],
            toolbar_mode=1,
            toolbar_enabled=False,
        ),
        home_library=Application.HomeSettings.HomeLibrary(
            content_bundle_ids=[],
            show_all_contents=None,
            icons=[
                'sidebars',
                'sort_and_filter',
                'search',
                'options',
            ],
            customized_items=Application.HomeSettings.HomeLibrary.CustomizedItems(
                my_content=False,
                subscriptions=True,
                new_dossier=True,
                edit_dossier=True,
                add_library_server=False,
                data_search=True,
                hyper_intelligence=False,
                font_size=True,
                undo_and_redo=True,
                insights=True,
                content_discovery=False,
                mobile_account_panel_user_name=True,
                mobile_account_panel_preferences_my_language=True,
                mobile_account_panel_preferences_my_time_zone=True,
                mobile_account_panel_preferences_face_id_login=False,
                mobile_account_panel_preferences_take_a_tour=True,
                mobile_account_panel_preferences_refresh_view_automatically=True,
                mobile_account_panel_preferences_smart_download=False,
                mobile_account_panel_preferences_automatically_add_to_library=True,
                mobile_account_panel_advanced_settings_app_settings=True,
                mobile_account_panel_advanced_settings_security_settings=True,
                mobile_account_panel_advanced_settings_logging=True,
                mobile_account_panel_help_and_legal=True,
                mobile_account_panel_help_and_legal_help=True,
                mobile_account_panel_help_and_legal_legal=False,
                mobile_account_panel_help_and_legal_report_a_problem=True,
                mobile_account_panel_log_out=True,
                filter_summary=False,
                share_panel_share=True,
                share_panel_export_to_excel=False,
                share_panel_export_to_pdf=True,
                share_panel_download=True,
                share_panel_subscribe=True,
                share_panel_annotate_and_share=True,
                web_account_panel_user_name=True,
                web_account_panel_my_library=False,
                web_account_panel_manage_library=True,
                web_account_panel_preference=True,
                web_account_panel_preference_my_language=True,
                web_account_panel_preference_my_time_zone=True,
                web_account_panel_switch_workspace=False,
                web_account_panel_take_a_tour=True,
                web_account_panel_help=True,
                web_account_panel_log_out=True,
                mobile_downloads=True,
                table_of_contents_header=True,
                table_of_contents_content_info=True,
                table_of_contents_chapter_and_page=True,
                switch_library_server=True,
                create_new_content_dossier=True,
                create_new_content_report=False,
                layout_tile_view=True,
                layout_list_view=True,
                ai_assistant=True,
                share_panel_manage_access=True,
                bot_window_share_panel=True,
                bot_window_share_panel_share_bot=True,
                bot_window_share_panel_embed_bot=True,
                bot_window_share_panel_manage_access=False,
                bot_window_edit_bot=True,
                create_new_content_bot=False,
                dashboard_view_mode=True,
                content_info_content_creator=False,
                content_info_timestamp=True,
                content_info_description=True,
                content_info_project=True,
                content_info_path=True,
                content_info_object_id=True,
                content_info_info_window=True,
                control_filter_summary=True,
                hide_filter_summary=False,
                sidebars_unpin=True,
                table_of_contents_unpin=False,
                filter_panel_unpin=True,
                comments_panel_unpin=False,
                ai_assistant_unpin=True,
                table_of_contents_allow_close=True,
                filter_panel_allow_close=True,
                comments_panel_allow_close=True,
                ai_assistant_allow_close=True,
            ),
            customized_item_properties={
                'report_a_problem': {'address': 'essa@bessa.com'}
            },
            toolbar_mode=1,
            sidebars=[
                'all',
                'favorites',
                'my_groups',
                'options',
            ],
            toolbar_enabled=False,
            default_groups_name='Default Groups Not',
        ),
        theme=Application.HomeSettings.Theme(
            logos=Application.HomeSettings.Theme.Logos(
                web=Application.HomeSettings.Theme.Logos.Logo(
                    type='URL',
                    value=(
                        'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%'
                        'on-D750-2Fnikonrumors.com%2Fwp-content%2Fuploads%2F2014%2F0'
                        '9%2FNiksample-photo1.jpg&f=1&nofb=1&ipt=9639facf02de16ed8'
                        '20d7c3150c2e05820c52e403a54dded4c175d00048dbabe&ipo=images'
                    ),
                ),
                favicon=Application.HomeSettings.Theme.Logos.Logo(
                    type='URL',
                    value=(
                        'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%'
                        'on-D750-2Fnikonrumors.com%2Fwp-content%2Fuploads%2F2014%2F0'
                        '9%2FNiksample-photo1.jpg&f=1&nofb=1&ipt=9639facf02de16ed8'
                        '20d7c3150c2e05820c52e403a54dded4c175d00048dbabe&ipo=images'
                    ),
                ),
                mobile=Application.HomeSettings.Theme.Logos.Logo(
                    type='URL',
                    value=(
                        'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%'
                        'on-D750-2Fnikonrumors.com%2Fwp-content%2Fuploads%2F2014%2F0'
                        '9%2FNiksample-photo1.jpg&f=1&nofb=1&ipt=9639facf02de16ed8'
                        '20d7c3150c2e05820c52e403a54dded4c175d00048dbabe&ipo=images'
                    ),
                ),
            ),
            color=Application.HomeSettings.Theme.Color(
                selected_theme='custom',
                formatting=Application.HomeSettings.Theme.Color.Formatting(
                    toolbar_fill='#0074E7',
                    toolbar_color='#FFFFFF',
                    sidebar_fill='#EDF8FF',
                    sidebar_color='#244D81',
                    sidebar_active_fill='#307BEC',
                    sidebar_active_color='#FFFFFF',
                    panel_fill='#FFFFFF',
                    panel_color='#4E4545',
                    accent_fill='#0077D7',
                    notification_badge_fill='#FF0000',
                    button_color='#FFFFFF',
                    canvas_fill='#F3F4F4',
                ),
                enable_for_bots=False,
            ),
        ),
    ),
    managed=True,
    general=Application.GeneralSettings(
        disable_advanced_settings=False,
        disable_preferences=False,
        network_timeout=420,
        cache_clear_mode=1,
        clear_cache_on_logout=True,
        max_log_size=999,
        log_level=10,
        update_interval=30,
    ),
    platforms=['web', 'mobile', 'desktop'],
    show_builtin_palettes=True,
    is_default=False,
    use_config_palettes=True,
    email_settings=Application.EmailSettings(
        enabled=True,
        host_portal='lanoches.com',
        show_branding_image=True,
        show_browser_button=True,
        show_mobile_button=True,
        show_button_description=True,
        show_reminder=True,
        show_sent_by=True,
        sent_by_text='Strategy One.',
        show_social_media=True,
        content=None,
        sender=Application.EmailSettings.Sender(
            address='library@strategy.com',
            display_name='Strategy One Library',
        ),
        branding_image={
            'url': (
                'https://letsenhance.io/static/8f5e523ee6b2479e26ecc91b9c25'
                '261e/1015f/MainAfter.jpg'
            )
        },
        button=Application.EmailSettings.Button(
            browser_button_style=Application.EmailSettings.Button.ButtonStyle(
                background_color='#3492ed',
                font_color='#ffffff',
                text='View in Browser',
            ),
            mobile_button_style=Application.EmailSettings.Button.ButtonStyle(
                background_color='#3492ed',
                font_color='#ffffff',
                text='View in Mobile App',
            ),
            mobile_button_link_type='DEFAULT',
            mobile_button_scheme='dossier',
            description=(
                '&#39;View in Mobile App&#39; may not work for all mobile '
                'mail apps. Use &#39;View in Browser&#39; option for such '
                'cases.'
            ),
        ),
        reminder=Application.EmailSettings.Reminder(
            text=(
                'Since you last checked, {&amp;NewNotificationCount} notification '
                'has been sent to you.'
            ),
            link_text='View Notification Center',
        ),
        social_media=Application.EmailSettings.SocialMedia(
            show_facebook=True,
            facebook_link='testlink',
            show_twitter=True,
            twitter_link='testlink',
            show_linked_in=True,
            linked_in_link='testlink',
            show_you_tube=True,
            you_tube_link='testlink',
        ),
    ),
    ai_settings=Application.AiSettings(
        feedback=True,
        learning=True,
        disclaimer='Disclaimer 1',
    ),
    auth_modes=Application.AuthModes(
        available_modes=[1, 16],
        default_mode=1,
    ),
)

# Get an Application by its id or name
app = Application(connection=conn, id=app.id)
app = Application(connection=conn, name=app.name)

# Alter an Application
app.alter(
    home_screen=app.home_screen,
    name='Application Validation Scripts Altered',
    general=app.general,
    email_settings=app.email_settings,
    ai_settings=app.ai_settings,
    auth_modes=app.auth_modes,
)

# Delete an Application without a prompt
app.delete(force=True)
