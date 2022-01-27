from typing import Callable, Optional

from mstrio.api import monitors
from mstrio.server.node import Node
from mstrio.utils.helper import _prepare_objects, auto_match_args, response_handler
from mstrio.utils.sessions import FuturesSessionWithRenewal


def all_nodes_async(connection, async_api: Callable, filters: dict, error_msg: str,
                    unpack_value: Optional[str] = None, limit: Optional[int] = None, **kwargs):
    """Return list of objects fetched async using wrappers in monitors.py
    """

    node = kwargs.get('node_name')
    if not node:
        nodes_response = monitors.get_node_info(connection).json()
        all_nodes = nodes_response['nodes']
        node_names = [node['name'] for node in all_nodes if node['status'] == 'running']
    else:
        node = node.name if isinstance(node, Node) else node
        if isinstance(node, str):
            node_names = [node]

    if kwargs.get('error_msg'):
        error_msg = kwargs.get('error_msg')

    with FuturesSessionWithRenewal(connection=connection, max_workers=8) as session:
        # Extract parameters of the api wrapper and set them using kwargs
        param_value_dict = auto_match_args(
            async_api,
            kwargs,
            exclude=['connection', 'limit', 'offset', 'future_session', 'error_msg', 'node_name'])
        futures = [
            async_api(future_session=session, connection=connection, node_name=n,
                      **param_value_dict)
            for n in node_names
        ]
        objects = []
        for f in futures:
            response = f.result()
            if not response.ok:
                response_handler(response, error_msg, throw_error=False)
            else:
                obj = _prepare_objects(response.json(), filters, unpack_value)
                objects.extend(obj)
    if limit:
        objects = objects[:limit]
    return objects
