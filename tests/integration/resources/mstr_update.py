from mstrio.dataset import Dataset
import pandas as pd


def update_cube(connection, new_data, cube_id, table_name, update_policy="replace"):
    ds = Dataset(connection=connection, dataset_id=cube_id)
    ds.add_table(name=table_name, data_frame=new_data, update_policy=update_policy)
    ds.update()


def modify_locally(downloaded_file_df, initial_value, replacing_value):
    locally_modified_df = downloaded_file_df
    locally_modified_df = locally_modified_df.replace(initial_value,
                                                      replacing_value)
    return locally_modified_df

def modify_locally_add_row(downloaded_file_df, values_to_add, columns_to_add,
                           ignore_index=True):
    locally_modified_df = downloaded_file_df
    new_row = pd.DataFrame([values_to_add], columns=columns_to_add)
    locally_modified_df = locally_modified_df.append(new_row, 
                                                     ignore_index=ignore_index)
    return locally_modified_df
