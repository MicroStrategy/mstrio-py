import unittest
from unittest.mock import Mock, patch
import pandas as pd
from mstrio.dataset import Dataset


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


class TestDatasets(unittest.TestCase):

    def test_init_null_values(self):
        # Test that null param values are assigned properly when initiated

        ds = Dataset(connection={}, name="__test_name")

        self.assertIsNone(ds.description)
        self.assertIsNone(ds.dataset_id)
        self.assertIsNone(ds._definition)
        self.assertIsNone(ds._session_id)
        self.assertIsNone(ds._folder_id)
        self.assertIsNone(ds.upload_body)
        self.assertEqual(len(ds._tables), 0)
    
    @patch('mstrio.api.datasets.dataset_definition')
    def test_init_non_null(self, mock_definition):
        # Test that non-null param values are assigned properly when initiated

        __test_name = "TEST"
        __test_desc = "TEST DESCRIPTION"
        __test_ds_id = "id1234567890"
        __definition = {'name': 'test_name', 'id': __test_ds_id}
        
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = __definition

        ds = Dataset(connection={}, name=__test_name)
        self.assertEqual(ds._name, __test_name)

        ds = Dataset(connection={}, name=__test_name, description=__test_desc)
        self.assertEqual(ds._desc, __test_desc)

        ds = Dataset(connection={}, dataset_id=__test_ds_id)
        self.assertTrue(mock_definition.called)
        self.assertEqual(ds._definition, __definition)
        self.assertEqual(ds._dataset_id, __test_ds_id)
        self.assertEqual(ds._name, __definition['name'])

    def test_add_table(self):
        # Test that adding a table to the dataset increases length of tables property by one

        ds = Dataset(connection={}, name="test_name")

        ds.add_table(name="TEST1", data_frame=make_df(), update_policy="add")
        self.assertEqual(len(ds._tables), 1)

        ds.add_table(name="TEST2", data_frame=make_df(), update_policy="add")
        self.assertEqual(len(ds._tables), 2)

    def test_invalid_update_policy(self):
        # Test that invalid update policy values produces an error

        ds = Dataset(connection={}, name="test_name")
        self.assertRaises(ValueError, ds.add_table, name="TEST", data_frame=make_df(), update_policy="invalid")

    def test_invalid_attr_override(self):
        # Test that attribute override columns names which dont match the source table produces an error

        ds = Dataset(connection={}, name="test_name")
        self.assertRaises(ValueError, ds.add_table, name="TEST", data_frame=make_df(), update_policy="add",
                          to_attribute=["invalid"])

    def test_invalid_metr_override(self):
        # Test that metric override columns names which dont match the source table produces an error

        ds = Dataset(connection={}, name="test_name")
        self.assertRaises(ValueError, ds.add_table, name="TEST", data_frame=make_df(), update_policy="add",
                          to_metric=["invalid"])

    def test_duplicate_col_attr_metr_override(self):
        # Test that duplicate attribute and metric column names when override produces an error

        ds = Dataset(connection={}, name="test_name")
        self.assertRaises(ValueError, ds.add_table, name="TEST", data_frame=make_df(), update_policy="add",
                          to_attribute=["age"], to_metric=["age"])


if __name__ == '__main__':
    unittest.main()
