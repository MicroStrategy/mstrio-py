from collections.abc import Callable

from mstrio.api import monitors
from mstrio.utils.helper import _prepare_objects, auto_match_args, get_response_json
from mstrio.utils.sessions import FuturesSessionWithRenewal


def all_nodes_async(
    connection,
    async_api: Callable,
    filters: dict,
    error_msg: str,
    unpack_value: str | None = None,
    limit: int | None = None,
    **kwargs,
):
    """Return list of objects fetched async using wrappers in monitors.py"""

    node = kwargs.get('node_name')
    if not node:
        nodes_response = monitors.get_node_info(connection).json()
        all_nodes = nodes_response['nodes']
        node_names = [node['name'] for node in all_nodes if node['status'] == 'running']
    else:
        from mstrio.server.node import Node

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
            exclude=[
                'connection',
                'limit',
                'offset',
                'future_session',
                'error_msg',
                'node_name',
            ],
        )
        futures = [
            async_api(
                future_session=session,
                node_name=n,
                **param_value_dict,
            )
            for n in node_names
        ]
        objects = []
        for f in futures:
            response = f.result()
            res_json = get_response_json(response, msg=error_msg, throw_error=False)
            if res_json:
                obj = _prepare_objects(res_json, filters, unpack_value)
                objects.extend(obj)

    if limit:
        objects = objects[:limit]
    return objects
