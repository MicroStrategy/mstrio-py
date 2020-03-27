import pandas
import unittest
from unittest.mock import Mock, patch

from mstrio.cube import Cube


class TestCube(unittest.TestCase):

    def setUp(self):
        self.cube_id = '7F632A3811E97C1734270080EFE5A6F1'
        self.cube_name = 'df2'
        self.connection = "test_connection"

        self.__info = {
            "cubesInfos": [
                {
                    "cubeName": self.cube_name,
                    "cubeId": self.cube_id,
                    "ownerId": "2ED12F4211E7409200000080EF755231",
                    "path": "\\Rally Analytics\\Profiles\\MSTR User (mstr)\\My Reports\\employees",
                    "modificationTime": "2019-10-13 20:34:22",
                    "serverMode": 1,
                    "size": 453632,
                    "status": 17510
                }
            ]
        }

        self.__definition = {
            "id": "7F632A3811E97C1734270080EFE5A6F1",
            "name": "employees",
            "definition": {
                "availableObjects": {
                    "attributes": [
                        {
                            "name": "id",
                            "id": "C545617611E9EDF8240A0080EF15C472",
                            "type": "attribute",
                            "forms": [
                                {
                                    "id": "45C11FA478E745FEA08D781CEA190FE5",
                                    "name": "ID",
                                    "dataType": "integer",
                                    "baseFormCategory": "ID",
                                    "baseFormType": "number"
                                }
                            ]
                        },
                        {
                            "name": "firstname",
                            "id": "C5456B1C11E9EDF8240A0080EF15C472",
                            "type": "attribute",
                            "forms": [
                                {
                                    "id": "45C11FA478E745FEA08D781CEA190FE5",
                                    "name": "ID",
                                    "dataType": "UTF8Char",
                                    "baseFormCategory": "ID",
                                    "baseFormType": "text"
                                }
                            ]
                        },
                        {
                            "name": "lastname",
                            "id": "C545724211E9EDF8240A0080EF15C472",
                            "type": "attribute",
                            "forms": [
                                {
                                    "id": "45C11FA478E745FEA08D781CEA190FE5",
                                    "name": "ID",
                                    "dataType": "UTF8Char",
                                    "baseFormCategory": "ID",
                                    "baseFormType": "text"
                                }
                            ]
                        },
                        {
                            "name": "state",
                            "id": "C545792211E9EDF89B140080EF15C473",
                            "type": "attribute",
                            "forms": [
                                {
                                    "id": "B191051C48221A6AE44CA2B65B1B65E3",
                                    "name": "Latitude",
                                    "dataType": "double",
                                    "baseFormCategory": "Latitude",
                                    "baseFormType": "number"
                                },
                                {
                                    "id": "2345134F4F5E261C3BB902A874467080",
                                    "name": "Longitude",
                                    "dataType": "double",
                                    "baseFormCategory": "Longitude",
                                    "baseFormType": "number"
                                },
                                {
                                    "id": "45C11FA478E745FEA08D781CEA190FE5",
                                    "name": "ID",
                                    "dataType": "UTF8Char",
                                    "baseFormCategory": "ID",
                                    "baseFormType": "text"
                                }
                            ]
                        }
                    ],
                    "metrics": [
                        {
                            "name": "age",
                            "id": "C5457FEE11E9EDF89B140080EF15C473",
                            "type": "metric",
                            "dataType": "integer"
                        },
                        {
                            "name": "years",
                            "id": "C545891211E9EDF89B140080EF15C473",
                            "type": "metric",
                            "dataType": "double"
                        },
                        {
                            "name": "Row Count - employees.xlsx",
                            "id": "C4A2C01011E9EDF80ADB0080EFB50371",
                            "type": "metric",
                            "dataType": "reserved"
                        }
                    ],
                    "customGroups": [],
                    "consolidations": [],
                    "hierarchies": []
                }
            }
        }

        self.__ds_definition = {
            'result': {
                'definition': {
                    'availableObjects': {
                        'tables': [
                            {
                            'name': 'table1',
                            'columns': ['age']
                            },
                            {
                                'name': 'table2',
                                'columns': ['firstname']
                            }],
                        'columns': [
                            {
                            'columnName': 'age',
                            'tableName': 'table1'
                            },
                            {
                                'columnName': 'firstname',
                                'tableName': 'table2'
                            }]
                    }
                }
            }
        }

        self.__instance = {
            "id": "7F632A3811E97C1734270080EFE5A6F1",
            "name": "employees",
            "instanceId": "C9A98F7011E9EDF9D7DC0080EF0522FC",
            "status": 1,
            "definition": {
                "grid": {
                    "crossTab": False,
                    "metricsPosition": {
                        "axis": "columns",
                        "index": 0
                    },
                    "rows": [{
                        "name": "firstname",
                        "id": "C5456B1C11E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["Amy"],
                            "id": "hAmy;C5456B1C11E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Jake"],
                            "id": "hJake;C5456B1C11E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Jason"],
                            "id": "hJason;C5456B1C11E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "id",
                        "id": "C545617611E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "integer",
                            "baseFormCategory": "ID",
                            "baseFormType": "number"
                        }],
                        "elements": [{
                            "formValues": ["5"],
                            "id": "h5;C545617611E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["4"],
                            "id": "h4;C545617611E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["1"],
                            "id": "h1;C545617611E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "lastname",
                        "id": "C545724211E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["Cooze"],
                            "id": "hCooze;C545724211E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Milner"],
                            "id": "hMilner;C545724211E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Miller"],
                            "id": "hMiller;C545724211E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "state",
                        "id": "C545792211E9EDF89B140080EF15C473",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["CA"],
                            "id": "hCA;C545792211E9EDF89B140080EF15C473"
                        }, {
                            "formValues": ["VA"],
                            "id": "hVA;C545792211E9EDF89B140080EF15C473"
                        }]
                    }],
                    "columns": [{
                        "name": "Metrics",
                        "id": "00000000000000000000000000000000",
                        "type": "templateMetrics",
                        "elements": [{
                            "name": "age",
                            "id": "C5457FEE11E9EDF89B140080EF15C473",
                            "type": "metric",
                            "min": 24,
                            "max": 73,
                            "dataType": "integer",
                            "numberFormatting": {
                                "category": 9,
                                "formatString": "General"
                            }
                        }, {
                            "name": "RowCount-employees.xlsx",
                            "id": "C4A2C01011E9EDF80ADB0080EFB50371",
                            "type": "metric",
                            "min": 1,
                            "max": 1,
                            "dataType": "integer",
                            "numberFormatting": {
                                "category": 0,
                                "decimalPlaces": 0,
                                "formatString": "#,##0;(#,##0)"
                            }
                        }, {
                            "name": "years",
                            "id": "C545891211E9EDF89B140080EF15C473",
                            "type": "metric",
                            "min": 1.2,
                            "max": 15.9,
                            "dataType": "double",
                            "numberFormatting": {
                                "category": 9,
                                "formatString": "General"
                            }
                        }]
                    }],
                    "pageBy": [],
                    "sorting": {
                        "rows": [],
                        "columns": []
                    },
                    "thresholds": []
                }
            },
            "data": {
                "currentPageBy": [],
                "paging": {
                    "total": 5,
                    "current": 3,
                    "offset": 0,
                    "limit": 3
                },
                "headers": {
                    "rows": [
                        [0, 0, 0, 0],
                        [1, 1, 1, 0],
                        [2, 2, 2, 1]
                    ],
                    "columns": [
                        [0, 1, 2]
                    ]
                },
                "metricValues": {
                    "raw": [
                        [73, 1, 15.9],
                        [24, 1, 1.2],
                        [42, 1, 5.6]
                    ]
                }
            }
        }

        self.__instance_id = {
            "id": "7F632A3811E97C1734270080EFE5A6F1",
            "name": "employees",
            "instanceId": "C9A98F7011E9EDF9D7DC0080EF0522FC",
            "status": 1,
            "definition": {
                "grid": {
                    "crossTab": False,
                    "metricsPosition": {
                        "axis": "columns",
                        "index": 0
                    },
                    "rows": [{
                        "name": "firstname",
                        "id": "C5456B1C11E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["Molly"],
                            "id": "hMolly;C5456B1C11E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Tina"],
                            "id": "hTina;C5456B1C11E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "id",
                        "id": "C545617611E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "integer",
                            "baseFormCategory": "ID",
                            "baseFormType": "number"
                        }],
                        "elements": [{
                            "formValues": ["2"],
                            "id": "h2;C545617611E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["3"],
                            "id": "h3;C545617611E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "lastname",
                        "id": "C545724211E9EDF8240A0080EF15C472",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["Jacobson"],
                            "id": "hJacobson;C545724211E9EDF8240A0080EF15C472"
                        }, {
                            "formValues": ["Turner"],
                            "id": "hTurner;C545724211E9EDF8240A0080EF15C472"
                        }]
                    }, {
                        "name": "state",
                        "id": "C545792211E9EDF89B140080EF15C473",
                        "type": "attribute",
                        "forms": [{
                            "id": "45C11FA478E745FEA08D781CEA190FE5",
                            "name": "ID",
                            "dataType": "UTF8Char",
                            "baseFormCategory": "ID",
                            "baseFormType": "text"
                        }],
                        "elements": [{
                            "formValues": ["NC"],
                            "id": "hNC;C545792211E9EDF89B140080EF15C473"
                        }, {
                            "formValues": ["WY"],
                            "id": "hWY;C545792211E9EDF89B140080EF15C473"
                        }]
                    }],
                    "columns": [{
                        "name": "Metrics",
                        "id": "00000000000000000000000000000000",
                        "type": "templateMetrics",
                        "elements": [{
                            "name": "age",
                            "id": "C5457FEE11E9EDF89B140080EF15C473",
                            "type": "metric",
                            "min": 24,
                            "max": 73,
                            "dataType": "integer",
                            "numberFormatting": {
                                "category": 9,
                                "formatString": "General"
                            }
                        }, {
                            "name": "RowCount-employees.xlsx",
                            "id": "C4A2C01011E9EDF80ADB0080EFB50371",
                            "type": "metric",
                            "min": 1,
                            "max": 1,
                            "dataType": "integer",
                            "numberFormatting": {
                                "category": 0,
                                "decimalPlaces": 0,
                                "formatString": "#,##0;(#,##0)"
                            }
                        }, {
                            "name": "years",
                            "id": "C545891211E9EDF89B140080EF15C473",
                            "type": "metric",
                            "min": 1.2,
                            "max": 15.9,
                            "dataType": "double",
                            "numberFormatting": {
                                "category": 9,
                                "formatString": "General"
                            }
                        }]
                    }],
                    "pageBy": [],
                    "sorting": {
                        "rows": [],
                        "columns": []
                    },
                    "thresholds": []
                }
            },
            "data": {
                "currentPageBy": [],
                "paging": {
                    "total": 5,
                    "current": 2,
                    "offset": 3,
                    "limit": 3
                },
                "headers": {
                    "rows": [
                        [0, 0, 0, 0],
                        [1, 1, 1, 1]
                    ],
                    "columns": [
                        [0, 1, 2]
                    ]
                },
                "metricValues": {
                    "raw": [
                        [52, 1, 10.4],
                        [36, 1, 8.5]
                    ]
                }
            }
        }

        self.__attributes = [{'name': a['name'], 'id': a['id']} for a in
                             self.__definition["definition"]["availableObjects"]["attributes"]]
        self.__metrics = [{'name': m['name'], 'id': m['id']} for m in
                          self.__definition["definition"]["availableObjects"]["metrics"]]

        self.__attr_elements = [{"id": "C5456B1C11E9EDF8240A0080EF15C472:Amy", "formValues": ["Amy"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Jake", "formValues": ["Jake"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Jason", "formValues": ["Jason"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Molly", "formValues": ["Molly"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Tina", "formValues": ["Tina"]}]

        self.__headers = {'x-mstr-total-count': '7'}
        self.__selected_attr = ['C5456B1C11E9EDF8240A0080EF15C472']
        self.__selected_metrs = ['C545891211E9EDF89B140080EF15C473']
        self.__selected_elem = ['C5456B1C11E9EDF8240A0080EF15C472:Amy', 'C5456B1C11E9EDF8240A0080EF15C472:Jake']
        self.__dataframe_7 = pandas.DataFrame({'firstname': {0: 'Amy', 1: 'Jake', 2: 'Jason', 3: 'Molly', 4: 'Tina', 5:                                           'Molly', 6: 'Tina'},
                                             'id': {0: '5', 1: '4', 2: '1', 3: '2', 4: '3', 5: '2', 6: '3'},
                                             'lastname': {0: 'Cooze', 1: 'Milner', 2: 'Miller', 3: 'Jacobson', 4:           'Turner', 5: 'Jacobson', 6: 'Turner'},
                                             'state': {0: 'CA', 1: 'CA', 2: 'VA', 3: 'NC', 4: 'WY', 5: 'NC', 6: 'WY'},
                                             'age': {0: 73, 1: 24, 2: 42, 3: 52, 4: 36, 5: 52, 6: 36},
                                             'RowCount-employees.xlsx': {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1},
                                             'years': {0: 15.9, 1: 1.2, 2: 5.6, 3: 10.4, 4: 8.5, 5: 10.4, 6: 8.5}})
        
        self.__dataframe = pandas.DataFrame({'firstname': {0: 'Amy', 1: 'Jake', 2: 'Jason', 3: 'Molly', 4: 'Tina'},
                                               'id': {0: '5', 1: '4', 2: '1', 3: '2', 4: '3'},
                                               'lastname': {0: 'Cooze', 1: 'Milner', 2: 'Miller', 3: 'Jacobson', 4:           'Turner'},
                                               'state': {0: 'CA', 1: 'CA', 2: 'VA', 3: 'NC', 4: 'WY'},
                                               'age': {0: 73, 1: 24, 2: 42, 3: 52, 4: 36},
                                               'RowCount-employees.xlsx': {0: 1, 1: 1, 2: 1, 3: 1, 4: 1},
                                               'years': {0: 15.9, 1: 1.2, 2: 5.6, 3: 10.4, 4: 8.5}})

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
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

        self.assertEqual(cube.attributes, self.__attributes)

        self.assertEqual(cube.metrics, self.__metrics)

        self.assertEqual(cube._attr_elements, [])

        self.assertIsNone(cube.selected_attributes)
        self.assertIsNone(cube.selected_metrics)
        self.assertIsNone(cube.selected_attr_elements)
        self.assertIsNone(cube._dataframe)
        with self.assertWarns(Warning):
            cube.dataframe

    @patch('mstrio.api.cubes.cube_single_attribute_elements_coroutine')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filters(self, mock_info, mock_definition, mock_attr_element, mock_attr_element_coroutine):
        """Test that selected objects are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertTrue(mock_attr_element_coroutine.called)
        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem)

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(attributes=[], metrics=[])
        self.assertEqual(cube.selected_attr_elements, None)
        self.assertEqual(cube.selected_attributes, [])
        self.assertEqual(cube.selected_metrics, [])

    @patch('mstrio.api.cubes.cube_single_attribute_elements_coroutine')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
    @patch('mstrio.api.cubes.cube_info')
    def test_clear_filters(self, mock_info, mock_definition, mock_attr_element, mock_attr_element_coroutine):
        """Test that selected objects are assigned with empty lists when filter is cleared."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.__attr_elements

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
    @patch('mstrio.api.cubes.cube_definition')
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
        df = cube.to_dataframe(limit=3)

        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id.called)
        self.assertIsInstance(df, pandas.core.frame.DataFrame)
        self.assertIsInstance(cube.dataframe, pandas.core.frame.DataFrame)
        self.assertEqual(df.years.sum(), 41.6)
        self.assertEqual(df.age.sum(), 227)

    @patch('mstrio.api.cubes.cube_instance_id_coroutine')
    @patch('mstrio.api.cubes.cube_instance_id')
    @patch('mstrio.api.cubes.cube_instance')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
    @patch('mstrio.api.cubes.cube_info')
    @patch('mstrio.api.datasets.dataset_definition')
    def test_to_dataframe_multi_data_frame_true(self, mock_ds_definition, mock_info, mock_definition, mock_attr_element,
                                                mock_instance, mock_instance_id, mock_instance_id_coroutine):
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
        mock_instance_id_coroutine = Mock()
        mock_instance_id_coroutine.return_value.result.return_value = Mock(ok=True)
        mock_instance_id_coroutine.return_value.result.return_value.json.return_value = self.__instance_id

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.to_dataframe(limit=3, multi_df=True)

        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id.called)
        # self.assertIsInstance(cube.dataframes, list)
        self.assertIsInstance(cube.dataframe, pandas.core.frame.DataFrame)
        self.assertTrue(cube.dataframe.equals(self.__dataframe))

        for i, df in enumerate(cube.dataframes):
            colnames = self.__ds_definition['result']['definition']['availableObjects']['tables'][i]['columns']
            self.assertIsInstance(df, pandas.core.frame.DataFrame)
            self.assertTrue(df.equals(self.__dataframe[colnames]))

    @patch('mstrio.api.cubes.cube_single_attribute_elements_coroutine')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filters_for_incorrect_assignments(self, mock_info, mock_definition, mock_attr_element,
                                                     mock_attr_element_coroutine):
        """Test that incorrectly assigned selected objects are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        # attributes assigned selected_metrs, metrics assigned selected_elem and attr_elements assigned selected_attr
        cube.apply_filters(attributes=self.__selected_metrs, metrics=self.__selected_elem,
                           attr_elements=self.__selected_attr)

        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, self.__selected_elem)

    @patch('mstrio.api.cubes.cube_single_attribute_elements_coroutine')
    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
    @patch('mstrio.api.cubes.cube_info')
    def test_apply_filter_no_list(self, mock_info, mock_definition, mock_attr_element, mock_attr_element_coroutine):
        """Test that selected objects passed as strings are assigned properly when filter is applied."""

        mock_info.return_value = Mock(ok=True)
        mock_info.return_value.json.return_value = self.__info
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.__attr_elements

        cube = Cube(connection=self.connection, cube_id=self.cube_id)
        cube.apply_filters(attributes=self.__selected_attr[0],
                           metrics=self.__selected_metrs[0],
                           attr_elements=self.__selected_elem[0])

        self.assertEqual(cube.selected_attributes, self.__selected_attr)
        self.assertEqual(cube.selected_metrics, self.__selected_metrs)
        self.assertEqual(cube.selected_attr_elements, [self.__selected_elem[0]])

    @patch('mstrio.api.cubes.cube_single_attribute_elements')
    @patch('mstrio.api.cubes.cube_definition')
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


if __name__ == '__main__':
    unittest.main()
