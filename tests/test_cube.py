import pandas
import unittest
from unittest.mock import Mock, patch

from mstrio.cube import Cube


class TestCube(unittest.TestCase):

    def setUp(self):
        self.cube_id = '08A0D88011E9CA4D00000080EFE555B9'
        self.cube_name = 'df2'
        self.connection = "test_connection"
        self.__info = {'cubesInfos': [{'cubeName': self.cube_name,
                                       'cubeId': self.cube_id,
                                       'ownerId': '7FC05A65473CE2FD845CE6A1D3F13233',
                                       'path': '\\MicroStrategy Tutorial\\Profiles\\MSTR User (mstr)\\My Reports\\unit tests\\df2',
                                       'modificationTime': '2019-08-29 11:06:24',
                                       'serverMode': 1,
                                       'size': 271360,
                                       'status': 17518}]}
        self.__definition = {'id': self.cube_id,
                            'name': self.cube_name,
                             'result': {'definition': {'availableObjects': {'metrics': [{'name': 'Age',
                                'id': '089FB58611E9CA4D39700080EF15B5B9',
                                'type': 'Metric'},
                                {'name': 'Row Count - table1',
                                'id': '089DE7BA11E9CA4D085B0080EFC515B9',
                                'type': 'Metric'}],
                                'attributes': [{'name': 'Name',
                                'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                'type': 'Attribute',
                                'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                    'name': 'ID',
                                    'dataType': 'Char',
                                    'baseFormCategory': 'ID',
                                    'baseFormType': 'Text'}]}]}}}}
        self.__ds_definition = {
            'result': {
                'definition': {
                    'availableObjects': {
                        'tables': [
                            {
                            'name': 'table1',
                            'columns': ['Age']
                            },
                            {
                                'name': 'table2',
                                'columns': ['Name']
                            }],
                        'columns': [
                            {
                            'columnName': 'Age',
                            'tableName': 'table1'
                            },
                            {
                                'columnName': 'Name',
                                'tableName': 'table2'
                            }]
                    }
                }
            }
        }
        self.__instance = {'id': '08A0D88011E9CA4D00000080EFE555B9',
                            'name': 'df2',
                            'status': 1,
                            'instanceId': '49C2D26C11E9CB21237E0080EF1546B6',
                            'result': {'definition': {'metrics': [{'name': 'Age',
                                'id': '089FB58611E9CA4D39700080EF15B5B9',
                                'type': 'Metric',
                                'min': 18,
                                'max': 21,
                                'dataType': 'Integer',
                                'numberFormatting': {'category': 9, 'formatString': 'General'}}],
                            'attributes': [{'name': 'Name',
                                'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                'type': 'Attribute',
                                'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                'name': 'ID',
                                'dataType': 'Char',
                                'baseFormCategory': 'ID',
                                'baseFormType': 'Text'}]}],
                            'thresholds': [],
                            'sorting': []},
                            'data': {'paging': {'total': 4,
                                'current': 2,
                                'offset': 0,
                                'limit': 2,
                                'prev': None,
                                'next': None},
                            'root': {'isPartial': True,
                                'children': [{'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'jack'},
                                'name': 'jack',
                                'id': 'hjack;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 18, 'fv': '18', 'mi': 0}}},
                                {'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'krish'},
                                'name': 'krish',
                                'id': 'hkrish;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 19, 'fv': '19', 'mi': 0}}}]}}}}
        self.__instance_id = {'id': '08A0D88011E9CA4D00000080EFE555B9',
                            'name': 'df2',
                            'status': 1,
                            'instanceId': '49C2D26C11E9CB21237E0080EF1546B6',
                            'result': {'definition': {'metrics': [{'name': 'Age',
                                'id': '089FB58611E9CA4D39700080EF15B5B9',
                                'type': 'Metric',
                                'min': 18,
                                'max': 21,
                                'dataType': 'Integer',
                                'numberFormatting': {'category': 9, 'formatString': 'General'}}],
                            'attributes': [{'name': 'Name',
                                'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                'type': 'Attribute',
                                'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                'name': 'ID',
                                'dataType': 'Char',
                                'baseFormCategory': 'ID',
                                'baseFormType': 'Text'}]}],
                            'thresholds': [],
                            'sorting': []},
                            'data': {'paging': {'total': 4,
                                'current': 2,
                                'offset': 2,
                                'limit': 2,
                                'prev': None,
                                'next': None},
                            'root': {'isPartial': True,
                                'children': [{'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'nick'},
                                'name': 'nick',
                                'id': 'hnick;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 21, 'fv': '21', 'mi': 0}}},
                                {'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'Tom'},
                                'name': 'Tom',
                                'id': 'hTom;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 20, 'fv': '20', 'mi': 0}}}]}}}}

        self.__attr_elements = [{'id': '089FC10C11E9CA4D39700080EF15B5B9:jack', 'formValues': ['jack']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:krish', 'formValues': ['krish']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:nick', 'formValues': ['nick']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:Tom', 'formValues': ['Tom']}]
        self.__headers = {'x-mstr-total-count': '4'}
        self.__selected_attr = ['089FC10C11E9CA4D39700080EF15B5B9']
        self.__selected_metrs = ['089FB58611E9CA4D39700080EF15B5B9']
        self.__selected_elem = ['089FC10C11E9CA4D39700080EF15B5B9:Tom', '089FC10C11E9CA4D39700080EF15B5B9:jack']
        self.__dataframe = pandas.DataFrame({'Name':['jack', 'krish','nick','Tom'], 'Age':[18,19,21,20]})

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_init_cube(self, mock_info, mock_definition, mock_attr_element):
        """Test that definition of the cube is assigned properly when cube is initialized."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)

        self.assertTrue(mock_info.called)
        self.assertTrue(mock_definition.called)

        self.assertEqual(cube._connection, self.connection)
        self.assertEqual(cube._cube_id, self.cube_id)
        self.assertEqual(cube.name, self.cube_name)
        self.assertEqual(cube.size, self.__info['cubesInfos'][0]['size'])
        self.assertEqual(cube.status, self.__info['cubesInfos'][0]['status'])
        self.assertEqual(cube.path, self.__info['cubesInfos'][0]['path'])
        self.assertEqual(cube.owner_id, self.__info['cubesInfos'][0]['ownerId'])
        self.assertEqual(cube.last_modified, self.__info['cubesInfos'][0]['modificationTime'])

        self.assertEqual(cube.attributes, [{'name': 'Name', 'id': '089FC10C11E9CA4D39700080EF15B5B9'}])
        self.assertEqual(cube.metrics, [{'name': 'Age', 'id': '089FB58611E9CA4D39700080EF15B5B9'},
                                        {'name': 'Row Count - table1', 'id': '089DE7BA11E9CA4D085B0080EFC515B9'}])
        self.assertEqual(cube.attr_elements, [])

        self.assertIsNone(cube.selected_attributes)
        self.assertIsNone(cube.selected_metrics)
        self.assertIsNone(cube.selected_attr_elements)
        self.assertIsNone(cube._dataframe)
        with self.assertWarns(Warning):
            cube.dataframe

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filters(self, mock_info, mock_definition, mock_attr_element):
        """Test that selected objects are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertTrue(mock_attr_element.called)
        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem)

        cube.clear_filters()
        cube.apply_filters(attributes=[], metrics=[])
        self.assertEqual(cube.attr_elements, [{'attribute_name': 'Name',
                                        'attribute_id': '089FC10C11E9CA4D39700080EF15B5B9','elements': [
                                        {'id': '089FC10C11E9CA4D39700080EF15B5B9:jack','formValues': ['jack']},
                                        {'id': '089FC10C11E9CA4D39700080EF15B5B9:krish', 'formValues': ['krish']},
                                        {'id': '089FC10C11E9CA4D39700080EF15B5B9:nick', 'formValues': ['nick']},
                                        {'id': '089FC10C11E9CA4D39700080EF15B5B9:Tom', 'formValues': ['Tom']}]}])
        self.assertEqual(cube.selected_attributes, None)
        self.assertEqual(cube.selected_metrics, None)

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_clear_filters(self, mock_info, mock_definition, mock_attr_element):
        """Test that selected objects are assigned with empty lists when filter is cleared."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem)

        cube.clear_filters()

        self.assertIsNone(cube.selected_attributes)
        self.assertIsNone(cube.selected_metrics)
        self.assertIsNone(cube.selected_attr_elements)

    @patch('mstrio.api.cubes.cube_instance_id')
    @patch('mstrio.api.cubes.cube_instance')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_to_dataframe(self, mock_info, mock_definition, mock_attr_element, mock_instance, mock_instance_id):
        """Test that data is retrieved and parsed properly when to_dataframe() is called.
        Result should be saved to Cube.dataframe property.
        """

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)        
        mock_instance.return_value.json.return_value = self.__instance
        mock_instance_id.return_value = Mock(ok=True)
        mock_instance_id.return_value.json.return_value = self.__instance_id

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        df = cube.to_dataframe(limit=2)
        
        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id.called)
        self.assertIsInstance(df, pandas.core.frame.DataFrame)
        self.assertIsInstance(cube.dataframe, pandas.core.frame.DataFrame)
        self.assertTrue(df.equals(self.__dataframe))

    @patch('mstrio.api.cubes.cube_instance_id')
    @patch('mstrio.api.cubes.cube_instance')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    @patch('mstrio.api.datasets.dataset_definition')
    def test_to_dataframe_multi_data_frame_true(self, mock_ds_definition, mock_info, mock_definition, mock_attr_element,
                                                mock_instance, mock_instance_id):
        mock_ds_definition.return_value = Mock(ok=True)
        mock_ds_definition.return_value.json.return_value = self.__ds_definition
        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance
        mock_instance_id.return_value = Mock(ok=True)
        mock_instance_id.return_value.json.return_value = self.__instance_id

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        dfs = cube.to_dataframe(limit=2, multi_df=True)

        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id.called)
        self.assertIsInstance(dfs, list)
        self.assertIsInstance(cube.dataframe, pandas.core.frame.DataFrame)
        self.assertTrue(cube.dataframe.equals(self.__dataframe))
        for i, df in enumerate(dfs):
            colnames = self.__ds_definition['result']['definition']['availableObjects']['tables'][i]['columns']
            self.assertIsInstance(df, pandas.core.frame.DataFrame)
            self.assertTrue(df.equals(self.__dataframe[colnames]))

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filters_for_incorrect_assignments(self, mock_info, mock_definition, mock_attr_element):
        """Test that incorrectly assigned selected objects are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        # attributes assigned selected_metrs, metrics assigned selected_elem and attr_elements assigned selected_attr
        cube.apply_filters(attributes=self.__selected_metrs, metrics=self.__selected_elem,
                           attr_elements=self.__selected_attr)

        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem)

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filter_no_list(self, mock_info, mock_definition, mock_attr_element):
        """Test that selected objects passed as strings are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(attributes=self.__selected_attr[0], metrics=self.__selected_metrs[0],
                           attr_elements= self.__selected_elem[0])

        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem[:1])

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filters_invalid_elements(self, mock_info, mock_definition, mock_attr_element):
        """Test that invalid id passed to a filter raises ValueError."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        self.assertRaises(ValueError, cube.apply_filters, attributes='INV123456')

    @patch('mstrio.api.datasets.dataset_definition')
    @patch('mstrio.api.cubes.cube')
    @patch('mstrio.api.cubes.cube_info')
    def test_multitable_definition(self, mock_info, mock_definition, mock_ds_definition):
        """Test that multitable definition function returns proper dictionary."""
        
        __definition = {'id': '3D6D912611E9F40400000080EF3580D0',
                        'name': 'IRIS',
                        'result': {'definition': {'availableObjects': {'tables': [{'id': 'F256FBE616DFD979E7548694E3363106',
                        'name': 'IRIS',
                        'type': 15},
                        {'id': 'F256FBE616DFD979E7548694E3363109',
                        'name': 'IRIS2',
                        'type': 15}],
                        'columns': [{'tableId': 'F256FBE616DFD979E7548694E3363106',
                        'tableName': 'IRIS',
                        'columnId': '0621CC6C11E9F65400000080EF35AAE7',
                        'columnName': 'Id',
                        'dataType': 33,
                        'precision': 0,
                        'scale': 0},
                        {'tableId': 'F256FBE616DFD979E7548694E3363106',
                        'tableName': 'IRIS',
                        'columnId': '0621CF3C11E9F65400000080EF35AAE7',
                        'columnName': 'PetalWidthCm',
                        'dataType': 33,
                        'precision': 0,
                        'scale': 0},
                        {'tableId': 'F256FBE616DFD979E7548694E3363109',
                        'tableName': 'IRIS2',
                        'columnId': '0621D0EA11E9F65400000080EF35AAE7',
                        'columnName': 'SepalWidthCm',
                        'dataType': 33,
                        'precision': 0,
                        'scale': 0}]}}}}

        __returned_dictionary = {
                                'IRIS': ['Id','PetalWidthCm'],
                                'IRIS2': ['SepalWidthCm']}

        mock_ds_definition.return_value = Mock(ok=True)
        mock_ds_definition.return_value.json.return_value = __definition

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube._Cube__multitable_definition()
        self.assertEqual(cube.table_definition,__returned_dictionary)
        


if __name__ == '__main__':
    unittest.main()
