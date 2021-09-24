from datetime import datetime
from enum import Enum
from functools import wraps
import pytz


class DatetimeFormats(Enum):
    FULLDATETIME = '%Y-%m-%dT%H:%M:%S.%f%z'
    DATE = '%Y-%m-%d'
    YMDHMSmS = '%Y-%m-%dT%H:%M:%S.%f%z'
    YMDHMS = '%Y-%m-%dT%H:%M:%S%z'
    YMD = '%Y-%m-%d'


def str_to_datetime(date: str, format_str: str) -> datetime:
    """Change date format to datetime, based on `format_str` provided.
    If `date` is already a datetime object, return it. Make the date aware."""
    if date is None:
        return date
    try:
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
    except (TypeError, ValueError):
        print('Error')
        return None


def _return_with_miliseconds(func):
    """If the date has miliseconds, return only 3 decimal places. Older servers
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
def datetime_to_str(date: datetime, format_str: str) -> str:
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
        format = string_to_date_map[f'_{name}'].value if isinstance(
            string_to_date_map[f'_{name}'], DatetimeFormats) else string_to_date_map[f'_{name}']
        return func(date, format)
    elif name in string_to_date_map:
        format = string_to_date_map[name].value if isinstance(
            string_to_date_map[name], DatetimeFormats) else string_to_date_map[name]
        return func(date, format)
    return date


def map_str_to_datetime(name: str, date: str, string_to_date_map: dict,
                        only_datetimefomat: bool = True) -> datetime:
    """Change date format to datetime, based on `string_to_date_map`
    conversion dict. All occurances of `DATETIMEFORMAT` Enum in
    `string_to_date_map` are converted to coresponding string values.
    If name is not found in `string_to_date_map`, returns date without changes.
    """
    return _solve_prefix_and_convert_date(str_to_datetime, name, date, string_to_date_map,
                                          only_datetimefomat)


def map_datetime_to_str(name: str, date: datetime, string_to_date_map: dict,
                        only_datetimefomat: bool = True) -> str:
    """Change date format to string, based on `string_to_date_map`
    conversion dict. All occurances of `DATETIMEFORMAT` Enum in
    `string_to_date_map` are converted to coresponding string values.
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
