from functools import wraps
from json import dumps
from typing import List, Optional

from mstrio.api.changesets import commit_changeset_changes, create_changeset, delete_changeset
from mstrio.connection import Connection
from mstrio.utils.helper import (
    auto_match_args, delete_none_values, get_parallel_number, response_handler
)
from mstrio.utils.sessions import FuturesSessionWithRenewal


def unpack_information(func):

    @wraps(func)
    def unpack_information_inner(*args, **kwargs):
        if kwargs.get('body'):
            info = {
                "information": {
                    "objectId": kwargs['body'].pop('id', None),
                    "subType": kwargs['body'].pop('subType', None),
                    "name": kwargs['body'].pop('name', None),
                    "isEmbedded": kwargs['body'].pop('isEmbedded', None),
                    "description": kwargs['body'].pop('description', None),
                    "dateCreated": kwargs['body'].pop('dateCreated', None),
                    "dateModified": kwargs['body'].pop('dateModified', None),
                    "destinationFolderId": kwargs['body'].pop('destinationFolderId', None),
                    "versionId": kwargs['body'].pop('versionId', None),
                    "path": kwargs['body'].pop('path', None),
                    "acl": kwargs['body'].pop('acl', None),
                    "primaryLocale": kwargs['body'].pop('primaryLocale', None),
                }
            }
            info = delete_none_values(info, recursion=True)
            if info['information']:
                kwargs['body'].update(info)

        resp = func(*args, **kwargs)
        response_json = resp.json()

        if response_json.get('information'):
            response_json.update(response_json.pop('information'))
            response_json['id'] = response_json.pop('objectId', None)
            resp.encoding, resp._content = 'utf-8', dumps(response_json).encode('utf-8')
        return resp

    return unpack_information_inner


def changeset_decorator(func):

    @wraps(func)
    def changeset_inner(*args, **kwargs):
        connection = args[0] if args and isinstance(args[0], Connection) else kwargs["connection"]
        changeset = create_changeset(connection, schema_edit=True)
        changeset_id = changeset.json()['id']
        kwargs['changeset_id'] = changeset_id
        try:
            resp = func(*args, **kwargs)
            commit_changeset_changes(connection=connection, id=changeset_id)
        finally:
            delete_changeset(connection=connection, id=changeset_id)
        return resp

    return changeset_inner


def async_get(async_wrapper: callable, connection: Connection, ids: List[str],
              error_msg: Optional[str] = None, **kwargs) -> List[dict]:
    """Asynchronously get results of single object GET requests. GET requests
    requires to have future session param to be used with this function. Threads
    number is set automatically.

    Args:
        async_wrapper: callable async REST API wrapper function
        connection: Connection object
        ids: list of objects ids to be retrieved
        error_msg: optional error message
        kwargs: additional async wrapper arguments to be passed

    Returns:
        List of responses as a list of dicts

    Examples:
        >>> async_get(tables.get_table_async, connection, ['112233','223344'])
    """
    project_id = kwargs.get('project_id') or connection.project_id
    kwargs['project_id'] = project_id
    threads = get_parallel_number(len(ids))
    all_objects = []
    with FuturesSessionWithRenewal(connection=connection, max_workers=threads) as session:
        # Extract parameters of the api wrapper and set them using kwargs
        param_value_dict = auto_match_args(async_wrapper, kwargs,
                                           exclude=['connection', 'session', 'error_msg', 'id'])
        futures = [
            async_wrapper(session=session, connection=connection, id=id, **param_value_dict)
            for id in ids
        ]
        for f in futures:
            response = f.result()
            if not response.ok:
                response_handler(response, error_msg, throw_error=False)
            all_objects.append(response.json())

    return all_objects
