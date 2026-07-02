import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.modeling.data_model.data_model_component import DataModelComponent
from mstrio.modeling.data_model.helpers import unpack_information_dict
from mstrio.utils.helper import delete_none_values
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.data_model.data_model import DataModel
    from mstrio.users_and_groups import UserOrGroup

logger = logging.getLogger(__name__)

_USER_SUBTYPE = 8704
_USER_GROUP_SUBTYPE = 8705


@method_version_handler('11.6.0100')
def list_data_model_security_filters(
    connection: Connection,
    data_model: 'DataModel | str',
    to_dictionary: bool = False,
    limit: int | None = None,
    offset: int | None = None,
    changeset_id: str | None = None,
) -> list['DataModelSecurityFilter'] | list[dict]:
    """Get a list of security filters of a Mosaic data model (Modeling-Service
    collection).

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        data_model (DataModel | str): data model object or its ID
        to_dictionary (bool, optional): if True, return security filters as
            a list of dicts
        limit (int, optional): limit the number of elements returned
        offset (int, optional): starting point within the collection
        changeset_id (str, optional): ID of an existing changeset to read from

    Returns:
        A list of DataModelSecurityFilter objects or dictionaries
        representing them.
    """
    data_model_id = data_model if isinstance(data_model, str) else data_model.id
    security_filters = (
        data_models.list_data_model_security_filters(
            connection,
            id=data_model_id,
            changeset_id=changeset_id,
            offset=offset,
            limit=limit,
        )
        .json()
        .get('securityFilters', [])
    )
    if limit:
        security_filters = security_filters[:limit]
    if to_dictionary:
        return [unpack_information_dict(sf) for sf in security_filters]
    return [
        DataModelSecurityFilter._from_api_source(connection, data_model_id, sf)
        for sf in security_filters
    ]


