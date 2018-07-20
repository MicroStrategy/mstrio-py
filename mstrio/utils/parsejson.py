import pandas as pd


def parsejson(response):
    """

    :param response:
    :return:
    """

    def _has_child(node):
        if 'children' in node.keys():
            return True
        else:
            return False

    def _get_attribute_names(_response):
        # Returns a list of attribute column names from the full json response object
        j = _response['result']['definition']['attributes']
        return [j[n]['name'] for n in range(len(j))]

    def _get_attribute(node):
        # Returns the attribute index and name from a node as a tuple
        return node['element']['attributeIndex'], node['element']['name']

    def _get_metric_names(_response):
        # Returns a list of metric names from the full json response object
        j = _response['result']['definition']['metrics']
        return [j[n]['name'] for n in range(len(j))]

    def _get_metrics(node):
        _metrics = [node['metrics'][_key]['rv'] for _key in node['metrics']]
        return _metrics

    def _parse_node(node):
        # Recursively parses the json string, extract attributes and metrics
        _data = []
        if _has_child(node=node):
            for child in node['children']:
                _data.append(_get_attribute(node=child))
                _data += _parse_node(node=child)
        else:
            _data.append(_get_metrics(node=node))
        return _data

    attribute_names = _get_attribute_names(response)
    metric_names = _get_metric_names(response)
    parsed_rows = _parse_node(node=response['result']['data']['root'])

    metrs = []
    attrs = []
    temp = [None] * len(attribute_names)

    for element in parsed_rows:
        if isinstance(element, tuple):
            _attr_idx, _attr_name = element
            temp[_attr_idx] = _attr_name
            if _attr_idx == len(attribute_names)-1:
                attrs.append(temp[:])
        if isinstance(element, list):
            metrs.append(element)

    df_data = []
    for att, met in zip(attrs, metrs):
        df_data.append(att + met)

    df = pd.DataFrame(df_data, columns=attribute_names + metric_names)

    return df
