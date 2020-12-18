import unittest
import pandas as pd
from mstrio.utils.encoder import Encoder
from base64 import b64decode
import json


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


class TestEncoder(unittest.TestCase):

    def test_type_mapping_error(self):
        # Test that returns an error if input is not one of single or multi
        with self.assertRaises(ValueError):
            Encoder(data_frame=make_df(), dataset_type='notsupportedtype')

    def test_type_mapping_single(self):
        enc = Encoder(data_frame=make_df(), dataset_type='single')
        self.assertEqual(enc._Encoder__orientation, 'records')

    def test_type_mapping_multi(self):
        enc = Encoder(data_frame=make_df(), dataset_type='multi')
        self.assertEqual(enc._Encoder__orientation, 'values')

    def test_single_table_encoding(self):
        # Test validity of encoding for single-table
        enc = Encoder(data_frame=make_df(), dataset_type='single')
        enc.encode
        df = pd.DataFrame(json.loads(b64decode(enc._Encoder__b64_data)))
        self.assertEqual(df.salary.sum(), 560000)

    def test_multi_table_encoding(self):
        # Test validity of encoding of multi-table
        enc = Encoder(data_frame=make_df(), dataset_type='multi')
        enc.encode
        df = pd.DataFrame(json.loads(b64decode(enc._Encoder__b64_data)),
                          columns=["id_int", "id_str", "first_name",
                                   "last_name", "age", "weight", "state", "salary"])
        self.assertEqual(df.salary.sum(), 560000)


if __name__ == '__main__':
    unittest.main()
