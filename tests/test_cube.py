import json
import pickle
import unittest

import pandas as pd
from tests.mock_cube import MockCubes
from tests.mock_connection import MockConnection
from mstrio import connection
from mstrio import cube
from mstrio import microstrategy


class TestCube(unittest.TestCase):
    test_df_path = 'production/tests/api-responses/cubes/iris_cube_dumped.pkl'
    test_multi_df_path = 'production/tests/api-responses/cubes/iris_cube_multi_dumped.pkl'
    cube_info_path = 'production/tests/api-responses/cubes/cube_info.json'
    cube_definition_path = 'production/tests/api-responses/cubes/cube_definition.json'

    def setUp(self):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        microstrategy.connection.projects = MockConnection.mock_projects_api()
        microstrategy.connection.authentication = MockConnection.mock_authentication_api()
        microstrategy.connection.misc = MockConnection.mock_misc_api()
        cube.cubes = MockCubes.mock_cubes_api()
        cube.datasets = MockCubes.mock_datasets_api()

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')
        self.cube_id = ''
        with open(self.test_df_path, 'rb') as f:
            self.required_df = pickle.load(f)

        with open(self.test_multi_df_path, 'rb') as f:
            self.required_multi_df = pickle.load(f)

        with open(self.cube_info_path, 'rb') as f:
            self.cube_info_data = json.load(f)

        with open(self.cube_definition_path, 'rb') as f:
            self.cube_definition_data = json.load(f)

    def test_apply_filters(self):
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        metric_id = tested_cube.metrics[0]['id']
        tested_cube.apply_filters(metrics=metric_id)
        self.assertEqual(tested_cube.selected_metrics, [metric_id])
        attribute_id = tested_cube.attributes[0]['id']
        tested_cube.apply_filters(attributes=attribute_id)
        self.assertEqual(tested_cube.selected_attributes, [[attribute_id]])
        attribute_element_id = tested_cube.attr_elements[0]['elements'][0]['id']
        tested_cube.apply_filters(attr_elements=attribute_element_id)
        self.assertEqual(tested_cube.selected_attr_elements, [attribute_element_id])

    def test_attribute_form_filters(self):
        """Test filtering of attribute forms"""
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        tested_cube.clear_filters()
        tested_cube.apply_filters(attributes=["7BC6BEBA11EA4C2060710080EFD5AA25;45C11FA478E745FEA08D781CEA190FE5"])
        self.assertEqual(tested_cube.selected_attributes, [["7BC6BEBA11EA4C2060710080EFD5AA25", "45C11FA478E745FEA08D781CEA190FE5"]])
        tested_cube.clear_filters()
        tested_cube.apply_filters(attributes=["7BC6BEBA11EA4C2060710080EFD5AA25;45C11FA478E745FEA08D781CEA190FE5"], metrics = ["7C047DCC11EA4C205F200080EFF5EA25"])
        self.assertEqual(tested_cube.selected_attributes, [["7BC6BEBA11EA4C2060710080EFD5AA25", "45C11FA478E745FEA08D781CEA190FE5"]])
        self.assertEqual(tested_cube.selected_metrics, ["7C047DCC11EA4C205F200080EFF5EA25"])

    def test_clear_filters(self):
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        attribute_id = tested_cube.attributes[0]['id']
        metric_id = tested_cube.metrics[0]['id']
        attribute_element_id = tested_cube.attr_elements[0]['elements'][0]['id']
        tested_cube.apply_filters(attributes=attribute_id)
        tested_cube.clear_filters()
        self.assertEqual(tested_cube.selected_attributes, [])
        tested_cube.apply_filters(metrics=metric_id)
        tested_cube.clear_filters()
        self.assertCountEqual(tested_cube.selected_metrics, [mtr['id'] for mtr in tested_cube.metrics])
        tested_cube.apply_filters(attr_elements=attribute_element_id)
        tested_cube.clear_filters()
        self.assertEqual(tested_cube.selected_attr_elements, [])


    def test_to_dataframe_no_filter(self):
        tested_cube = cube.Cube(parallel=True, connection=self.connection, cube_id=self.cube_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True)[0].equals(self.required_multi_df[0]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True)[1].equals(self.required_multi_df[1]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True, limit=70)[0].equals(self.required_multi_df[0]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True, limit=70)[1].equals(self.required_multi_df[1]))
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True)[0].equals(self.required_multi_df[0]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True)[1].equals(self.required_multi_df[1]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True, limit=70)[0].equals(self.required_multi_df[0]))
        self.assertTrue(tested_cube.to_dataframe(multi_df=True, limit=70)[1].equals(self.required_multi_df[1]))

    def test_to_dataframe_metric_filter(self):
        tested_cube = cube.Cube(parallel=True, connection=self.connection, cube_id=self.cube_id)
        metric_id = tested_cube.metrics[0]['id']
        metric_name = tested_cube.metrics[0]['name']
        tested_cube.apply_filters(attributes=[], metrics=metric_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[[metric_name]]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[[metric_name]]))
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        metric_id = tested_cube.metrics[0]['id']
        metric_name = tested_cube.metrics[0]['name']
        tested_cube.apply_filters(attributes=[], metrics=metric_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[[metric_name]]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[[metric_name]]))

    def test_to_dataframe_attribute_filter(self):
        tested_cube = cube.Cube(parallel=True, connection=self.connection, cube_id=self.cube_id)
        attribute_id = tested_cube.attributes[0]['id']
        attribute_name = tested_cube.attributes[0]['name']
        tested_cube.apply_filters(attributes=attribute_id, metrics=[])
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[[attribute_name]]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[[attribute_name]]))
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        attribute_id = tested_cube.attributes[0]['id']
        attribute_name = tested_cube.attributes[0]['name']
        tested_cube.apply_filters(attributes=attribute_id, metrics=[])
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[[attribute_name]]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[[attribute_name]]))

    def test_to_dataframe_attribute_element_filter(self):
        tested_cube = cube.Cube(parallel=True, connection=self.connection, cube_id=self.cube_id)
        attr_element_id = tested_cube.attr_elements[0]['elements'][0]['id']
        attr_el_value = tested_cube.attr_elements[0]['elements'][0]['formValues'][0]
        tested_cube.apply_filters(attr_elements=attr_element_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[self.required_df['Id'] == attr_el_value]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[self.required_df['Id'] == attr_el_value]))
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        attr_element_id = tested_cube.attr_elements[0]['elements'][0]['id']
        attr_el_value = tested_cube.attr_elements[0]['elements'][0]['formValues'][0]
        tested_cube.apply_filters(attr_elements=attr_element_id)
        self.assertTrue(tested_cube.to_dataframe().equals(self.required_df[self.required_df['Id'] == attr_el_value]))
        self.assertTrue(tested_cube.to_dataframe(limit=70).equals(self.required_df[self.required_df['Id'] == attr_el_value]))

    def test_properties(self):
        tested_cube = cube.Cube(parallel=False, connection=self.connection, cube_id=self.cube_id)
        tested_df = tested_cube.to_dataframe()
        self.assertTrue(tested_df.equals(tested_cube.dataframe))
        tested_dfs = tested_cube.to_dataframe(multi_df=True)
        self.assertTrue(tested_dfs[0].equals(tested_cube.dataframes[0]))
        self.assertTrue(tested_dfs[1].equals(tested_cube.dataframes[1]))
        self.assertEqual(tested_cube.name, self.cube_info_data['cubesInfos'][0]['cubeName'])
        self.assertEqual(tested_cube.size, self.cube_info_data['cubesInfos'][0]['size'])
        self.assertEqual(tested_cube.status, self.cube_info_data['cubesInfos'][0]['status'])
        self.assertEqual(tested_cube.path, self.cube_info_data['cubesInfos'][0]['path'])
        self.assertEqual(tested_cube.owner_id, self.cube_info_data['cubesInfos'][0]['ownerId'])
        self.assertEqual(tested_cube.attributes,
                         [{'id': attr['id'],
                           'name': attr['name']} for \
                          attr in self.cube_definition_data['definition']['availableObjects']['attributes']])
        self.assertEqual(tested_cube.metrics,
                         [{'id': metric['id'],
                           'name': metric['name']} for \
                          metric in self.cube_definition_data['definition']['availableObjects']['metrics'] \
                          if not metric['name'].startswith('Row Count - ')])
        self.assertEqual(tested_cube.table_definition,
                         {'Iris.csv': ['Id',
                                       'SepalLengthCm',
                                       'SepalWidthCm',
                                       'PetalLengthCm',
                                       'PetalWidthCm',
                                       'Species'],
                          'Iris2.csv': ['SrepalLengthCm',
                                        'SrepalWidthCm',
                                        'PietalLengthCm',
                                        'PietalWidthCm',
                                        'Species',
                                        'Id']})

    def test_compatibility(self):
        connection = microstrategy.Connection(base_url='http://mocked.url.com',
                                              username='username',
                                              password='password')
        tested_cube = cube.Cube(parallel=False,
                                connection=connection,
                                cube_id=self.cube_id)
        tested_cube.apply_filters(metrics=['7B708EF011EA4C20098D0080EFF5EA25'])
        tested_cube.to_dataframe()
        df = tested_cube.dataframe
        self.assertIsInstance(df, pd.DataFrame)


