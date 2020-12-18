import json
import os

from mstrio.api import cubes, datasets, misc, projects, reports
from mstrio.microstrategy import Connection


class ResponsesGenerator:
    def __init__(self, connection, cube_id, report_id, dataset_id, cube_attribute_id, report_attribute_id,
                 settings_path='production/tests/unit/settings/api_response_path.json'):
        self.connection = connection
        self.cube_id = cube_id
        self.report_id = report_id
        self.dataset_id = dataset_id
        self.cube_attribute_id = cube_attribute_id
        self.report_attribute_id = report_attribute_id
        with open(settings_path) as f:
            self.paths = json.load(f)

    def generate_cubes_responses(self):
        g = CubeResponsesGenerator(connection=self.connection, cube_id=self.cube_id,
                                   filter_attribute_id=self.cube_attribute_id)
        self.cube_definition = g.generate_cube_definition()
        self.cube_info = g.generate_cube_info()
        self.cube_instance = g.generate_cube_instance()
        self.cube_instance_attr_el_fltr = g.generate_cube_instance(filter='attr_el')
        self.cube_instance_id1 = g.generate_cube_instance_id(offset=0, limit=70)
        self.cube_instance_id2 = g.generate_cube_instance_id(offset=70)
        self.cube_single_attr_el = g.generate_cube_single_attr_el()
        self.cube_single_attr_el_headers = g.generate_cube_single_attr_el_headers()

    def generate_reports_responses(self):
        g = ReportResponsesGenerator(connection=self.connection,
                                     report_id=self.report_id,
                                     filter_attribute_id=self.report_attribute_id)
        self.report_definition = g.generate_report_definition()
        self.report_instance = g.generate_report_instance()
        self.report_instance_attr_el_fltr = g.generate_report_instance(filter='attr_el')
        self.report_instance_id1 = g.generate_report_instance_id(offset=0, limit=70)
        self.report_instance_id2 = g.generate_report_instance_id(offset=70)
        self.report_single_attr_el = g.generate_report_single_attr_el()
        self.report_single_attr_el_headers = g.generate_report_single_attr_el_headers()

    def generate_other_responses(self):
        g = OtherResponsesGenerator(connection=self.connection,
                                    dataset_id=self.dataset_id)
        self.dataset_definition = g.generate_dataset_definition()
        self.projects = g.generate_projects()
        self.server_status = g.generate_server_status()

    def dump_cubes_responses(self):
        cubes_paths = self.paths['cube']
        with open(cubes_paths['single_attr_el_headers'], 'w+') as f:
            json.dump(dict(self.cube_single_attr_el_headers), f)
        with open(cubes_paths['definition'], 'w+') as f:
            json.dump(self.cube_definition, f)
        with open(cubes_paths['info'], 'w+') as f:
            json.dump(self.cube_info, f)
        with open(cubes_paths['instance'], 'w+') as f:
            json.dump(self.cube_instance, f)
        with open(cubes_paths['instance_attr_el_fltr'], 'w+') as f:
            json.dump(self.cube_instance_attr_el_fltr, f)
        with open(cubes_paths['instance_id1'], 'w+') as f:
            json.dump(self.cube_instance_id1, f)
        with open(cubes_paths['instance_id2'], 'w+') as f:
            json.dump(self.cube_instance_id2, f)
        with open(cubes_paths['single_attr_el'], 'w+') as f:
            json.dump(self.cube_single_attr_el, f)

    def dump_reports_responses(self):
        reports_paths = self.paths['report']
        with open(reports_paths['definition'], 'w+') as f:
            json.dump(self.report_definition, f)
        with open(reports_paths['instance'], 'w+') as f:
            json.dump(self.report_instance, f)
        with open(reports_paths['instance_attr_el_fltr'], 'w+') as f:
            json.dump(self.report_instance_attr_el_fltr, f)
        with open(reports_paths['instance_id1'], 'w+') as f:
            json.dump(self.report_instance_id1, f)
        with open(reports_paths['instance_id2'], 'w+') as f:
            json.dump(self.report_instance_id2, f)
        with open(reports_paths['single_attr_el'], 'w+') as f:
            json.dump(self.report_single_attr_el, f)
        with open(reports_paths['single_attr_el_headers'], 'w+') as f:
            json.dump(dict(self.report_single_attr_el_headers), f)

    def dump_other_responses(self):
        other_paths = self.paths['other']
        with open(other_paths['datasets'], 'w+') as f:
            json.dump(self.dataset_definition, f)
        with open(other_paths['projects'], 'w+') as f:
            json.dump(self.projects, f)
        with open(other_paths['misc'], 'w+') as f:
            json.dump(self.server_status, f)


