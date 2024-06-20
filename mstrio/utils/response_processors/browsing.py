from mstrio.api import browsing as browsing_api
from mstrio.connection import Connection


def get_search_objects(
    connection: 'Connection',
    body: dict,
    include_ancestors: bool = False,
    show_navigation_path: bool = False,
    fields: str | None = None,
):
    return (
        browsing_api.get_search_objects(
            connection=connection,
            body=body,
            include_ancestors=include_ancestors,
            show_navigation_path=show_navigation_path,
            fields=fields,
        )
        .json()
        .get('result')
    )