@class_version_handler('11.6.0100')
class DataModelSecurityFilter(DataModelComponent):
    """Python representation of a security filter of a Mosaic data model.

    Security filter definitions are managed through the changeset-scoped
    Modeling-Service endpoints, while member assignment uses the runtime
    `/api/dataModels/{id}/securityFilters/{sfId}/members` endpoint. Member
    assignment requires the security filter's creation changeset to be
    committed first (this happens automatically, as every write api call
    commits its own changeset).
    """

    _ACL_SUBTYPE = 'md_security_filter'
    _GET_FUNC = staticmethod(data_models.get_data_model_security_filter)
    _DELETE_FUNC = staticmethod(data_models.delete_data_model_security_filter)
    _ID_KWARG = 'security_filter_id'

    @classmethod
    def create(
        cls,
        connection: Connection,
        data_model: 'DataModel | str',
        name: str,
        qualification: dict,
        top_level: list | None = None,
        bottom_level: list | None = None,
        description: str | None = None,
        show_filter_tokens: bool | None = None,
        show_expression_as: str | None = None,
    ) -> 'DataModelSecurityFilter':
        """Create a new security filter in a Mosaic data model.

        Note:
            The object subtype MUST be `md_security_filter` (it is set
            automatically; plain `security_filter` is rejected). Two verified
            qualification tree shapes:

            - `predicate_form_qualification` - the form reference inside must
              carry `subType: 'attribute_form_system'`
            - `predicate_element_list` - with
              `elements: [{'display': ..., 'elementId': ...}]` and
              `function: 'in'`

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model (DataModel | str): data model object or its ID
            name (str): name of the security filter
            qualification (dict): filter definition written as an expression
                tree over predicate nodes (`ms-Expression` schema)
            top_level (list, optional): top level attributes of the filter
            bottom_level (list, optional): bottom level attributes of the
                filter
            description (str, optional): description of the security filter
            show_filter_tokens (bool, optional): whether to show filter
                expressions as tokens in the response
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')

        Returns:
            DataModelSecurityFilter object.
        """
        data_model_id = data_model if isinstance(data_model, str) else data_model.id
        body = {
            'name': name,
            'description': description,
            'subType': 'md_security_filter',
            'qualification': qualification,
            'topLevel': top_level or [],
            'bottomLevel': bottom_level or [],
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.create_data_model_security_filter(
            connection,
            id=data_model_id,
            body=body,
            show_filter_tokens=show_filter_tokens,
            show_expression_as=show_expression_as,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created security filter named: '{name}' with "
                f"ID: '{response.get('id')}' in data model '{data_model_id}'."
            )
        return cls._from_api_source(connection, data_model_id, response)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        qualification: dict | None = None,
        top_level: list | None = None,
        bottom_level: list | None = None,
    ) -> None:
        """Alter the security filter.

        Note:
            The underlying endpoint is a PUT (full replace). This method
            first fetches the current definition and merges the requested
            changes into it before sending, so unspecified fields are
            preserved.

        Args:
            name (str, optional): new name of the security filter
            description (str, optional): new description
            qualification (dict, optional): new filter definition
            top_level (list, optional): new top level attributes
            bottom_level (list, optional): new bottom level attributes
        """
        current = (
            type(self)
            ._GET_FUNC(
                self.connection, id=self.data_model_id, security_filter_id=self.id
            )
            .json()
        )
        body = {key: val for key, val in current.items() if key != 'id'}
        changes = {
            'name': name,
            'description': description,
            'qualification': qualification,
            'topLevel': top_level,
            'bottomLevel': bottom_level,
        }
        body.update(delete_none_values(changes, recursion=False))
        response = data_models.update_data_model_security_filter(
            self.connection,
            id=self.data_model_id,
            security_filter_id=self.id,
            body=body,
        )
        self._set_object_attributes(**unpack_information_dict(response.json()))
        if config.verbose:
            logger.info(
                f"Successfully altered security filter with ID: '{self.id}' "
                f"in data model '{self.data_model_id}'."
            )

    def list_members(
        self,
        offset: int | None = None,
        limit: int | None = None,
        to_dictionary: bool = True,
    ) -> dict:
        """List users and user groups the security filter is assigned to
        (runtime endpoint).

        Args:
            offset (int, optional): starting point within the collection
            limit (int, optional): limit the number of elements returned
            to_dictionary (bool, optional): if True (default), members are
                returned as plain dicts; if False, they are hydrated into
                `User` / `UserGroup` objects

        Returns:
            Dictionary with keys `users`, `user_groups`, `total_users` and
            `total_user_groups`. The totals are authoritative and may exceed
            the number of returned members when paging.
        """
        data = data_models.get_security_filter_members(
            self.connection,
            id=self.data_model_id,
            security_filter_id=self.id,
            offset=offset,
            limit=limit,
        ).json()
        members = data.get('users', []) + data.get('userGroups', [])
        users = [m for m in members if m.get('subtype') != _USER_GROUP_SUBTYPE]
        user_groups = [m for m in members if m.get('subtype') == _USER_GROUP_SUBTYPE]
        if not to_dictionary:
            from mstrio.users_and_groups import User, UserGroup

            users = [
                User.from_dict(source=user, connection=self.connection)
                for user in users
            ]
            user_groups = [
                UserGroup.from_dict(source=group, connection=self.connection)
                for group in user_groups
            ]
        return {
            'users': users,
            'user_groups': user_groups,
            'total_users': data.get('totalUsers'),
            'total_user_groups': data.get('totalUserGroups'),
        }

    def _update_members(self, op: str, members: list['UserOrGroup']) -> bool:
        """Send a member operation. `op` must be one of the one-word
        camelCase verbs `addElements`, `removeElements` or `replaceElements`
        (plain 'add' is rejected by the server) and the path must be exactly
        `/Members`."""
        from mstrio.users_and_groups import User, UserGroup

        member_ids = [
            member.id if isinstance(member, (User, UserGroup)) else member
            for member in members
        ]
        body = {'operationList': [{'op': op, 'path': '/Members', 'value': member_ids}]}
        response = data_models.update_security_filter_members(
            self.connection,
            id=self.data_model_id,
            security_filter_id=self.id,
            body=body,
        )
        if response.ok and config.verbose:
            logger.info(
                f"Successfully updated members of security filter with ID: "
                f"'{self.id}' (operation: '{op}')."
            )
        return response.ok

    def add_members(self, members: list['UserOrGroup']) -> bool:
        """Assign users or user groups to the security filter.

        Args:
            members (list): list of `User` / `UserGroup` objects or their IDs

        Returns:
            True on success (the endpoint returns 204 with an empty body).
        """
        return self._update_members('addElements', members)

    def remove_members(self, members: list['UserOrGroup']) -> bool:
        """Unassign users or user groups from the security filter.

        Args:
            members (list): list of `User` / `UserGroup` objects or their IDs

        Returns:
            True on success (the endpoint returns 204 with an empty body).
        """
        return self._update_members('removeElements', members)

    def replace_members(self, members: list['UserOrGroup']) -> bool:
        """Replace the whole member list of the security filter.

        Args:
            members (list): list of `User` / `UserGroup` objects or their IDs

        Returns:
            True on success (the endpoint returns 204 with an empty body).
        """
        return self._update_members('replaceElements', members)
