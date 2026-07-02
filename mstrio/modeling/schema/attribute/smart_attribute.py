import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import smart_attributes as smart_attributes_api
from mstrio.connection import Connection
from mstrio.utils.helper import Dictable, get_objects_id
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.schema.attribute.attribute import Attribute

logger = logging.getLogger(__name__)


@dataclass
class SmartAttribute(Dictable):
    """Object that describes a smart attribute derived from a base attribute.

    Attributes:
        object_id: ID of the smart attribute object
        subtype: subtype of the smart attribute object
        name: name of the smart attribute
        definition: definition of the smart attribute
    """

    object_id: str | None = None
    subtype: str | None = None
    name: str | None = None
    definition: dict | None = None


def _get_attribute_id(attribute: 'Attribute | str') -> str:
    # Import lazily to avoid a circular import: this module lives inside
    # the `mstrio.modeling.schema.attribute` package which `attribute.py`
    # is part of.
    from mstrio.modeling.schema.attribute.attribute import Attribute

    return get_objects_id(attribute, Attribute)


def _unwrap_smart_attributes(
    data: dict, root_key: str, to_dictionary: bool
) -> list[SmartAttribute] | list[dict]:
    elements = data.get(root_key) or []
    if to_dictionary:
        return elements
    return [SmartAttribute.from_dict(element) for element in elements]


@method_version_handler('11.6.0100')
def list_smart_attributes(
    connection: Connection,
    attribute: 'Attribute | str',
    to_dictionary: bool = False,
    changeset_id: str | None = None,
) -> list[SmartAttribute] | list[dict]:
    """Get a list of references to all smart attributes derived from
    the base attribute.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        attribute (Attribute, str): `Attribute` object or ID of the base
            attribute
        to_dictionary (bool, optional): If True returns a list of
            dictionaries, otherwise returns a list of `SmartAttribute`
            objects
        changeset_id (str, optional): ID of a changeset. If provided, smart
            attributes are read in the context of that changeset.

    Returns:
        A list of `SmartAttribute` objects or dictionaries representing
        smart attributes.
    """
    attribute_id = _get_attribute_id(attribute)
    response = smart_attributes_api.list_smart_attributes(
        connection=connection,
        attribute_id=attribute_id,
        changeset_id=changeset_id,
    )
    return _unwrap_smart_attributes(response.json(), 'smartAttributes', to_dictionary)


@method_version_handler('11.6.0100')
def list_smart_attribute_templates(
    connection: Connection,
    attribute: 'Attribute | str',
    to_dictionary: bool = False,
    changeset_id: str | None = None,
) -> list[SmartAttribute] | list[dict]:
    """Get a list of smart attribute templates that can be created
    for the base attribute.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        attribute (Attribute, str): `Attribute` object or ID of the base
            attribute
        to_dictionary (bool, optional): If True returns a list of
            dictionaries, otherwise returns a list of `SmartAttribute`
            objects
        changeset_id (str, optional): ID of a changeset. If provided,
            templates are read in the context of that changeset.

    Returns:
        A list of `SmartAttribute` objects or dictionaries representing
        smart attribute templates.
    """
    attribute_id = _get_attribute_id(attribute)
    response = smart_attributes_api.list_smart_attribute_templates(
        connection=connection,
        attribute_id=attribute_id,
        changeset_id=changeset_id,
    )
    return _unwrap_smart_attributes(
        response.json(), 'smartAttributesTemplates', to_dictionary
    )


@method_version_handler('11.6.0100')
def update_smart_attributes(
    connection: Connection,
    attribute: 'Attribute | str',
    smart_attributes: list[SmartAttribute | dict] | None = None,
) -> list[SmartAttribute]:
    """Reconcile the service-managed smart attributes for the base
    attribute based on its key form.

    Note:
        This operation is a reconcile/merge, not a wholesale replacement.
        If `smart_attributes` entries are provided, applicable entries are
        merged into the service-managed set so fields such as `object_id`,
        `name` and `hidden` are respected. Omitted existing applicable
        entries are kept as-is; omitted missing applicable entries are
        auto-created, and existing non-applicable smart attributes may be
        removed. Passing `None` or an empty list lets the service
        regenerate the set.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        attribute (Attribute, str): `Attribute` object or ID of the base
            attribute
        smart_attributes (list, optional): list of `SmartAttribute` objects
            or dictionaries to merge into the service-managed set. If
            `None` or empty, the service regenerates the smart attributes.

    Returns:
        A list of `SmartAttribute` objects representing the reconciled
        smart attributes.
    """
    attribute_id = _get_attribute_id(attribute)
    body = {}
    if smart_attributes:
        body['smartAttributes'] = [
            item.to_dict() if isinstance(item, SmartAttribute) else item
            for item in smart_attributes
        ]
    response = smart_attributes_api.update_smart_attributes(
        connection=connection,
        attribute_id=attribute_id,
        body=body,
    )
    result = _unwrap_smart_attributes(
        response.json(), 'smartAttributes', to_dictionary=False
    )
    if config.verbose:
        logger.info(
            "Successfully reconciled smart attributes for attribute "
            f"with ID: '{attribute_id}'."
        )
    return result
