import unittest
import pandas as pd
from mstrio.utils.formjson import formjson


def make_df():
    # this is the base data frame used for testing
    raw_data = {"id_int": [1, 2, 3, 4, 5],
                "id_str": ["1", "2", "3", "4", "5"],
                "first_name": ["Jason", "Molly", "Tina", "Jake", "Amy"],
                "last_name": ["Miller", "Jacobson", "Turner", "Milner", "Cooze"],
                "age": [42, 52, 36, 24, 73],
                "weight": [100.22, 210.2, 175.1, 155.9, 199.9],
                "state": ["VA", "NC", "WY", "CA", "CA"],
                "salary": [50000, 100000, 75000, 85000, 250000]}
    df = pd.DataFrame(raw_data, columns=["id_int", "id_str", "first_name", "last_name",
                                         "age", "weight", "state", "salary"])
    return df


class TestFormjson(unittest.TestCase):

    def test_column_headers(self):
        column_headers, attribute_list, metric_list = formjson(df=make_df(), table_name='TEST')
        testcase = [{'name': 'id_int', 'dataType': 'INTEGER'},
                    {'name': 'id_str', 'dataType': 'STRING'},
                    {'name': 'first_name', 'dataType': 'STRING'},
                    {'name': 'last_name', 'dataType': 'STRING'},
                    {'name': 'age', 'dataType': 'INTEGER'},
                    {'name': 'weight', 'dataType': 'DOUBLE'},
                    {'name': 'state', 'dataType': 'STRING'},
                    {'name': 'salary', 'dataType': 'INTEGER'}]
        self.assertListEqual(column_headers, testcase)

    def test_attribute_list(self):
        column_headers, attribute_list, metric_list = formjson(df=make_df(), table_name='TEST')
        testcase = [{'name': 'id_str', 'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.id_str'}]}]},
                    {'name': 'first_name', 'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.first_name'}]}]},
                    {'name': 'last_name', 'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.last_name'}]}]},
                    {'name': 'state', 'attributeForms': [{'category': 'ID', 'expressions': [{'formula': 'TEST.state'}]}]}]

        self.assertListEqual(attribute_list, testcase)

    def test_metric_list(self):
        column_headers, attribute_list, metric_list = formjson(df=make_df(), table_name='TEST')
        testcase = [{'name': 'id_int', 'dataType': 'number', 'expressions': [{'formula': 'TEST.id_int'}]},
                    {'name': 'age', 'dataType': 'number', 'expressions': [{'formula': 'TEST.age'}]},
                    {'name': 'weight', 'dataType': 'number', 'expressions': [{'formula': 'TEST.weight'}]},
                    {'name': 'salary', 'dataType': 'number', 'expressions': [{'formula': 'TEST.salary'}]}]

        self.assertListEqual(metric_list, testcase)

    def test_formjson_with_attribute_override(self):

        # in this test, the element 'id_int' from the data frame needs to be converted to a attribute in the data model.
        # to accomplish this, simply check that id_int is present in the model json when it is specified as the override

        column_headers, attribute_list, metric_list = formjson(df=make_df(), table_name='TEST', as_attributes=['id_int'])

        # check that id_int is in attribute list
        attributes = [i['name'] for i in attribute_list]
        self.assertIn('id_int', attributes)

    def test_formjson_with_metric_override(self):

        # in this test, the element 'id_str' from the data frame needs to be converted to a metric in the data model.
        # to accomplish this, simply check that id_str is present in the model json when it is specified as the override

        column_headers, attribute_list, metric_list = formjson(df=make_df(), table_name='TEST', as_metrics=['id_str'])

        # check that id_str is in metric list
        metrics = [i['name'] for i in metric_list]
        self.assertIn('id_str', metrics)

    def test_formjson_with_32_bit_metrics(self):

        # create df and change types as needed
        df = make_df()
        df.weight = df.weight.astype('float32')
        df.id_int = df.id_int.astype('int32')
        df.age = df.age.astype('int32')
        df.salary = df.salary.astype('int32')

        # generate json string model from the test dataframe
        column_headers, attribute_list, metric_list = formjson(df=df, table_name='TEST')
        for col in column_headers:
            if col['name'] == 'weight':
                self.assertEqual(col['dataType'], 'DOUBLE')
            if col['name'] in ['id_int', 'age', 'salary']:
                self.assertEqual(col['dataType'], 'INTEGER')

        # Test that created json for the above metrics as in the metrics from created_json and that types didnt change

    def test_formjson_with_64_bit_metrics(self):

        # create df and change types as needed
        df = make_df()
        df.weight = df.weight.astype('float64')
        df.id_int = df.id_int.astype('int64')
        df.age = df.age.astype('int64')
        df.salary = df.salary.astype('int64')

        # generate json string model from the test dataframe
        column_headers, attribute_list, metric_list = formjson(df=df, table_name='TEST')
        for col in column_headers:
            if col['name'] == 'weight':
                self.assertEqual(col['dataType'], 'DOUBLE')
            if col['name'] in ['id_int', 'age', 'salary']:
                self.assertEqual(col['dataType'], 'INTEGER')


if __name__ == '__main__':
    unittest.main()
