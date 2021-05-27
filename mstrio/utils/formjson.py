def _map_data_type(datatype):
    if datatype == 'object':
        return "STRING"
    elif datatype in ['int64', 'int32']:
        return "INTEGER"
    elif datatype in ['float64', 'float32']:
        return "DOUBLE"
    elif datatype == 'bool':
        return "BOOL"
    elif datatype == 'datetime64[ns]':
        return 'DATETIME'


def formjson(df, table_name, as_metrics=None, as_attributes=None):

    def _form_column_headers(_col_names, _col_types):
        return [{'name': n, 'dataType': t} for n, t in zip(_col_names, _col_types)]

    def _form_attribute_list(_attributes):
        return [{
            'name': n,
            'attributeForms': [{
                'category': 'ID',
                'expressions': [{
                    'formula': table_name + "." + n
                }]
            }]
        } for n in _attributes]

    def _form_metric_list(_metrics):
        return [{
            'name': n,
            'dataType': 'number',
            'expressions': [{
                'formula': table_name + "." + n
            }]
        } for n in _metrics]

    col_names = list(df.columns)
    col_types = list(map(_map_data_type, list(df.dtypes.values)))

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
