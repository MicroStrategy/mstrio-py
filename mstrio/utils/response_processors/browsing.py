from mstrio.api import browsing as browsing_api
from mstrio.connection import Connection


def get_objects_from_quick_search(
    connection: 'Connection',
    body: dict,
    include_ancestors: bool = False,
    show_navigation_path: bool = False,
    fields: str | None = None,
):
    return (
        browsing_api.get_objects_from_quick_search(
            connection=connection,
            body=body,
            include_ancestors=include_ancestors,
            show_navigation_path=show_navigation_path,
            fields=fields,
        )
        .json()
        .get('result')
    )


def get_search_object(
    connection: 'Connection',
    id: str,
):
    result_dict: dict = browsing_api.get_search_object(
        connection=connection, id=id
    ).json()

    time_range = result_dict.pop('timeRange', None)
    date_filter_type = result_dict.pop('dateFilterType', None)
    if date_filter_type and date_filter_type.upper() == 'CREATED':
        result_dict['dateCreatedQuery'] = time_range
    elif date_filter_type and date_filter_type.upper() == 'MODIFIED':
        result_dict['dateModifiedQuery'] = time_range

    search_visibility = result_dict.pop('visibility', None)
    if search_visibility and search_visibility.upper() == 'VISIBLE':
        result_dict['includeHidden'] = False
    elif search_visibility and search_visibility.upper() == 'ALL':
        result_dict['includeHidden'] = True

    if 'ownerId' in result_dict:
        result_dict['ownerQuery'] = result_dict.pop('ownerId')

    return result_dict
