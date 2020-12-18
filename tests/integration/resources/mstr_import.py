from copy import copy
from operator import itemgetter

from mstrio.cube import Cube
from mstrio.report import Report


def get_cube_dataframe(connection, cube_id,
                       attribute_filter=None,
                       metric_filter=None,
                       element_filter=None,
                       parallel=True):
    cube = Cube(connection=connection,
                cube_id=cube_id,
                parallel=parallel)
    cube.apply_filters(attributes=attribute_filter,
                       metrics=metric_filter,
                       attr_elements=element_filter)
    df = cube.to_dataframe()
    return df


def get_report_dataframe(connection, report_id,
                         attribute_filter=None,
                         metric_filter=None,
                         element_filter=None,
                         parallel=True):
    report = Report(connection=connection,
                    report_id=report_id,
                    parallel=parallel)
    report.apply_filters(attributes=attribute_filter,
                         metrics=metric_filter,
                         attr_elements=element_filter)
    df = report.to_dataframe()
    return df


def filter_dict(d, keys, how='drop'):
    d = copy(d)
    if how == 'drop':
        for col in keys:
            del d[col]
        return d
    elif how == 'keep':
        for col in set(d.keys()).difference(keys):
            del d[col]
        return d
    else:
        raise ValueError("Only 'drop' and 'keep' values permitted for the 'keep' flag")


def view_filter_dict(d, values, how='drop'):
    d = copy(d)
    positives = set()
    for key in d.keys():
        for i, v in enumerate(d[key]):
            if v in values:
                positives.add(i)
    if how == 'drop':
        positives = set(range(len(d[key]))).difference(positives)
        for key in d.keys():
            d[key] = list(itemgetter(*positives)(d[key]))
        return d
    elif how =='keep':
        for key in d.keys():
            d[key] = [itemgetter(*positives)(d[key])]
        return d
    else:
        raise ValueError("Only 'drop' and 'keep' values permitted for the 'keep' flag")
