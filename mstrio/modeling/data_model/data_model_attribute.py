import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.modeling.data_model.data_model_component import DataModelComponent
from mstrio.modeling.data_model.helpers import unpack_information_dict
from mstrio.utils.helper import Dictable, delete_none_values
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.data_model.data_model import DataModel
    from mstrio.modeling.schema.attribute.smart_attribute import SmartAttribute

logger = logging.getLogger(__name__)


def _to_rest(value):
    """Convert Dictable value objects (or lists of them) to REST dicts."""
    if isinstance(value, Dictable):
        return value.to_dict()
    if isinstance(value, list):
        return [_to_rest(item) for item in value]
    return value


@method_version_handler('11.6.0100')
def list_data_model_attributes(
    connection: Connection,
    data_model: 'DataModel | str',
    to_dictionary: bool = False,
    limit: int | None = None,
    offset: int | None = None,
    fields: str | None = None,
    show_expression_as: str | None = None,
    show_derived_forms: bool | None = None,
    show_subscription_filter_candidates_only: bool | None = None,
    changeset_id: str | None = None,
) -> list['DataModelAttribute'] | list[dict]:
    """Get a list of attributes of a Mosaic data model.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        data_model (DataModel | str): data model object or its ID
        to_dictionary (bool, optional): if True, return attributes as
            a list of dicts
        limit (int, optional): limit the number of elements returned
        offset (int, optional): starting point within the collection
        fields (str, optional): comma-separated top-level field whitelist
        show_expression_as (str, optional): specify how expressions are
            presented ('tree' or 'tokens')
        show_derived_forms (bool, optional): whether to show derived forms
        show_subscription_filter_candidates_only (bool, optional): whether to
            return only subscription filter candidates
        changeset_id (str, optional): ID of an existing changeset to read from

    Returns:
        A list of DataModelAttribute objects or dictionaries representing
        them.
    """
    data_model_id = data_model if isinstance(data_model, str) else data_model.id
    attributes = (
        data_models.list_data_model_attributes(
            connection,
            id=data_model_id,
            changeset_id=changeset_id,
            offset=offset,
            limit=limit,
            fields=fields,
            show_expression_as=show_expression_as,
            show_derived_forms=show_derived_forms,
            show_subscription_filter_candidates_only=(
                show_subscription_filter_candidates_only
            ),
        )
        .json()
        .get('attributes', [])
    )
    if limit:
        attributes = attributes[:limit]
    if to_dictionary:
        return [unpack_information_dict(attr) for attr in attributes]
    return [
        DataModelAttribute._from_api_source(connection, data_model_id, attr)
        for attr in attributes
    ]


