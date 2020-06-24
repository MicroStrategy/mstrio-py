from copy import deepcopy
import json
from unittest.mock import Mock


class MockCubes:
    with open('production/tests/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['cube']['definition']) as f:
        definition_data = json.load(f)
    with open(data_paths['cube']['instance']) as f:
        instance_data = json.load(f)
    with open(data_paths['cube']['instance_id1']) as f:
        instance_id1_data = json.load(f)
    with open(data_paths['cube']['instance_id2']) as f:
        instance_id2_data = json.load(f)
    with open(data_paths['cube']['info']) as f:
        info_data = json.load(f)
    with open(data_paths['cube']['single_attr_el']) as f:
        single_attr_el_data = json.load(f)
    with open(data_paths['cube']['single_attr_el_headers']) as f:
        single_attr_el_headers = json.load(f)
    with open(data_paths['other']['datasets']) as f:
        datasets_data = json.load(f)
    with open(data_paths['other']['projects']) as f:
        projects_data = json.load(f)

    @classmethod
    def mock_projects_api(cls):
        mocked_projects = Mock()
        mocked_projects.projects.return_value = cls.projects_data
        return mocked_projects

    @classmethod
    def mock_cubes_api(cls):
        mocked_cubes = Mock()
        mocked_cubes.cube_definition.return_value.json.return_value = cls.definition_data
        mocked_cubes.cube_definition.return_value.ok = True
        mocked_cubes.cube_instance = cls.mock_instance()
        mocked_cubes.cube_instance_id.return_value.json.return_value = cls.instance_id1_data
        mocked_cubes.cube_instance_id.return_value.ok = True
        mocked_cubes.cube_info.return_value.json.return_value = cls.info_data
        mocked_cubes.cube_info.return_value.ok = True
        mocked_cubes.cube_single_attribute_elements.return_value.json.return_value = cls.single_attr_el_data
        mocked_cubes.cube_single_attribute_elements.return_value.ok = True
        mocked_cubes.cube_single_attribute_elements.return_value.headers = cls.single_attr_el_headers
        mocked_future = Mock()
        mocked_future.result = mocked_cubes.cube_single_attribute_elements
        mocked_cubes.cube_single_attribute_elements_coroutine.return_value = mocked_future

        return mocked_cubes

    @classmethod
    def mock_authentication_api(cls):
        mocked_authentication = Mock()
        mocked_authentication.login.return_value.ok = True
        return mocked_authentication

    @classmethod
    def mock_datasets_api(cls):
        mocked_datasets = Mock()
        mocked_datasets.dataset_definition.return_value.json.return_value = cls.datasets_data
        return mocked_datasets

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
                with open(cls.data_paths['cube']['instance_attr_el_fltr']) as f:
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
