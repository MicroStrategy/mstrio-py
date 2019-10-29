import unittest
import pandas as pd
from mstrio.utils.model import Model


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


class TestModel(unittest.TestCase):

    def test_model_structure(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)
        model_dict = model.get_model()

        # check that model is a dictionary
        self.assertIsInstance(model_dict, dict)

        # check that dictionary keys are as expected
        self.assertCountEqual(list(model_dict.keys()), ["name", "description", "folderId",
                                                         "tables", "metrics", "attributes"])

        # check that these elements of the dictionary are lists
        self.assertIsInstance(model.tables, list)
        self.assertIsInstance(model.metrics, list)
        self.assertIsInstance(model.attributes, list)

        # check that name and description match
        self.assertEqual(model.name, DATASETNAME)
        self.assertEqual(model.description, DESCRIPTION)

        # check that column names are unaffected and match the original data frame
        ch = [i['name'] for i in model.tables[0]['columnHeaders']]
        self.assertCountEqual(list(df.columns), ch)

    def test_single_table(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)

        self.assertEqual(len(model.tables), 1)
        self.assertEqual(len(model.attributes), 4)
        self.assertEqual(len(model.metrics), 4)

    def test_multi_table(self):
        df = make_df()
        tables = [{"table_name": "employee1",
                   "data_frame": df},
                  {"table_name": "employee2",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)

        self.assertEqual(len(model.tables), 2)
        self.assertEqual(len(model.attributes), 8)
        self.assertEqual(len(model.metrics), 8)

    def test_metric_override(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df,
                   "to_metric": ["id_str"]}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)

        self.assertEqual(len(model.attributes), 3)
        self.assertEqual(len(model.metrics), 5)

    def test_attribute_override(self):
        df = make_df()
        tables = [{"table_name": "employee1",
                   "data_frame": df,
                   "to_attribute": ["id_int"]},
                  {"table_name": "employee2",
                   "data_frame": df,
                   "to_attribute": ["id_int", "salary", "age"]}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)

        self.assertEqual(len(model.attributes), 12)
        self.assertEqual(len(model.metrics), 4)

    def test_both_override(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df,
                   "to_metric": ["id_str"],
                   "to_attribute": ["id_int", "salary", "age"]}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)

        self.assertEqual(len(model.attributes), 6)
        self.assertEqual(len(model.metrics), 2)

    def test_data_param_no_list(self):
        tables = make_df()

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        self.assertRaises(TypeError, Model, tables=tables, name=DATASETNAME, description=DESCRIPTION)

    def test_data_param_empty_list(self):
        df = make_df()
        tables = [df]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        self.assertRaises(TypeError, Model, tables=tables, name=DATASETNAME, description=DESCRIPTION)

    def test_data_param_bad_key(self):
        df = make_df()
        tables = [{"wrong1": df,
                   "wrong2": "employees"}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        self.assertRaises(ValueError, Model, tables=tables, name=DATASETNAME, description=DESCRIPTION)

    def test_long_dataset_description(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
                      "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " \
                      "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris " \
                      "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in " \
                      "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " \
                      "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa " \
                      "qui officia deserunt mollit anim id est laborum."

        self.assertRaises(ValueError, Model, tables=tables, name=DATASETNAME, description=DESCRIPTION)

    def test_folder_id_none(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION)
        self.assertEqual(model.folder_id, "")

    def test_folder_id_not_none(self):
        df = make_df()
        tables = [{"table_name": "employee",
                   "data_frame": df}]

        DATASETNAME = "Employees"
        DESCRIPTION = "Table of employee data."
        FOLDERID = 'folder123456'

        model = Model(tables=tables, name=DATASETNAME, description=DESCRIPTION, folder_id=FOLDERID)
        self.assertEqual(model.folder_id, FOLDERID)


if __name__ == '__main__':
    unittest.main()