@class_version_handler('11.6.0100')
class DataModelAttribute(DataModelComponent):
    """Python representation of an attribute of a Mosaic data model."""

    _ACL_SUBTYPE = 'attribute'
    _GET_FUNC = staticmethod(data_models.get_data_model_attribute)
    _DELETE_FUNC = staticmethod(data_models.delete_data_model_attribute)
    _ID_KWARG = 'attribute_id'

    @classmethod
    def create(
        cls,
        connection: Connection,
        data_model: 'DataModel | str',
        name: str,
        forms: list,
        key_form: 'Dictable | dict | None' = None,
        displays: 'Dictable | dict | None' = None,
        description: str | None = None,
        attribute_lookup_table: 'Dictable | dict | None' = None,
        sorts: 'Dictable | dict | None' = None,
        definition: dict | None = None,
        show_expression_as: str | None = None,
        allow_link: bool | None = None,
        show_derived_forms: bool | None = None,
    ) -> 'DataModelAttribute':
        """Create a new attribute in a Mosaic data model.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model (DataModel | str): data model object or its ID
            name (str): name of the attribute
            forms (list): attribute forms; `AttributeForm`-like value objects
                from `mstrio.modeling.schema` or plain dicts matching the
                `ms-DataModelAttributeForm` schema
            key_form (FormReference | dict, optional): key form reference
            displays (AttributeDisplays | dict, optional): report and browse
                displays of the attribute
            description (str, optional): description of the attribute
            attribute_lookup_table (SchemaObjectReference | dict, optional):
                lookup table reference
            sorts (AttributeSorts | dict, optional): report and browse sorts
            definition (dict, optional): additional top-level body keys of the
                `ms-DataModelAttribute` schema merged into the request body
                (e.g. `isTimezoneAware`)
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')
            allow_link (bool, optional): whether to allow linking
            show_derived_forms (bool, optional): whether to show derived forms

        Returns:
            DataModelAttribute object.
        """
        data_model_id = data_model if isinstance(data_model, str) else data_model.id
        body = {
            'name': name,
            'description': description,
            'forms': _to_rest(forms),
            'keyForm': _to_rest(key_form),
            'displays': _to_rest(displays),
            'attributeLookupTable': _to_rest(attribute_lookup_table),
            'sorts': _to_rest(sorts),
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.create_data_model_attribute(
            connection,
            id=data_model_id,
            body=body,
            show_expression_as=show_expression_as,
            allow_link=allow_link,
            show_derived_forms=show_derived_forms,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created attribute named: '{name}' with ID: '"
                f"{response.get('id')}' in data model '{data_model_id}'."
            )
        return cls._from_api_source(connection, data_model_id, response)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        forms: list | None = None,
        key_form: 'Dictable | dict | None' = None,
        displays: 'Dictable | dict | None' = None,
        sorts: 'Dictable | dict | None' = None,
        definition: dict | None = None,
    ) -> None:
        """Alter the attribute (partial update via PATCH).

        Args:
            name (str, optional): new name of the attribute
            description (str, optional): new description of the attribute
            forms (list, optional): new attribute forms
            key_form (FormReference | dict, optional): new key form reference
            displays (AttributeDisplays | dict, optional): new displays
            sorts (AttributeSorts | dict, optional): new sorts
            definition (dict, optional): additional top-level body keys merged
                into the request body
        """
        body = {
            'name': name,
            'description': description,
            'forms': _to_rest(forms),
            'keyForm': _to_rest(key_form),
            'displays': _to_rest(displays),
            'sorts': _to_rest(sorts),
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.update_data_model_attribute(
            self.connection,
            id=self.data_model_id,
            attribute_id=self.id,
            body=body,
        )
        self._set_object_attributes(**unpack_information_dict(response.json()))
        if config.verbose:
            logger.info(
                f"Successfully altered attribute with ID: '{self.id}' in data "
                f"model '{self.data_model_id}'."
            )

    def list_relationships(self) -> dict:
        """Get the relationships of the attribute.

        Returns:
            Dictionary with a `relationships` list
            (`ms-AttributeRelationships` schema).
        """
        return data_models.get_data_model_attribute_relationships(
            self.connection, id=self.data_model_id, attribute_id=self.id
        ).json()

    def update_relationships(self, relationships: dict | list) -> dict:
        """Update the relationships of the attribute.

        Note:
            The underlying endpoint is a PUT which REPLACES the attribute's
            ENTIRE relationship list. Omitting existing relationships DELETES
            them. Always read the current list with `list_relationships()`,
            modify it and send the full list back (read-modify-write).

        Args:
            relationships (dict | list): either the full
                `ms-AttributeRelationships` body (`{'relationships': [...]}`)
                or a plain list of relationship dicts

        Returns:
            Dictionary with the updated `relationships` list.
        """
        body = (
            relationships
            if isinstance(relationships, dict)
            else {'relationships': _to_rest(relationships)}
        )
        return data_models.update_data_model_attribute_relationships(
            self.connection, id=self.data_model_id, attribute_id=self.id, body=body
        ).json()

    def list_elements(
        self,
        offset: int | None = None,
        limit: int | None = None,
        search_pattern: str | None = None,
        element_id_format: str | None = None,
    ) -> list[dict]:
        """List elements of the attribute (runtime endpoint).

        Args:
            offset (int, optional): starting point within the collection
            limit (int, optional): limit the number of elements returned
            search_pattern (str, optional): pattern the element names are
                matched against
            element_id_format (str, optional): format of the returned element
                IDs

        Returns:
            A list of dictionaries with element `name` and `id`.
        """
        return data_models.get_data_model_attribute_elements(
            self.connection,
            id=self.data_model_id,
            attribute_id=self.id,
            offset=offset,
            limit=limit,
            search_pattern=search_pattern,
            element_id_format=element_id_format,
        ).json()

    def list_smart_attributes(
        self, to_dictionary: bool = False
    ) -> list['SmartAttribute'] | list[dict]:
        """List smart attributes generated for this attribute.

        Args:
            to_dictionary (bool, optional): if True, return smart attributes
                as a list of dicts

        Returns:
            A list of SmartAttribute objects or dictionaries representing
            them.
        """
        from mstrio.api import smart_attributes as smart_attributes_api

        response = smart_attributes_api.list_data_model_smart_attributes(
            self.connection,
            data_model_id=self.data_model_id,
            attribute_id=self.id,
        )
        objects_ = response.json().get('smartAttributes', [])
        if to_dictionary:
            return objects_
        from mstrio.modeling.schema.attribute.smart_attribute import SmartAttribute

        return [
            SmartAttribute.from_dict(source=obj, connection=self.connection)
            for obj in objects_
        ]

    def list_smart_attribute_templates(
        self, to_dictionary: bool = False
    ) -> list['SmartAttribute'] | list[dict]:
        """List smart attribute templates available for this attribute.

        Args:
            to_dictionary (bool, optional): if True, return templates as
                a list of dicts

        Returns:
            A list of SmartAttribute objects or dictionaries representing
            them.
        """
        from mstrio.api import smart_attributes as smart_attributes_api

        response = smart_attributes_api.list_data_model_smart_attribute_templates(
            self.connection,
            data_model_id=self.data_model_id,
            attribute_id=self.id,
        )
        objects_ = response.json().get('smartAttributesTemplates', [])
        if to_dictionary:
            return objects_
        from mstrio.modeling.schema.attribute.smart_attribute import SmartAttribute

        return [
            SmartAttribute.from_dict(source=obj, connection=self.connection)
            for obj in objects_
        ]

    def update_smart_attributes(
        self, smart_attributes: list | None = None
    ) -> list['SmartAttribute']:
        """Update the smart attributes of this attribute.

        Note:
            The PUT is a reconcile/merge: applicable entries are merged into
            the service-managed set. Passing `None` (or an empty list) lets
            the service regenerate the smart attributes.

        Args:
            smart_attributes (list, optional): list of `SmartAttribute`
                objects or dicts matching the `ms-SmartAttribute` schema

        Returns:
            A list of SmartAttribute objects after the update.
        """
        from mstrio.api import smart_attributes as smart_attributes_api

        body = (
            {}
            if smart_attributes is None
            else {'smartAttributes': _to_rest(smart_attributes)}
        )
        response = smart_attributes_api.update_data_model_smart_attributes(
            self.connection,
            data_model_id=self.data_model_id,
            attribute_id=self.id,
            body=body,
        )
        from mstrio.modeling.schema.attribute.smart_attribute import SmartAttribute

        return [
            SmartAttribute.from_dict(source=obj, connection=self.connection)
            for obj in response.json().get('smartAttributes', [])
        ]
