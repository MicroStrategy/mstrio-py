from typing import List, Optional
from enum import Enum

from mstrio.utils.helper import Dictable
from mstrio.distribution_services.subscription.common import RefreshPolicy


class Content(Dictable):
    """Class representation of subscription content object.

    Attributes:
        id: Content identifier
        type: Type of content
        name: Name of content
        personalization: Properties object which personalize content
        refresh_condition: RefreshCondition object which sets refresh condition
            of the content

    """

    class Type(Enum):
        REPORT = "report"
        DOCUMENT = "document"
        CUBE = "cube"
        DOSSIER = "dossier"
        UNSUPPORTED = "unsupported"

    class Properties(Dictable):
        """ Class representation of personalization properties

        Attributes:
            format_mode: Type that defines how much of the Report Services
                document, which has group by units, should be delivered
            view_mode: Indicates the view mode that is supported by this format
            format_type: Content format mode
            export_to_pdf_settings: ExportToPdfSettings object which specifies
                pdf settings if format_type is set to PDF
            delimiter: Format delimiter
            bursting: Bursting settings object
            prompt: Promp settings object
            file_name: file name of content
        """

        class FormatMode(Enum):
            DEFAULT = "DEFAULT"
            CURRENT_PAGE = "CURRENT_PAGE"
            ALL_PAGES = "ALL_PAGES"
            ALL_PAGES_SEPARATED = "ALL_PAGES_SEPARATED"
            CURRENT_WINDOW = "CURRENT_WINDOW"
            CURRENT_LAYOUT = "CURRENT_LAYOUT"

        class ViewMode(Enum):
            DEFAULT = "DEFAULT"
            GRID = "GRID"
            GRAPH = "GRAPH"
            BOTH = "BOTH"
            NONINTERACTIVE = "NONINTERACTIVE"

        class FormatType(Enum):
            PLAIN_TEXT = "PLAIN_TEXT"
            EXCEL = "EXCEL"
            HTML = "HTML"
            PDF = "PDF"
            STREAMING = "STREAMING"
            SWF_MHT = "SWF_MHT"
            SWF_HTML = "SWF_HTML"
            CSV = "CSV"
            VIEW = "VIEW"
            INTERACTIVE = "INTERACTIVE"
            EDITABLE = "EDITABLE"
            EXPORT_FLASH = "EXPORT_FLASH"
            PHONE = "PHONE"
            TABLET = "TABLET"
            JSON = "JSON"
            MSTR = "MSTR"

        class ExportToPdfSettings(Dictable):
            """Export to PDF Settings

            Attributes:
                page_option: Specifies whether to export current page or all
                    pages
                page_size: Page size of the PDF file
                orientation: Page orientation. If 'auto' is being used, the
                    exporting engine might swap the width and the height of the
                    page to optimize the export
                page_detail_level: Specifies the detail level of page to
                    be displayed
                include_header: Specifies whether to include header
                include_footer: Specifies whether to include footer
                include_toc: Specifies whether to include table of contents
                filter_summary: Specifies the options of including filter
                    summary in the exported PDF. If 'NONE' is being used, no
                    filter summary will be displayed. If 'BAR' is being used,
                    filter summary bar will be displayed on each page. If 'PAGE'
                    is being used, filter summary page will be displayed at the
                    end of each chapter. If 'ALL' is being used, both filter
                    summary bar and page will be displayed.
                fit_to_page: Specifies whether to fit grid to page
                repeat_column_header: Specifies whether to repeat grid column
                    header
                grid_paging_mode: Specifies how grids should be paginated
            """

            class PageOption(Enum):
                DEFAULT = "DEFAULT"
                ALL = "ALL"
                CURRENT = "CURRENT"
                PAGE = "PAGE"

            class PageSize(Enum):
                A3 = "a3"
                A4 = "a4"
                A5 = "a5"
                B4 = "b4"
                B5 = "b5"
                LETTER = "letter"
                LEGAL = "legal"
                LEDGER = "ledger"
                EXECUTIVE = "executive"
                FOLIO = "folio"
                STATEMENT = "statement"
                UNSUPPORTED = "unsupported"

            class PageDetailLevel(Enum):
                OVERVIEW = "overview"
                DETAILED_PAGES = "detailed_pages"
                OVERVIEW_AND_DETAILED_PAGES = "overview_and_detailed_pages"

            class Orientation(Enum):
                AUTOMATIC = "automatic"
                PORTRAIT = "portrait"
                LANDSCAPE = "landscape"

            class GridPagingMode(Enum):
                NONE = "none"
                ENLARGE = "enlarge"

            class FilterSummary(Enum):
                NONE = "NONE"
                BAR = "BAR"
                PAGE = "PAGE"
                ALL = "ALL"

            # ExportToPdfSettings
            def __init__(self, page_option: PageOption = PageOption.PAGE,
                         page_size: PageSize = PageSize.LETTER,
                         orientation: Orientation = Orientation.AUTOMATIC,
                         page_detail_level=PageDetailLevel.OVERVIEW, include_header: bool = True,
                         include_footer: bool = True, include_toc: bool = False,
                         filter_summary: FilterSummary = FilterSummary.BAR,
                         fit_to_page: bool = False, repeat_column_header: bool = False,
                         grid_paging_mode: GridPagingMode = GridPagingMode.NONE):

                self.page_option = page_option
                self.page_size = page_size
                self.page_detail_level = page_detail_level
                self.orientation = orientation
                self.include_header = include_header
                self.include_footer = include_footer
                self.include_toc = include_toc
                self.filter_summary = filter_summary
                self.fit_to_page = fit_to_page
                self.repeat_column_header = repeat_column_header
                self.grid_paging_mode = grid_paging_mode

            _FROM_DICT_MAP = {
                "page_option": PageOption,
                "page_size": PageSize,
                "orientation": Orientation,
                "filter_summary": FilterSummary
            }

        class Bursting(Dictable):
            """Bursting settings

            Attributes:
                slicing_attributes: The list of attributes to slice on
                address_attribute_id: Attribute ID in the email burst feature
                device_id: Device ID in the email burst feature
                form_id: Form ID in the email burst feature
            """

            def __init__(self, slicing_attributes: List[str] = [],
                         address_attribute_id: Optional[str] = None,
                         device_id: Optional[str] = None, form_id: Optional[str] = None):
                self.slicing_attributes = slicing_attributes
                self.address_attribute_id = address_attribute_id
                self.device_id = device_id
                self.form_id = form_id

        class Prompt(Dictable):

            def __init__(self, enabled: bool, instance_id: str = None):
                self.enabled = enabled
                self.instance_id = instance_id

        # Properties
        def __init__(self, format_mode: FormatMode = FormatMode.DEFAULT,
                     view_mode: ViewMode = ViewMode.DEFAULT,
                     format_type: FormatType = FormatType.PDF,
                     export_to_pdf_settings: Optional[ExportToPdfSettings] = None,
                     delimiter: Optional[str] = None, bursting: Optional[Bursting] = None,
                     prompt: Optional[Prompt] = None, file_name: Optional[str] = None):

            self.format_mode = format_mode
            self.view_mode = view_mode
            self.format_type = format_type
            pdf_format = format_type in [self.FormatType.PDF, self.FormatType.PDF.value]
            self.export_to_pdf_settings = export_to_pdf_settings if pdf_format else None
            self.delimiter = delimiter
            self.bursting = bursting
            self.prompt = prompt
            self.file_name = file_name

        _FROM_DICT_MAP = {
            "format_mode": FormatMode,
            "view_mode": ViewMode,
            "format_type": FormatType,
            "export_to_pdf_settings": ExportToPdfSettings.from_dict,
            "bursting": Bursting.from_dict,
            "prompt": Prompt.from_dict
        }

    class RefreshCondition(Dictable):
        """Dataset refresh condition settings

        Attributes:
            tables: List of TableRefreshInfo objects
            dataset_refresh_policy: Default refresh policy for all the tables
                in the dataset. The setting value must be provided if the tables
                setting value is not provided or empty.
            filters: list of SubscriptionFilter objects
        """

        class SubscriptionFilter(Dictable):
            """Subscription filter. The format of the subscription filters are
                exactly the same as the view filters. Please refer to
                https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/projects/RESTSDK/Content/topics/REST_API/REST_API_Filtering_RptsCubes_ViewFilter_CodeSamples.htm#multiple_filters_on_attribute_forms
                for detailed information. But itshould be noted that
                subscription filters only support Filter on attribute forms
                and Multiple filters on attribute forms.

            Attributes:
                type: Filter type
                expression: Metric limits
            """

            def __init__(self, type: str, expression):
                self.type = type
                self.expression = expression

        class TableRefreshInfo(Dictable):
            """Table refresh settings. When the setting is absent in the
                response or the array is empty, the datasetRefreshPolicy setting
                value must be provided and will be used as the refresh policy
                for all the tables, including the new added table after
                the scheduler is set up.

            Attributes:
                id: Table ID
                refresh_policy: Table refresh policy
                alternateSource: AlternateSource object
            """

            class AlternateSource(Dictable):
                """Alternate source

                Attributes:
                    db_role_id: Database instance ID of alternate source
                    namespace: Database namespace of alternate source
                    table_name: Table name of alternate source
                    url: URL of alternate source
                """

                # XXX: Should all of those be optional or all required or what?
                def __init__(self, db_role_id: Optional[str] = None,
                             namespace: Optional[str] = None, table_name: Optional[str] = None,
                             url: Optional[str] = None):
                    self.db_role_id = db_role_id
                    self.namespace = namespace
                    self.table_name = table_name
                    self.url = url

            # TableRefreshInfo
            def __init__(self, id: str, refresh_policy: RefreshPolicy,
                         alternate_source: Optional[AlternateSource] = None):
                self.id = id
                self.refresh_policy = refresh_policy
                self.alternate_source = alternate_source

            _FROM_DICT_MAP = {
                "refresh_policy": RefreshPolicy,
                "alternate_source": AlternateSource.from_dict
            }

        # RefreshCondition
        def __init__(self, tables: List[TableRefreshInfo],
                     dataset_refresh_policy: Optional[RefreshPolicy] = None,
                     filters: Optional[List[SubscriptionFilter]] = None):
            self.tables = tables
            self.dataset_refresh_policy = dataset_refresh_policy
            self.filters = filters

        _FROM_DICT_MAP = {
            "dataset_refresh_policy": RefreshPolicy,
            "tables": lambda tables: [
                Content.RefreshCondition.TableRefreshInfo.from_dict(t)  # noqa
                for t in tables
            ],
            "filters": lambda filters: [
                Content.RefreshCondition.SubscriptionFilter.from_dict(f)  # noqa
                for f in filters
            ],
        }

    # Content
    def __init__(self, id: str, type: Type, name: Optional[str] = None,
                 personalization: Optional[Properties] = None,
                 refresh_condition: Optional[RefreshCondition] = None):
        self.id = id
        self.type = type
        self.name = name
        self.personalization = personalization
        self.refresh_condition = refresh_condition

    _FROM_DICT_MAP = {
        "type": Type,
        "personalization": Properties.from_dict,
        "refresh_condition": RefreshCondition.from_dict
    }
