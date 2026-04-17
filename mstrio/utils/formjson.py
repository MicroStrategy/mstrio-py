from typing import TYPE_CHECKING

from mstrio.helpers import NotSupportedError

if TYPE_CHECKING:
    import pandas as pd


def map_data_type(datatype):
    """Converts `pandas dtype` into REST type expectation."""

    ret = {
        'object': 'STRING',
        'str': 'STRING',
        'string': 'STRING',
        'string[python]': 'STRING',
        'int64': 'INTEGER',
        'int32': 'INTEGER',
        'float64': 'DOUBLE',
        'float32': 'DOUBLE',
        'bool': 'BOOL',
        'datetime64[ns]': 'DATETIME',
        'date': 'DATE',
        'time': 'TIME',
    }.get(str(datatype))

    if not ret:
        raise NotSupportedError(f"'{datatype}' is an unsupported datatype.")

    return ret


def formjson(
    df: 'pd.DataFrame',
    table_name: str,
    as_metrics: list[str] | None = None,
    as_attributes: list[str] | None = None,
):
    def _form_column_headers(_col_names, _col_types):
        return [{'name': n, 'dataType': t} for n, t in zip(_col_names, _col_types)]

    def _form_attribute_list(_attributes):
        return [
            {
                'name': n,
                'attributeForms': [
                    {
                        'category': 'ID',
                        'expressions': [{'formula': table_name + "." + n}],
                    }
                ],
            }
            for n in _attributes
        ]

    def _form_metric_list(_metrics):
        return [
            {
                'name': n,
                'dataType': 'number',
                'expressions': [{'formula': table_name + "." + n}],
            }
            for n in _metrics
        ]

    col_names = list(df.columns)
    col_types = list(map(map_data_type, list(df.dtypes.values)))

    # Adjust attributes/metrics mapping if new mappings were provided in
    # as_metrics and as_attributes
    attributes = []
    metrics = []
    for _name, _type in zip(col_names, col_types):
        if _type in ['DOUBLE', 'INTEGER']:  # metric
            if as_attributes is not None and _name in as_attributes:
                attributes.append(_name)
            else:
                metrics.append(_name)
        else:  # attribute
            if as_metrics is not None and _name in as_metrics:
                metrics.append(_name)
            else:
                attributes.append(_name)

    column_headers = _form_column_headers(_col_names=col_names, _col_types=col_types)
    attribute_list = _form_attribute_list(_attributes=attributes)
    metric_list = _form_metric_list(_metrics=metrics)

    return column_headers, attribute_list, metric_list
