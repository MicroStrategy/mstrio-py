import unittest
import pandas as pd
from mstrio.utils.formjson import formjson


def make_df():
    raw_data = {'id_int': [1, 2, 3, 4, 5],
                'id_str': ['1', '2', '3', '4', '5'],
                'first_name': ['Jason', 'Molly', 'Tina', 'Jake', 'Amy'],
                'last_name': ['Miller', 'Jacobson', "Turner", 'Milner', 'Cooze'],
                'age': [42, 52, 36, 24, 73],
                'weight': [100.22, 210.2, 175.1, 155.9, 199.9],
                'state': ["VA", "NC", "WY", "CA", "CA"],
                'salary': [50000, 100000, 75000, 85000, 250000]}
    df = pd.DataFrame(raw_data, columns=['id_int', 'id_str', 'first_name ', 'last_name',
                                         'age', 'weight', 'state', 'salary'])
    return df


class TestFormjson(unittest.TestCase):

    def test_formjson(self):
        expected_json = tuple(([{'dataType': 'INTEGER', 'name': 'id_int'},
                                {'dataType': 'STRING', 'name': 'id_str'},
                                {'dataType': 'STRING', 'name': 'first_name '},
                                {'dataType': 'STRING', 'name': 'last_name'},
                                {'dataType': 'INTEGER', 'name': 'age'},
                                {'dataType': 'DOUBLE', 'name': 'weight'},
                                {'dataType': 'STRING', 'name': 'state'},
                                {'dataType': 'INTEGER', 'name': 'salary'}],
                               [{'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.id_str'}]}],
                                 'name': 'id_str'},
                                {'attributeForms': [
                                    {'category': 'ID', 'expressions': [{'formula': 'TEST.first_name '}]}],
                                 'name': 'first_name '},
                                {'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.last_name'}]}],
                                 'name': 'last_name'},
                                {'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.state'}]}],
                                 'name': 'state'}],
                               [{'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.id_int'}],
                                 'name': 'id_int'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.age'}],
                                 'name': 'age'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.weight'}],
                                 'name': 'weight'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.salary'}],
                                 'name': 'salary'}]))

        created_json = formjson(df=make_df(), table_name='TEST')
        self.assertEquals(created_json, expected_json)

    def test_formjson_with_attribute_override(self):
        expected_json = tuple(([{'dataType': 'INTEGER', 'name': 'id_int'},
                                {'dataType': 'STRING', 'name': 'id_str'},
                                {'dataType': 'STRING', 'name': 'first_name '},
                                {'dataType': 'STRING', 'name': 'last_name'},
                                {'dataType': 'INTEGER', 'name': 'age'},
                                {'dataType': 'DOUBLE', 'name': 'weight'},
                                {'dataType': 'STRING', 'name': 'state'},
                                {'dataType': 'INTEGER', 'name': 'salary'}],
                               [{'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.id_int'}]}],
                                 'name': 'id_int'},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.id_str'}]}],
                                 'name': 'id_str'},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.first_name '}]}],
                                 'name': 'first_name '},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.last_name'}]}],
                                 'name': 'last_name'},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.state'}]}],
                                 'name': 'state'}],
                               [{'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.age'}],
                                 'name': 'age'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.weight'}],
                                 'name': 'weight'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.salary'}],
                                 'name': 'salary'}]))
        created_json = formjson(df=make_df(), table_name='TEST', as_attributes=['id_int'])
        self.assertEquals(created_json, expected_json)

    def test_formjson_with_metric_override(self):
        expected_json = tuple(([{'dataType': 'INTEGER', 'name': 'id_int'},
                                {'dataType': 'STRING', 'name': 'id_str'},
                                {'dataType': 'STRING', 'name': 'first_name '},
                                {'dataType': 'STRING', 'name': 'last_name'},
                                {'dataType': 'INTEGER', 'name': 'age'},
                                {'dataType': 'DOUBLE', 'name': 'weight'},
                                {'dataType': 'STRING', 'name': 'state'},
                                {'dataType': 'INTEGER', 'name': 'salary'}],
                               [{'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.first_name '}]}],
                                 'name': 'first_name '},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.last_name'}]}],
                                 'name': 'last_name'},
                                {'attributeForms': [{'category': 'ID',
                                                     'expressions': [{'formula': 'TEST.state'}]}],
                                 'name': 'state'}],
                               [{'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.id_int'}],
                                 'name': 'id_int'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.id_str'}],
                                 'name': 'id_str'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.age'}],
                                 'name': 'age'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.weight'}],
                                 'name': 'weight'},
                                {'dataType': 'number',
                                 'expressions': [{'formula': 'TEST.salary'}],
                                 'name': 'salary'}]))
        created_json = formjson(df=make_df(), table_name='TEST', as_metrics=['id_str'])
        self.assertEquals(created_json, expected_json)

if __name__ == '__main__':
    unittest.main()
