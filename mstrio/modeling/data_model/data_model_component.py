import logging
from typing import Callable

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.modeling.data_model.helpers import unpack_information_dict
from mstrio.utils.entity import EntityBase

logger = logging.getLogger(__name__)


class DataModelComponent(EntityBase):
    """Base class for objects living inside a Mosaic data model.

    Components (tables, attributes, metrics, fact metrics, security filters)
    are addressed by the pair (`data_model_id`, `id`) and are managed through
    the changeset-scoped Modeling-Service endpoints
    `/api/model/dataModels/{dataModelId}/...`.

    Class attributes (set per subclass):
        _ACL_SUBTYPE (str): the `subType` query param value used by the
            object ACL / translations endpoints, e.g. 'logical_table'
        _GET_FUNC (Callable): api function fetching a single component
        _DELETE_FUNC (Callable): api function deleting a single component
        _ID_KWARG (str): name of the component id keyword argument of
            `_GET_FUNC` / `_DELETE_FUNC`, e.g. 'table_id'
    """

    _ACL_SUBTYPE: str | None = None
    _GET_FUNC: Callable | None = None
    _DELETE_FUNC: Callable | None = None
    _ID_KWARG: str = 'id'
    _DELETE_PROMPT_ANSWER: str = 'Y'

    def __init__(self, connection: Connection, data_model_id: str, id: str) -> None:
        """Initialize the component object.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model_id (str): ID of the data model containing the component
            id (str): ID of the component
        """
        if not data_model_id:
            raise ValueError("Please specify the 'data_model_id' parameter.")
        if not id:
            raise ValueError("Please specify the 'id' parameter.")
        self._init_variables(connection=connection, id=id, data_model_id=data_model_id)
        if config.fetch_on_init and type(self)._GET_FUNC is not None:
            self.fetch()
        if config.verbose:
            logger.info(self)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.data_model_id = kwargs.get('data_model_id', default_value)
        self.description = kwargs.get('description', default_value)
        self._sub_type = kwargs.get('sub_type', default_value)

    def fetch(self, attr: str | None = None) -> None:
        """Fetch the latest component definition from the I-Server.

        Args:
            attr (str, optional): ignored; present for compatibility with the
                `EntityBase` interface. The whole definition is always fetched.
        """
        func = type(self)._GET_FUNC
        if func is None:
            raise NotImplementedError(
                f"{type(self).__name__} does not support fetching."
            )
        response = func(
            self.connection, id=self.data_model_id, **{self._ID_KWARG: self.id}
        )
        data = unpack_information_dict(response.json())
        self._set_object_attributes(**data)
        self._add_to_fetched('id')

    def delete(self, force: bool = False) -> bool:
        """Delete the component from the data model.

        Args:
            force (bool, optional): if True, no additional prompt will be
                shown before deleting the object

        Returns:
            True on success. False otherwise.
        """
        func = type(self)._DELETE_FUNC
        if func is None:
            raise NotImplementedError(
                f"{type(self).__name__} does not support deleting."
            )
        object_name = type(self).__name__
        if not force:
            message = (
                f"Are you sure you want to delete {object_name} "
                f"'{self.name}' with ID: {self._id}? [Y/N]: "
            )
            if input(message) != self._DELETE_PROMPT_ANSWER:
                return False
        response = func(
            self.connection, id=self.data_model_id, **{self._ID_KWARG: self.id}
        )
        if response.ok and config.verbose:
            logger.info(f"Successfully deleted {object_name} with ID: '{self._id}'.")
        return response.ok

    def get_acl(self) -> dict:
        """Get the access control list of the component.

        Note:
            The endpoint returns a 500 error when the `subType` query param is
            missing and silently returns a consistent-but-wrong facet when it
            is wrong; the correct value is derived from `_ACL_SUBTYPE`.

        Returns:
            Dictionary with the component's ACL definition.
        """
        return data_models.get_data_model_object_acl(
            self.connection,
            id=self.data_model_id,
            object_id=self.id,
            sub_type=self._ACL_SUBTYPE,
        ).json()

    def update_acl(self, acl: dict) -> dict:
        """Update the access control list of the component.

        Note:
            The update is a WHOLESALE REPLACEMENT: trustees omitted from `acl`
            lose their entries. Read the current ACL with `get_acl()`, modify
            it and send the full mapping back. The rights mask `255` is the
            server's magic "Full Control" value.

        Args:
            acl (dict): mapping of trustee ID to rights definition, e.g.
                `{'<trusteeId>': {'granted': 255, 'denied': 0,
                'subType': 'user', 'inheritable': True}}`. May also be passed
                already wrapped as `{'acl': {...}}`.

        Returns:
            Dictionary with the updated ACL definition.
        """
        body = acl if 'acl' in acl else {'acl': acl}
        return data_models.update_data_model_object_acl(
            self.connection,
            id=self.data_model_id,
            object_id=self.id,
            sub_type=self._ACL_SUBTYPE,
            body=body,
        ).json()

    def get_translations(self) -> dict:
        """Get the translations of the component.

        Returns:
            Dictionary with the component's translations.
        """
        return data_models.get_data_model_object_translations(
            self.connection,
            id=self.data_model_id,
            object_id=self.id,
            sub_type=self._ACL_SUBTYPE,
        ).json()

    def update_translations(self, translations: dict) -> dict:
        """Update the translations of the component.

        Args:
            translations (dict): translations definition to send

        Returns:
            Dictionary with the updated translations.
        """
        return data_models.update_data_model_object_translations(
            self.connection,
            id=self.data_model_id,
            object_id=self.id,
            sub_type=self._ACL_SUBTYPE,
            body=translations,
        ).json()

    @classmethod
    def _from_api_source(
        cls, connection: Connection, data_model_id: str, source: dict
    ) -> 'DataModelComponent':
        """Build a component from a raw REST payload, injecting the data
        model scope."""
        return cls.from_dict(
            source={**unpack_information_dict(source), 'data_model_id': data_model_id},
            connection=connection,
        )

    @property
    def sub_type(self) -> str | None:
        """String literal identifying the metadata subtype of the object."""
        return self._sub_type
