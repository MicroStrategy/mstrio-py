from functools import wraps
from json import dumps

from mstrio.api.changesets import commit_changeset_changes, create_changeset, delete_changeset
from mstrio.connection import Connection
from mstrio.utils.helper import delete_none_values


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
