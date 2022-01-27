from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Union
import json
import pytz


class DatetimeFormats(Enum):
    FULLDATETIME = '%Y-%m-%dT%H:%M:%S.%f%z'
    DATE = '%Y-%m-%d'
    YMDHMSmS = '%Y-%m-%dT%H:%M:%S.%f%z'
    YMDHMS = '%Y-%m-%dT%H:%M:%S%z'
    YMD = '%Y-%m-%d'


def str_to_datetime(date: str, format_str: str) -> Union[datetime, None]:
    """Change date format to datetime, based on `format_str` provided.
    If `date` is already a datetime object, return it. Make the date aware."""
    if date is None:
        return date

    if not isinstance(date, datetime):
        if format_str.find('%z') != -1:
            # Localization needed. Check if provided.
            if date[-1] == 'Z':
                date = date[:-1]
                format_str = format_str[:-2]
            elif date.find('+') == -1:
                format_str = format_str[:-2]
        date = datetime.strptime(date, format_str)
    try:  # Localize to utc if not yet localized
        return pytz.utc.localize(date)
    except ValueError:  # Already localized
        return date


def _return_with_miliseconds(func):
    """If the date has milliseconds, return only 3 decimal places. Older servers
    need this to work. New can parse both 3 and 6 decimal places."""

    @wraps(func)
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        if isinstance(res, str) and res.find('.') != -1:
            plus_pos = res.find('+')
            res = f"{res[:res.find('.') + 4]}{res[plus_pos:] if plus_pos != -1 else ''}"
        return res

    return inner


@_return_with_miliseconds
def datetime_to_str(date: datetime, format_str: str) -> Union[str, None]:
    """Get date string from datetime, based on `format_str` provided.
    If `date` is already a string, return it. Make the date aware."""
    if isinstance(date, str):
        return date
    try:
        # We need the date to be aware, or the string won't be accepted by API
        try:
            return pytz.utc.localize(date).strftime(format_str)
        except ValueError:  # Already localized
            return date.strftime(format_str)
    except (TypeError, AttributeError):
        return None


def _get_only_datetimeformat_map(string_to_date_map: dict) -> dict:
    """Return all entries that are of `DATETIMEFORMAT` enum type."""
    return {
        key: value
        for (key, value) in string_to_date_map.items()
        if isinstance(value, DatetimeFormats)
    }


def _solve_prefix_and_convert_date(func, name: str, date: str, string_to_date_map: dict,
                                   only_datetimefomat: bool = True):
    if only_datetimefomat:
        string_to_date_map = _get_only_datetimeformat_map(string_to_date_map)
    if f'_{name}' in string_to_date_map:
        date_format = string_to_date_map[f'_{name}'].value if isinstance(
            string_to_date_map[f'_{name}'], DatetimeFormats) else string_to_date_map[f'_{name}']
        return func(date, date_format)
    elif name in string_to_date_map:
        date_format = string_to_date_map[name].value if isinstance(
            string_to_date_map[name], DatetimeFormats) else string_to_date_map[name]
        return func(date, date_format)
    return date


def map_str_to_datetime(name: str, date: str, string_to_date_map: dict,
                        only_datetimefomat: bool = True) -> datetime:
    """Change date format to datetime, based on `string_to_date_map`
    conversion dict. All occurrences of `DATETIMEFORMAT` Enum in
    `string_to_date_map` are converted to corresponding string values.
    If name is not found in `string_to_date_map`, returns date without changes.
    """
    return _solve_prefix_and_convert_date(str_to_datetime, name, date, string_to_date_map,
                                          only_datetimefomat)


def map_datetime_to_str(name: str, date: datetime, string_to_date_map: dict,
                        only_datetimefomat: bool = True) -> str:
    """Change date format to string, based on `string_to_date_map`
    conversion dict. All occurrences of `DATETIMEFORMAT` Enum in
    `string_to_date_map` are converted to corresponding string values.
    If name is not found in `string_to_date_map`, returns date without changes.
    """
    return _solve_prefix_and_convert_date(datetime_to_str, name, date, string_to_date_map,
                                          only_datetimefomat)


def bulk_str_to_datetime(source: dict, string_to_date_map: dict,
                         only_datetimefomat: bool = True) -> dict:
    """Change all dates from `source` found in `string_to_date_map`
    to datetime format. If parameter is not found in `string_to_date_map`,
    it is returned without changes."""
    for key, val in source.items():
        source[key] = map_str_to_datetime(key, val, string_to_date_map, only_datetimefomat)
    return source


def bulk_datetime_to_str(source: dict, string_to_date_map: dict,
                         only_datetimefomat: bool = True) -> dict:
    """Change all dates from `source` found in `string_to_date_map`
    to string format. If parameter is not found in `string_to_date_map`,
    it is returned without changes."""
    for key, val in source.items():
        source[key] = map_datetime_to_str(key, val, string_to_date_map, only_datetimefomat)
    return source


def override_datetime_format(original_format: str, expected_format: str, fields: tuple,
                             to_unpack=None):
    """A decorator designed to override the datetime format
    of some dates in responses from REST server as they can be
    a bit crazy sometimes (e.g. two different formats for one object)

    Args:
        original_format: original format of a datetime
        expected_format: the format you want to convert to
        fields: fields of the object - e.g. dateModified, dateCreated
        to_unpack: when response returns a list of objects
            probably they need to be unpacked
    """
    def decorator_datetime(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            response = func(*args, **kwargs)
            response_json = response.json()
            try:
                iterable = response_json[to_unpack] if to_unpack else [response_json]
            except KeyError:
                iterable = []
            for obj in iterable:
                for field in fields:
                    datetime_obj = str_to_datetime(obj[field], original_format)
                    obj[field] = datetime_to_str(datetime_obj, expected_format)
            response.encoding, response._content = 'utf-8', json.dumps(response_json).encode(
                'utf-8')
            return response
        return wrapped
    return decorator_datetime
