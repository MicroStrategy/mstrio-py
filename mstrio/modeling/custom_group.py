import logging
import uuid
from enum import auto
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import custom_groups
from mstrio.modeling.expression import Expression, ExpressionFormat
from mstrio.modeling.metric.metric_format import MetricFormat
from mstrio.modeling.schema.helpers import ObjectSubType
from mstrio.object_management import Folder, SearchPattern, full_search
from mstrio.object_management.object import Object
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    Dictable,
    construct_expression_body,
    delete_none_values,
    filter_params_for_func,
    find_object_with_name,
)
from mstrio.utils.resolvers import (
    get_drill_map_id_from_params_set,
    get_folder_id_from_params_set,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import custom_groups as cg_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import (
    class_version_handler,
    meets_minimal_version,
    method_version_handler,
)
from mstrio.utils.vldb_mixin import ModelVldbMixin

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


class CustomGroupOptions(Dictable):
    """Custom Group display options.

    Attributes:
        hierarchy_display: Whether to enable hierarchical display. Default is
            True.
        subtotals_display: Whether to enable subtotals display. Default is
            False.
        element_header_above_child: Whether to display element header above
            child elements. Default is True.
    """

    def __init__(
        self,
        hierarchy_display: bool | None = None,
        subtotals_display: bool | None = None,
        element_header_above_child: bool | None = None,
    ):
        self.hierarchy_display = hierarchy_display
        self.subtotals_display = subtotals_display
        self.element_header_above_child = element_header_above_child


class ElementDisplayOption(AutoName):
    """Enumeration of Custom Group Element display options.

    Attributes:
        ELEMENT: Display only the element name.
        INDIVIDUAL: Display only individual items within the element.
        INDIVIDUAL_EXPAND: Display individual items within the element. Expand
            individual items if possible.
        ELEMENT_INDIVIDUAL_EXPAND: Display both the element name and individual
            items. Expand individual items if possible.
    """

    ELEMENT = auto()
    INDIVIDUAL = auto()
    INDIVIDUAL_EXPAND = auto()
    ELEMENT_INDIVIDUAL_EXPAND = auto()


class CustomGroupElement(Dictable):
    """Custom Group Element representation.

    Attributes:
        name (str): Name of the custom group element.
        display (ElementDisplayOption): Display option for the element.
        element_format (MetricFormat): Format settings for the element.
        items_format (MetricFormat): Format settings for individual items in
            the report.
        qualification (Expression): Qualification expression for the element.
        id (str, optional): ID of the custom group element. If not provided,
            it will be generated automatically and replaced by server-generated
            ID when Custom Group is created on the server.
    """

    _FROM_DICT_MAP = {
        "display": ElementDisplayOption,
        "element_format": MetricFormat.from_dict,
        "items_format": MetricFormat.from_dict,
        "qualification": Expression.from_dict,
    }

    def __init__(
        self,
        name: str,
        display: ElementDisplayOption,
        qualification: Expression,
        element_format: MetricFormat | None = None,
        items_format: MetricFormat | None = None,
        id: str | None = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.display = display
        self.element_format = element_format
        self.items_format = items_format
        self.qualification = qualification


@method_version_handler("11.3.0200")
def list_custom_groups(
    connection: "Connection",
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: "Project | str | None" = None,
    project_id: str | None = None,
    project_name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    folder: "Folder | tuple[str] | list[str] | str | None" = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> list["CustomGroup"] | list[dict]:
    """Get a list of CustomGroup objects or dicts. Optionally filter the
    objects by specifying `filters` parameters.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        name (str, optional): value the search pattern is set to, which
            will be applied to the names of CustomGroup objects being searched
        to_dictionary (bool, optional): If `True` returns dictionaries, by
            default (`False`) returns `CustomGroup` objects.
        limit (int, optional): limit the number of elements returned. If `None`
            (default), all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        show_expression_as (ExpressionFormat or str, optional): specify how
            expressions should be presented
            Available values:
            - None
            (expression is returned in "text" format)
            - `ExpressionFormat.TREE` or `tree`
            (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`
            (expression is returned in `text` and `tokens` formats)
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['id', 'name',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'owner', 'ext_type']
    Returns:
        list of filter objects or list of filter dictionaries.
    """
    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    objects = full_search(
        connection,
        object_types=ObjectSubTypes.CUSTOM_GROUP,
        project=proj_id,
        pattern=search_pattern,
        name=name,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects

    # `show_expression_as` does not apply to search. It has to be stored in the
    # `CustomGroup` object for when the element expressions are retrieved later
    # in the object's lifetime.
    return [
        CustomGroup.from_dict(
            source={
                "show_expression_as": (
                    show_expression_as
                    if isinstance(show_expression_as, ExpressionFormat)
                    else ExpressionFormat(show_expression_as)
                ),
                **obj,
            },
            connection=connection,
        )
        for obj in objects
    ]


@class_version_handler("11.3.0200")
class CustomGroup(Entity, CopyMixin, MoveMixin, DeleteMixin, ModelVldbMixin):
    """Python representation of a Custom Group object.

    Attributes:
        name (str): Name of the custom group.
        id (str): ID of the custom group.
        description (str): Description of the custom group.
        sub_type (ObjectSubType): Subtype of the object in metadata, here:
            CUSTOM_GROUP.
        version (str): Version of the object in metadata.
        ancestors (list[dict]): List of ancestor folders.
        type (ObjectTypes): Type of the object in metadata, here: FILTER.
        date_created (datetime): Date and time when the object was created.
        date_modified (datetime): Date and time when the object was last
            modified.
        owner (dict): Information about the owner of the object.
        acg (Rights): Access rights flags for the object.
        acl (list[ACE]): Access control list for the object.
        is_embedded (bool): If True, indicates that the target object of this
            reference is embedded within this object. Alternatively if this
            object is itself embedded, then it means that the target object is
            embedded in the same container as this object. If this field is
            omitted (as is usual) then the target is not embedded.
        path (str): Path to the object in the project/folder structure.
        primary_locale (str): The primary locale of the object, in the
            IETF BCP 47 language tag format, such as "en-US". Read only.
        hidden (bool): Whether the object is hidden in the folder structure.
        elements (list[CustomGroupElement]): List of custom group elements.
            Note: IDs of the elements are generated by the server independently
            from the client-side generated IDs and differ between fetches.
        drill_map (dict, optional): Drill map used by the custom group.
        options (CustomGroupOptions, optional): Display options for the custom
            group.
    """

    _OBJECT_TYPE = ObjectTypes.FILTER
    _OBJECT_SUBTYPES = [ObjectSubTypes.CUSTOM_GROUP]

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "owner": User.from_dict,
        "subtype": ObjectSubTypes,
        "sub_type": ObjectSubType,
        "elements": [CustomGroupElement.from_dict],
        "options": CustomGroupOptions.from_dict,
    }
    _API_GETTERS = {
        (
            "type",
            "subtype",
            "ext_type",
            "date_created",
            "date_modified",
            "version",
            "owner",
            "ancestors",
            "acg",
            "acl",
            "hidden",
            "comments",
        ): objects_processors.get_info,
        (
            "id",
            "name",
            "description",
            "sub_type",
            "date_created",
            "date_modified",
            "path",
            "version_id",
            "is_embedded",
            "primary_locale",
            "destination_folder_id",
            "elements",
            "drill_map",
            "options",
        ): cg_processors.get_custom_group,
    }
    _API_PATCH = {
        (
            "name",  # required by Custom Group REST even if not changing
            "primary_locale",
            "elements",
            "drill_map",
            "options",
        ): (cg_processors.update_custom_group, "partial_put"),
        (
            "description",
            "folder_id",
            "hidden",
            "comments",
            "owner",
        ): (objects_processors.update, "partial_put"),
    }

    _MODEL_VLDB_API = {
        'GET_ADVANCED': custom_groups.get_custom_group,
        'GET_APPLICABLE': custom_groups.get_applicable_vldb_settings,
    }

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        name: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ):
        """Initialize Custom Group object by its identifier.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): Metadata ID of the Custom Group. May be omitted
                if `name` parameter is provided.
            name (str, optional): Name of the Custom Group.
            show_expression_as (enum or str, optional): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS` or `tokens`
            show_filter_tokens (bool, optional): specify whether `qualification`
                is returned in `tokens` format, along with `text` and `tree`
                format
        """
        connection._validate_project_selected()
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            found_cg = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_custom_groups,
            )
            id = found_cg["id"]

        super().__init__(
            connection=connection,
            object_id=id,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.primary_locale = kwargs.get("primary_locale", default_value)
        self.is_embedded = kwargs.get("is_embedded", default_value)
        self.destination_folder_id = kwargs.get("destination_folder_id", default_value)
        self._sub_type = (
            ObjectSubType(kwargs.get("sub_type"))
            if kwargs.get("sub_type")
            else default_value
        )
        self._path = kwargs.get("path", default_value)
        self.elements = (
            [CustomGroupElement.from_dict(el) for el in kwargs.get("elements", [])]
            if kwargs.get("elements")
            else default_value
        )
        self.drill_map = kwargs.get("drill_map", default_value)
        self.options = (
            CustomGroupOptions.from_dict(kwargs.get("options"))
            if kwargs.get("options")
            else default_value
        )
        show_expression_as = kwargs.get("show_expression_as", "tree")
        self._show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )

        # PUT endpoint requires 'information.name' in the body even if name is
        # not being changed. Wrapper must know the objects body, hence setting
        # method here.
        self._MODEL_VLDB_API = self._MODEL_VLDB_API.copy()
        self._MODEL_VLDB_API["PUT_ADVANCED"] = self._update_vldb_properties

    @staticmethod
    def _construct_element_body(element: CustomGroupElement) -> dict:
        body = element.to_dict()
        body["qualification"] = construct_expression_body(element.qualification)
        return body

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        elements: list[CustomGroupElement],
        destination_folder: "Folder | tuple[str] | list[str] | str | None" = None,
        destination_folder_path: tuple[str] | list[str] | str | None = None,
        description: str | None = None,
        primary_locale: str | None = None,
        options: CustomGroupOptions | None = None,
        drill_map: Object | str | None = None,
        drill_map_id: str | None = None,
        drill_map_name: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        journal_comment: str | None = None,
    ) -> "CustomGroup":
        """Create a new Custom Group object on the server.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            name (str): Name of the custom group.
            elements (list[CustomGroupElement]): List of elements to include in
                the custom group.
            destination_folder (Folder | tuple | list | str, optional): Folder
                object or ID or name or path specifying the folder where to
                create object.
            destination_folder_path (str, optional): Path of the folder.
                The path has to be provided in the following format:
                    /MicroStrategy Tutorial/Public Objects/Metrics
            description (str, optional): Description of the custom group.
            primary_locale (str, optional): the primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
            options (CustomGroupOptions, optional): Display options
                for the custom group.
            drill_map (Object | str, optional): Object or ID or name specifying
                the drill map. May be used instead of `drill_map_id` or
                `drill_map_name`.
            drill_map_id (str, optional): ID of a drill map.
            drill_map_name (str, optional): Name of a drill map.
            show_expression_as (ExpressionFormat | str, optional): How
                expressions should be presented. Defaults to
                ExpressionFormat.TREE.
            journal_comment (optional, str): Comment that will be added to the
                object's change journal entry

        Returns:
            CustomGroup | dict: Newly created Custom Group object.
        """

        dest_id = get_folder_id_from_params_set(
            connection,
            connection.project_id,
            folder=destination_folder,
            folder_path=destination_folder_path,
        )
        drill_map_id = get_drill_map_id_from_params_set(
            connection,
            drill_map=drill_map,
            drill_map_id=drill_map_id,
            drill_map_name=drill_map_name,
        )
        body = {
            "information": {
                "name": name,
                "description": description,
                "destinationFolderId": dest_id,
                "primaryLocale": primary_locale,
            },
            "drillMap": {"objectId": drill_map_id} if drill_map_id else None,
            "options": options.to_dict() if options else None,
            "elements": [cls._construct_element_body(el) for el in elements],
        }

        if journal_comment:
            body.update({"changeJournal": {"userComments": journal_comment}})
        body = delete_none_values(body, recursion=True)

        response = cg_processors.create_custom_group(
            connection,
            body=body,
            project_id=connection.project_id,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
        )

        if config.verbose:
            logger.info(
                f"Successfully created custom group named: '{name}' with ID: '"
                f"{response['id']}'"
            )
        return cls.from_dict(
            source={
                **response,
                "show_expression_as": show_expression_as,
            },
            connection=connection,
        )

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        primary_locale: str | None = None,
        elements: list[CustomGroupElement] | None = None,
        options: CustomGroupOptions | None = None,
        drill_map: Object | str | None = None,
        drill_map_id: str | None = None,
        drill_map_name: str | None = None,
        remove_drill_map: bool = False,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
        journal_comment: str | None = None,
    ):
        """Alter properties of the Custom Group object.
        Args:
            name (str, optional): New name of the custom group.
            description (str, optional): New description of the custom group.
            primary_locale (str, optional): New primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US".
            elements (list[CustomGroupElement], optional): New list of elements
                to include in the custom group. This will completely replace
                the existing list of elements.
            options (CustomGroupOptions, optional): New display options
                for the custom group. May be partially specified to update only
                certain options.
            drill_map (Object | str, optional): Object or ID or name specifying
                the drill map. May be used instead of `drill_map_id` or
                `drill_map_name`.
            drill_map_id (str, optional): ID of a drill map.
            drill_map_name (str, optional): Name of a drill map.
            remove_drill_map (bool, optional): If `True`, removes the drill map
                from the custom group. Defaults to `False`.
            hidden (bool, optional): Whether the object is hidden in the folder
                structure.
            comments (str, optional): Long description for the object.
            owner (str | User, optional): New owner of the object. Can be
                specified either as User object or user ID.
            journal_comment (str, optional): Comment that will be added to the
                object's change journal entry.
        """
        if name is None:
            name = self.name  # REST requires name in body, even if not changing
        drill_map_id = get_drill_map_id_from_params_set(
            self.connection,
            drill_map=drill_map,
            drill_map_id=drill_map_id,
            drill_map_name=drill_map_name,
        )
        if drill_map_id:
            drill_map = {"objectId": drill_map_id}
        if remove_drill_map:
            drill_map = {}
            if not meets_minimal_version(self.connection.iserver_version, "11.6.0100"):
                logger.warning(
                    "Removing Drill Map from Custom Group is not supported "
                    "in I-Server versions prior to 11.6.0100. The operation "
                    "will be attempted, but may fail."
                )
        if elements:
            elements = [self._construct_element_body(el) for el in elements]
        if isinstance(owner, User):
            owner = owner.id

        if remove_drill_map:
            # When fetching afterwards, "drill_map" field will be unset rather
            # than set to None and the field in local object will not update
            # If failed to remove, will fetch again
            self.drill_map = None

        properties = filter_params_for_func(
            self.alter,
            locals(),
            exclude=["self", "drill_map_id", "drill_map_name", "remove_drill_map"],
        )
        properties = delete_none_values(properties, recursion=True)
        self._alter_properties(**properties)

    @staticmethod
    def _match_element(
        el: CustomGroupElement, id: str | None, name: str | None
    ) -> bool:
        """Match Custom Group Element by ID or name query args. To be used by
        element-related methods.

        Args:
            el (CustomGroupElement): Custom Group Element to match against.
            id (str, optional): ID of the custom group element.
            name (str, optional): Name of the custom group element.

        Returns:
            bool: True if the element matches the query, False otherwise.
        """
        if id is not None:
            return el.id == id
        if name is not None:
            return el.name == name
        return False

    def get_element(
        self,
        id: str | None = None,  # must be one of the two
        name: str | None = None,
        to_dictionary: bool = False,
    ) -> CustomGroupElement | dict:
        """Get a specific Custom Group Element by its ID or name.

        Note:
            Provide either `id` or `name` parameter, but not both.

        Args:
            id (str, optional): ID of the custom group element. May be omitted
                if `name` parameter is provided.
            name (str, optional): Name of the custom group element.
            to_dictionary (bool, optional): If `True` returns a dictionary
                instead of a `CustomGroupElement` object. Default is `False`.

        Returns:
            CustomGroupElement | dict | None: The specified custom group element
                or None if not found.
        """
        if not bool(id) ^ bool(name):
            raise ValueError(
                "Please specify either `id` or `name`, but not both nor neither"
            )
        for el in self.elements:
            if self._match_element(el, id, name):
                return el.to_dict() if to_dictionary else el
        return None

    def create_element(
        self,
        name: str,
        display: ElementDisplayOption,
        qualification: Expression,
        element_format: MetricFormat | None = None,
        items_format: MetricFormat | None = None,
        journal_comment: str | None = None,
    ):
        """Create a new Custom Group Element and add it to the Custom Group.

        Args:
            name (str): Name of the custom group element.
            display (ElementDisplayOption): Display option for the element.
            element_format (MetricFormat, optional): Format settings for
                the element.
            items_format (MetricFormat, optional): Format settings for
                individual items in the report.
            qualification (Expression): Qualification expression
                for the element.
            journal_comment (str, optional): Comment that will be added to the
                object's change journal entry.
        """
        new_element = CustomGroupElement(
            name=name,
            display=display,
            element_format=element_format,
            items_format=items_format,
            qualification=qualification,
        )
        new_elements = self.elements.copy()
        new_elements.append(new_element)
        self.alter(elements=new_elements, journal_comment=journal_comment)

    def alter_element(
        self,
        id: str,
        name: str | None = None,
        display: ElementDisplayOption | None = None,
        element_format: MetricFormat | None = None,
        items_format: MetricFormat | None = None,
        reset_format: bool = False,
        qualification: Expression | None = None,
        journal_comment: str | None = None,
    ):
        """Alter properties of a specific Custom Group Element.

        Args:
            id (str): ID of the custom group element to alter.
            name (str, optional): New name of the custom group element.
            display (ElementDisplayOption, optional): New display option
                for the element.
            element_format (MetricFormat, optional): Format settings for
                the element.
            items_format (MetricFormat, optional): Format settings for
                individual items in the report.
            reset_format (bool, optional): If `True`, erase format settings
                previously set on the server for both `element_format` and
                `items_format`. Defaults to `False`.
            qualification (Expression, optional): New qualification expression
                for the element.
            journal_comment (str, optional): Comment that will be added to the
                object's change journal entry.
        """
        altered_element = self.get_element(id=id)
        if altered_element is None:
            if config.verbose:
                logger.warning(f"No element found with ID: {id}")
            return
        if name is not None:
            altered_element.name = name
        if display is not None:
            altered_element.display = display
        if element_format is not None or reset_format:
            altered_element.element_format = element_format
        if items_format is not None or reset_format:
            altered_element.items_format = items_format
        if qualification is not None:
            altered_element.qualification = qualification
        new_elements = [el for el in self.elements if not el.id == id]
        new_elements.append(altered_element)
        self.alter(elements=new_elements, journal_comment=journal_comment)

    def delete_element(
        self,
        id: str,
        journal_comment: str | None = None,
    ):
        """Delete a specific Custom Group Element from the Custom Group.

        Args:
            id (str): ID of the custom group element to delete.
            journal_comment (str, optional): Comment that will be added to the
                object's change journal entry.
        """
        new_elements = [el for el in self.elements if not el.id == id]
        if len(new_elements) == len(self.elements):
            if config.verbose:
                logger.warning(f"No element found with ID: {id}")
        else:
            self.alter(elements=new_elements, journal_comment=journal_comment)

    # VLDB methods. Wrapped with version checks as relevant APIs were added
    # later than the ones for Custom Group object.

    @method_version_handler("11.5.0900")
    def list_vldb_settings(
        self,
        set_names=None,
        names=None,
        groups=None,
        to_dictionary=False,
        to_dataframe=False,
    ):
        return super().list_vldb_settings(
            set_names, names, groups, to_dictionary, to_dataframe
        )

    @method_version_handler("11.5.0900")
    def alter_vldb_settings(self, names_to_values):
        return super().alter_vldb_settings(names_to_values)

    @method_version_handler("11.5.0900")
    def reset_vldb_settings(self, set_names=None, names=None, groups=None, force=False):
        return super().reset_vldb_settings(set_names, names, groups, force)

    def _update_vldb_properties(self, connection: "Connection", id: str, body: dict):
        """Update VLDB properties of the Custom Group object.
        Wraps custom_groups.update_custom_group API call to account for
            required 'information.name' field in the body.
        """
        if "information" not in body:
            body["information"] = {}
        if "name" not in body["information"]:
            body["information"]["name"] = self.name
        custom_groups.update_custom_group(connection, id, body)

    # TODO: remove to standalone function when implementing Drill Map class
    @staticmethod
    def _list_drill_maps(connection: "Connection"):
        return full_search(
            connection,
            object_types=ObjectTypes.DRILL_MAP,
            project=connection.project_id,
        )
