from dataclasses import dataclass
import logging
from typing import Optional

from packaging import version

from mstrio import config
from mstrio.api import subscriptions
from mstrio.connection import Connection
from mstrio.utils.entity import EntityBase, DeleteMixin
from mstrio.utils.helper import (
    delete_none_values,
    Dictable,
    exception_handler,
    fetch_objects_async,
    filter_params_for_func,
    get_valid_project_id
)
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


def list_dynamic_recipient_lists(
    connection: Connection,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters
) -> list["DynamicRecipientList"] | list[dict]:
    """Get list of Dynamic Recipient List objects or dicts with them.

    Note:
        When `project_id` is specified, `project_name` is omitted.
        If neither is specified then `project_id` from `connection` object
        is taken.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (str, optional): ID of the project to list the metrics from
        project_name (str, optional): name of the project
        to_dictionary (bool, optional): If True returns list of dictionaries,
            by default (False) returns DynamicRecipientList objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned
        **filters: parameters to filter the search on, for example `name`

    Returns:
        list with DynamicRecipientList objects or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True
    )

    msg = "Error getting Dynamic Recipient List list."
    chunk_size = 1000 if version.parse(connection.iserver_version
                                       ) >= version.parse('11.3.0300') else 1000000

    objects = fetch_objects_async(
        connection=connection,
        api=subscriptions.list_dynamic_recipient_lists,
        async_api=subscriptions.list_dynamic_recipient_lists_async,
        limit=limit,
        chunk_size=chunk_size,
        filters=filters,
        error_msg=msg,
        dict_unpack_value='listOfDynamicRecipientLists',
        project_id=project_id
    )

    if to_dictionary:
        return objects
    else:
        return [
            DynamicRecipientList.from_dict(connection=connection, source=obj) for obj in objects
        ]


@class_version_handler('11.3.0600')
class DynamicRecipientList(EntityBase, DeleteMixin):
    """Python representation of MicroStrategy DynamicRecipientList object.

    Attributes:
        id: DynamicRecipientList's ID
        name: DynamicRecipientList's name
        description: DynamicRecipientList's description
        source_report_id: Id of the Report that is the source of the
            DynamicRecipientList
        physical_address: Physical Address for the DynamicRecipientList
        linked_user: Linked User for the DynamicRecipientList
        device: Device for the DynamicRecipientList
        recipient_name: Recipient Name for the DynamicRecipientList
        notification_address: Notification Address for the DynamicRecipientList
        notification_device: Notification Device for the DynamicRecipientList
        personalization: Personalization for the DynamicRecipientList
        """

    @dataclass
    class MappingField(Dictable):
        """Python representation of a Mapping Field.

        Attributes:
            attribute_id: ID of the mapped attribute
            attribute_form_id: ID of the mapped attribute's form
            """
        attribute_id: str
        attribute_form_id: str

    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'source_report_id',
            'physical_address',
            'linked_user',
            'device',
            'recipient_name',
            'notification_address',
            'notification_device',
            'personalization'
        ): subscriptions.get_dynamic_recipient_list
    }
    _API_PATCH = {
        (
            'id',
            'name',
            'description',
            'source_report_id',
            'physical_address',
            'linked_user',
            'device',
            'recipient_name',
            'notification_address',
            'notification_device',
            'personalization'
        ): (subscriptions.update_dynamic_recipient_list, 'partial_put')
    }
    _API_DELETE = staticmethod(subscriptions.remove_dynamic_recipient_list)
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'physical_address': MappingField.from_dict,
        'linked_user': MappingField.from_dict,
        'device': MappingField.from_dict,
        'recipient_name': MappingField.from_dict,
        'notification_address': MappingField.from_dict,
        'notification_device': MappingField.from_dict,
        'personalization': MappingField.from_dict
    }

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> None:
        """Initializes a new instance of a DynamicRecipientList class

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): DynamicRecipientList's ID. Defaults to None
            name (str, optional): DynamicRecipientList's name. Defaults to None

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Raises:
            ValueError: if both `id` and `name` are not provided or if
                DynamicRecipientList with the given `name` doesn't exist.
        """
        if not id:
            if name:
                dynamic_recipient_list = self.__find_dynamic_recipient_list_by_name(
                    connection=connection, name=name
                )
                id = dynamic_recipient_list['id']
            else:
                exception_handler(msg='Must provide valid id or name', exception_type=ValueError)
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )
        super().__init__(connection=connection, object_id=id, name=name, project_id=project_id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.name = kwargs.get('name')
        self.project_id = kwargs.get('project_id')
        self.description = kwargs.get('description')
        self.source_report_id = kwargs.get('source_report_id')
        self.physical_address = DynamicRecipientList.MappingField.from_dict(paddress) if (
            paddress := kwargs.get('physical_address')
        ) else None
        self.linked_user = DynamicRecipientList.MappingField.from_dict(luser) if (
            luser := kwargs.get('linked_user')
        ) else None
        self.device = DynamicRecipientList.MappingField.from_dict(dvc) if (
            dvc := kwargs.get('device')
        ) else None
        self.recipient_name = DynamicRecipientList.MappingField.from_dict(rname) if (
            rname := kwargs.get('recipient_name')
        ) else None
        self.notification_address = DynamicRecipientList.MappingField.from_dict(naddress) if (
            naddress := kwargs.get('notification_address')
        ) else None
        self.notification_device = DynamicRecipientList.MappingField.from_dict(ndevice) if (
            ndevice := kwargs.get('notification_device')
        ) else None
        self.personalization = DynamicRecipientList.MappingField.from_dict(prsnlz) if (
            prsnlz := kwargs.get('personalization')
        ) else None

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        source_report_id: str,
        physical_address: MappingField,
        linked_user: MappingField,
        device: MappingField,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        recipient_name: Optional[MappingField] = None,
        notification_address: Optional[MappingField] = None,
        notification_device: Optional[MappingField] = None,
        personalization: Optional[MappingField] = None
    ) -> "DynamicRecipientList":
        """Create a new DynamicRecipientList with specified properties.

        Args:
            name (string): DynamicRecipientList's name
            source_report_id (string): ID of the Report that is the source of
                the DynamicRecipientList
            physical_address (MappingField): Mapping Field representing the
                Physical Address for the DynamicRecipientList
            linked_user (MappingField): Mapping Field representing the Linked
                User for the DynamicRecipientList
            device (MappingField): Mapping Field representing the Device for
                the DynamicRecipientList
            project_id (string, optional): ID of the project in which the
                DynamicRecipientList is to be created, if not provided, ID will
                be taken from project_name, if neither is provided, project will
                be extracted from the connection
            project_name (string, optional): name of the project in which the
                DynamicRecipientList is to be created
            description (string, optional): DynamicRecipientList's description
            recipient_name (MappingField, optional): Mapping Field representing
                the Recipient Name for the DynamicRecipientList
            notification_address (MappingField, optional): Mapping Field
                representing the Notification Address for the
                DynamicRecipientList
            notification_device (MappingField, optional): Mapping Field
                representing the Notification Device for the
                DynamicRecipientList
            personalization (MappingField, optional): Mapping Field representing
                the Personalization for the DynamicRecipientList

        Returns:
            DynamicRecipientList class object.
        """
        body = {
            'name': name,
            'description': description if description else None,
            'sourceReportId': source_report_id,
            'physicalAddress': physical_address.to_dict(),
            'linkedUser': linked_user.to_dict(),
            'device': device.to_dict(),
            'recipientName': recipient_name.to_dict() if recipient_name else None,
            'notificationAddress': (
                notification_address.to_dict() if notification_address else None
            ),
            'notificationDevice': (notification_device.to_dict() if notification_device else None),
            'personalization': personalization.to_dict() if personalization else None
        }
        body = delete_none_values(source=body, recursion=True)
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )
        response = subscriptions.create_dynamic_recipient_list(
            connection=connection, project_id=project_id, body=body
        ).json()

        if config.verbose:
            logger.info(
                f"Created Dynamic Recipient List named: '{name}' with ID: '{response['id']}'"
            )

        return cls.from_dict(source={**response}, connection=connection)

    def alter(
        self,
        name: Optional[str] = None,
        source_report_id: Optional[str] = None,
        physical_address: Optional[MappingField] = None,
        linked_user: Optional[MappingField] = None,
        device: Optional[MappingField] = None,
        description: Optional[str] = None,
        recipient_name: Optional[MappingField] = None,
        notification_address: Optional[MappingField] = None,
        notification_device: Optional[MappingField] = None,
        personalization: Optional[MappingField] = None
    ) -> None:
        """Alter a DynamicRecipientList's specified properties

        Note:
            If one alters the source_report_id, all existing Mapping Fields
            also need to be updated to reflect the new source report.

        Args:
            name (string, optional): DynamicRecipientList's name
            source_report_id (string, optional): ID of the Report that is the
                source of the DynamicRecipientList
            physical_address (MappingField, optional): Mapping Field
                representing the Physical Address for the DynamicRecipientList
            linked_user (MappingField, optional): Mapping Field representing
                the Linked User for the DynamicRecipientList
            device (MappingField, optional): Mapping Field representing the
                Device for the DynamicRecipientList
            description (string, optional): DynamicRecipientList's description
            recipient_name (MappingField, optional): Mapping Field representing
                the Recipient Name for the DynamicRecipientList
            notification_address (MappingField, optional): Mapping Field
                representing the Notification Address for the
                DynamicRecipientList
            notification_device (MappingField, optional): Mapping Field
                representing the Notification Device for the
                DynamicRecipientList
            personalization (MappingField, optional): Mapping Field
                representing the Personalization for the DynamicRecipientList
        """
        name = name or self.name
        description = description or self.description
        source_report_id = source_report_id or self.source_report_id
        physical_address = physical_address or self.physical_address
        linked_user = linked_user or self.linked_user
        device = device or self.device
        recipient_name = recipient_name or self.recipient_name
        notification_address = notification_address or self.notification_address
        notification_device = notification_device or self.notification_device
        personalization = personalization or self.personalization
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @staticmethod
    def __find_dynamic_recipient_list_by_name(connection: "Connection", name: str):
        dynamic_recipient_lists = list_dynamic_recipient_lists(connection=connection, name=name)

        if dynamic_recipient_lists:
            number_of_drls = len(dynamic_recipient_lists)
            if number_of_drls > 1:
                raise ValueError(
                    f"There are {number_of_drls} Dynamic Recipient Lists"
                    " with this name. Please initialize with id."
                )
            else:
                return dynamic_recipient_lists[0].to_dict()
        else:
            raise ValueError(f"There is no DynamicRecipientList with the given name: '{name}'")
