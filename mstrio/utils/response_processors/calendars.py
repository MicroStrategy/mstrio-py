import mstrio.api.calendars as calendars_api
from mstrio.connection import Connection
from mstrio.utils import helper


def _wrangle_year(source: dict, *keys) -> int | None:
    """Safely extract year from a nested dictionary, i.e.
    source[key1][key2]...[keyN]"""
    acc = source
    for key in keys:
        acc = acc.get(key, {})
    return int(acc) if acc else None


def _wrangle_entry(source: dict) -> dict:
    data = source.copy()
    if base_cal := data.get('baseCalendar'):
        data['baseCalendar'] = base_cal['objectId']

    data['calendarBeginStatic'] = _wrangle_year(data, 'calendarBegin', 'staticYear')
    data['calendarBeginOffset'] = _wrangle_year(
        data, 'calendarBegin', 'dynamicYearOffset'
    )
    data['calendarEndStatic'] = _wrangle_year(data, 'calendarEnd', 'staticYear')
    data['calendarEndOffset'] = _wrangle_year(data, 'calendarEnd', 'dynamicYearOffset')
    del data['calendarBegin']
    del data['calendarEnd']

    data['weekStartDay'] = data['weekStartDay'].lower()
    data = helper.camel_to_snake(data)

    return data


def get_calendar(connection: Connection, id: str) -> dict:
    data = calendars_api.get_calendar(connection, id).json()
    return _wrangle_entry(data)


def list_calendars(
    connection: Connection,
    subtype: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict]:
    data = calendars_api.list_calendars(
        connection=connection,
        subtype=subtype,
        offset=offset,
        limit=limit,
    ).json()['calendars']
    return [_wrangle_entry(entry) for entry in data]


def create_calendar(
    connection: Connection,
    body: dict,
):
    data = calendars_api.create_calendar(connection, body=body).json()
    return _wrangle_entry(data)


def update_calendar(
    connection: Connection,
    id: str,
    body: dict,
):
    data = calendars_api.update_calendar(connection, id, body=body).json()
    return _wrangle_entry(data)
