from mstrio.cube import Cube
from mstrio.dataset import Dataset
from pandas import DataFrame


def create_cube(connection, data, cube_name="cube_tmp", table_name='table', folder_id=None,
                to_metric=None, to_attribute=None, update_policy='replace'):
    ds = Dataset(connection=connection, name=cube_name)
    ds.add_table(
        name=table_name,
        data_frame=data,
        update_policy=update_policy,
        to_metric=to_metric,
        to_attribute=to_attribute,
    )
    if (folder_id is None):
        ds.create()
    else:
        ds.create(folder_id=folder_id)
    return ds.dataset_id


def get_cube_from_dataframe(connection, dataframe_data, cube_name="cube_tmp", table_name="table",
                            folder_id=None, to_metric=None, to_attribute=None,
                            update_policy='add'):
    df = DataFrame(dataframe_data)
    ds_id = create_cube(
        connection=connection,
        data=df,
        folder_id=folder_id,
        update_policy=update_policy,
        to_metric=to_metric,
        to_attribute=to_attribute,
    )
    return Cube(connection=connection, cube_id=ds_id)
