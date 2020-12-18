import json
import os

from measurements import Measurer
import mstr_connect as con
import mstr_create as crt
import mstr_import as imp
import mstr_update as upd


def main():
    output_path = 'tests/integration/results/time_measurements.json'
    general_config_path = 'tests/integration/configs/general_configs.json'

    general_configs = read_configs(general_config_path)
    connection_details = {
        "url": general_configs["env_url"],
        "username": general_configs["username"],
        "password": general_configs["password"],
        "login_mode": general_configs["login_mode"],
        "project_id": general_configs["project_id"]
    }
    cube_id = general_configs["cube_id"]
    report_id = general_configs["report_id"]

    upload_data_filename = general_configs['upload_data_paths']['py']
    upload_data_path = os.path.join('tests', 'integration', 'configs',
                                    upload_data_filename)
    upload_data = read_configs(upload_data_path)

    update_data_filename = general_configs['upload_data_paths']['py_update']
    update_data_path = os.path.join('tests', 'integration', 'configs',
                                    update_data_filename)
    update_data = read_configs(update_data_path)

    filter_config_filename = general_configs['filters_paths']['py']
    filter_config_path = os.path.join('tests', 'integration', 'configs',
                                      filter_config_filename)
    filters = read_configs(filter_config_path)
    m = Measurer(measurements_path=output_path)
    m.time_that(n_times=50, f=con.get_connection,
                json_keyword='connection',
                **connection_details)
    connection = con.get_connection(**connection_details)

    # parallel = False
    m.time_that(n_times=5, f=imp.get_cube_dataframe,
                json_keyword='cube_no_filter_no_parallel',
                cube_id=cube_id,
                connection=connection,
                parallel=False)
    m.time_that(n_times=5, f=imp.get_cube_dataframe,
                json_keyword='cube_filter_no_parallel',
                cube_id=cube_id,
                connection=connection,
                attribute_filter=filters['attribute_ids'],
                metric_filter=['metric_ids'],
                element_filter=['element_ids'],
                parallel=False)
    m.time_that(n_times=5, f=imp.get_report_dataframe,
                json_keyword='report_no_filter_no_parallel',
                report_id=report_id,
                connection=connection,
                parallel=False)
    m.time_that(n_times=5, f=imp.get_report_dataframe,
                json_keyword='report_filter_no_parallel',
                report_id=report_id,
                connection=connection,
                attribute_filter=filters['attribute_ids'],
                metric_filter=['metric_ids'],
                element_filter=['element_ids'],
                parallel=False)

    # parallel = True
    downloaded_data = m.time_that(n_times=5, f=imp.get_cube_dataframe,
                json_keyword='cube_no_filter',
                cube_id=cube_id,
                connection=connection)
    m.time_that(n_times=5, f=imp.get_cube_dataframe,
                json_keyword='cube_filter',
                cube_id=cube_id,
                connection=connection,
                attribute_filter=filters['attribute_ids'],
                metric_filter=['metric_ids'],
                element_filter=['element_ids'],)
    m.time_that(n_times=5, f=imp.get_report_dataframe,
                json_keyword='report_no_filter',
                report_id=report_id,
                connection=connection)
    m.time_that(n_times=5, f=imp.get_report_dataframe,
                json_keyword='report_filter',
                report_id=report_id,
                connection=connection,
                attribute_filter=filters['attribute_ids'],
                metric_filter=['metric_ids'],
                element_filter=['element_ids'])

    updated_cube_id = m.time_that(n_times=5, f=crt.create_cube,
                json_keyword='create_cube',
                cube_name='uploaded_perf_tests',
                data=downloaded_data,
                connection=connection)

    m.time_that(n_times=5, f=upd.update_cube,
                json_keyword='update_cube',
                connection=connection,
                new_data=downloaded_data,
                cube_id=updated_cube_id,
                table_name='table')


if __name__ == '__main__':
    main()
