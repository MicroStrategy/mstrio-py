from copy import deepcopy
import json
from unittest.mock import Mock


class MockReports:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        all_data_paths = json.load(f)
        data_paths = all_data_paths

    with open(data_paths['report']['definition']) as f:
        definition_data = json.load(f)
    with open(data_paths['report']['instance']) as f:
        instance_data = json.load(f)
    with open(data_paths['report']['instance_id1']) as f:
        instance_id1_data = json.load(f)
    with open(data_paths['report']['instance_id2']) as f:
        instance_id2_data = json.load(f)
    with open(data_paths['report']['single_attr_el']) as f:
        single_attr_el_data = json.load(f)
    with open(data_paths['report']['single_attr_el_headers']) as f:
        single_attr_el_headers = json.load(f)
    with open(data_paths['other']['datasets']) as f:
        datasets_data = json.load(f)
    with open(data_paths['other']['projects']) as f:
        projects_data = json.load(f)

    @classmethod
    def mock_reports_api(cls):
        mocked_reports = Mock()
        mocked_reports.report_definition.return_value.json.return_value = cls.definition_data
        mocked_reports.report_definition.return_value.ok = True
        mocked_reports.report_instance = cls.mock_instance()
        mocked_reports.report_instance_id.return_value.json.return_value = cls.instance_id1_data
        mocked_reports.report_instance_id.return_value.ok = True
        mocked_reports.report_single_attribute_elements.return_value.json.return_value = cls.single_attr_el_data
        mocked_reports.report_single_attribute_elements.return_value.ok = True
        mocked_reports.report_single_attribute_elements.return_value.headers = cls.single_attr_el_headers
        mocked_future = Mock()
        mocked_future.result = mocked_reports.report_single_attribute_elements
        mocked_reports.report_single_attribute_elements_coroutine.return_value = mocked_future

        return mocked_reports

    @classmethod
    def mock_instance(cls):
        def mock_json(body, **kwargs):
            output = Mock()
            filters_contain_view_filter = bool(body.get('viewFilter'))
            filters_include_attributes = bool(body.get('requestedObjects').get('attributes'))
            filters_include_metrics = bool(body.get('requestedObjects').get('metrics'))
            filters_include_everything = bool((not body.get('requestedObjects')) or
                                                  (filters_include_attributes and
                                                   filters_include_metrics))

            if filters_contain_view_filter:
                with open(cls.data_paths['report']['instance_attr_el_fltr']) as f:
                    attr_el_filtered_instance_data = json.load(f)
                output.json.return_value = attr_el_filtered_instance_data
            elif filters_include_everything:
                output.json.return_value = cls.instance_data
            elif filters_include_attributes:
                attribute_id = body.get('requestedObjects').get('attributes')[0]['id']
                attr_filtered_instance_data = deepcopy(cls.instance_data)
                rows = attr_filtered_instance_data['definition']['grid']['rows']
                sel_rows = list(filter(lambda x: x['id'] == attribute_id, rows))
                # sel_rows = attr_filtered_instance_data['definition']['grid']['rows'][0]
                attr_filtered_instance_data['definition']['grid']['rows'] = sel_rows
                attr_filtered_instance_data['definition']['grid']['columns'] = []
                output.json.return_value = attr_filtered_instance_data
            elif filters_include_metrics:
                metric_id = body.get('requestedObjects').get('metrics')[0]['id']
                metric_filtered_instance_data = deepcopy(cls.instance_data)
                elements = metric_filtered_instance_data['definition']['grid']['columns'][0]['elements']
                sel_filter = list(filter(lambda x: x[1]['id'] == metric_id, enumerate(elements)))
                sel_cols = sel_filter[0][1]
                sel_idx = sel_filter[0][0]
                metric_filtered_instance_data['definition']['grid']['columns'][0]['elements'] = [sel_cols]
                metric_filtered_instance_data['definition']['grid']['rows'] = []
                raw = metric_filtered_instance_data['data']['metricValues']['raw']
                metric_filtered_instance_data['data']['metricValues']['raw'] = [row[sel_idx] for row in raw]
                output.json.return_value = metric_filtered_instance_data
            return output

        instance = Mock()
        instance.return_value.ok = True
        instance.side_effect = mock_json
        return instance