class CubeResponsesGenerator(object):
    def __init__(self, connection, cube_id, filter_attribute_id):
        self.connection = connection
        self.cube_id = cube_id
        self.filter_attribute_id = filter_attribute_id
        self.instance_id = None

    def generate_cube_definition(self):
        res = cubes.cube_definition(connection=self.connection,
                                    cube_id=self.cube_id)
        return res.json()

    def generate_cube_info(self):
        res = cubes.cube_info(connection=self.connection,
                              cube_id=self.cube_id)
        return res.json()

    def generate_cube_instance(self, filter=None):
        res = cubes.cube_instance(connection=self.connection,
                                  cube_id=self.cube_id)
        self.instance_id = res.json()['instanceId']
        res_json = res.json()
        if filter == 'attr_el':
            for i, row in enumerate(res_json['definition']['grid']['rows']):
                row['elements'] = row['elements'][0:1]
                res_json['definition']['grid']['rows'][i] = row

            res_json['data']['headers']['rows'] = res_json['data']['headers']['rows'][0:1]
            res_json['data']['metricValues']['raw'] = res_json['data']['metricValues']['raw'][0:1]
            res_json['data']['metricValues']['formatted'] = res_json['data']['metricValues']['formatted'][0:1]
            res_json['data']['metricValues']['extras'] = res_json['data']['metricValues']['extras'][0:1]

        return res_json

    def generate_cube_instance_id(self, offset, limit=5000):
        res = cubes.cube_instance_id(connection=self.connection,
                                     cube_id=self.cube_id,
                                     instance_id=self.instance_id,
                                     offset=offset,
                                     limit=limit)
        return res.json()

    def generate_cube_single_attr_el(self):
        res = cubes.cube_single_attribute_elements(connection=self.connection,
                                                   cube_id=self.cube_id,
                                                   attribute_id=self.filter_attribute_id)
        return res.json()

    def generate_cube_single_attr_el_headers(self):
        res = cubes.cube_single_attribute_elements(connection=self.connection,
                                                   cube_id=self.cube_id,
                                                   attribute_id=self.filter_attribute_id)
        return res.headers


class ReportResponsesGenerator(object):
    def __init__(self, connection, report_id, filter_attribute_id):
        self.connection = connection
        self.report_id = report_id
        self.filter_attribute_id = filter_attribute_id
        self.instance_id = None

    def generate_report_definition(self):
        res = reports.report_definition(self.connection,
                                        report_id=self.report_id)

        return res.json()

    def generate_report_instance(self, filter=None):
        res = reports.report_instance(self.connection,
                                      report_id=self.report_id)
        self.instance_id = res.json()['instanceId']
        res_json = res.json()
        if filter == 'attr_el':
            for i, row in enumerate(res_json['definition']['grid']['rows']):
                row['elements'] = row['elements'][0:1]
                res_json['definition']['grid']['rows'][i] = row

            res_json['data']['headers']['rows'] = res_json['data']['headers']['rows'][0:1]
            res_json['data']['metricValues']['raw'] = res_json['data']['metricValues']['raw'][0:1]
            res_json['data']['metricValues']['formatted'] = res_json['data']['metricValues']['formatted'][0:1]
            res_json['data']['metricValues']['extras'] = res_json['data']['metricValues']['extras'][0:1]

            self.instance_id = res.json()['instanceId']
        return res_json

    def generate_report_instance_id(self, offset, limit=5000):
        res = reports.report_instance_id(self.connection,
                                         report_id=self.report_id,
                                         instance_id=self.instance_id,
                                         offset=offset,
                                         limit=limit)
        return res.json()

    def generate_report_single_attr_el(self):
        res = reports.report_single_attribute_elements(self.connection,
                                                       report_id=self.report_id,
                                                       attribute_id=self.filter_attribute_id)
        return res.json()

    def generate_report_single_attr_el_headers(self):
        res = reports.report_single_attribute_elements(self.connection,
                                                       report_id=self.report_id,
                                                       attribute_id=self.filter_attribute_id)
        return res.headers


class OtherResponsesGenerator(object):
    def __init__(self, connection, dataset_id):
        self.connection = connection
        self.dataset_id = dataset_id

    def generate_dataset_definition(self):
        res = datasets.dataset_definition(self.connection,
                                          dataset_id=self.dataset_id,
                                          fields=['tables', 'columns'])
        return res.json()

    def generate_projects(self):
        res = projects.get_projects(self.connection)
        return res.json()

    def generate_server_status(self):
        res = misc.server_status(self.connection)
        return res.json()

if __name__ == '__main__':
    base_url = 'https://env-167618.customer.cloud.microstrategy.com/MicroStrategyLibrary/api'
    mstr_username = "mstr"
    mstr_password = "admin"
    cube_id = "C70D1AEA11EA4C2000000080EF850925"
    report_id = "251F443C11EA4E5600000080EF1575DE"
    project_id = "B7CA92F04B9FAE8D941C3E9B7E0CD754"
    dataset_id = cube_id
    login_mode = 1
    cube_attribute_id = '7BC69FAC11EA4C2060710080EFD5AA25'
    report_attribute_id = '7BC69FAC11EA4C2060710080EFD5AA25'

    conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
    conn.connect()

    rg = ResponsesGenerator(connection=conn, cube_id=cube_id, report_id=report_id,
                            cube_attribute_id=cube_attribute_id, report_attribute_id=report_attribute_id,
                            dataset_id=dataset_id)
    print("Generating cube responses")
    rg.generate_cubes_responses()
    print("Generating report responses")
    rg.generate_reports_responses()
    print("Generating other responses")
    rg.generate_other_responses()
    print("Dumping results")
    rg.dump_cubes_responses()
    rg.dump_reports_responses()
    rg.dump_other_responses()
