# Class object for MicroStrategy API connection

# TODO: (1) Create method / param to check if connect is active, uses authentication.sessions()
# TODO: (2) Create method to select project, call it 'select_project'

import json
from base64 import b64encode
import pandas as pd
from mstrio.api import projects, cubes, reports, authentication, datasets
from mstrio.utils.parsejson import parsejson
from mstrio.utils.formjson import formjson


class Connection:

    auth_token = None
    cookies = None
    project_id = None

    def __init__(self, base_url=None, username=None, password=None, project_name=None, login_mode=1, ssl_verify=True):
        """
        Establishes a connection with MicroStrategy REST API

        :param base_url: URL of the MicroStrategy REST API server. Typically of the form
        https://<mstr_env>.com/MicroStrategyLibrary/api
        :param username: Username
        :param password: Password
        :param project_name: Name of the project you intend to connect to. Case-sensitive
        :param login_mode: Specifies the authentication mode to use. Supported authentication modes are: Standard (1)
                           (default) or LDAP (16)
        :param ssl_verify: If True (default), verifies the server's SSL certificates with each request
        """

        self.base_url = base_url
        self.username = username
        self.password = password
        self.project_name = project_name
        self.login_mode = login_mode
        self.ssl_verify = ssl_verify

    def connect(self):
        """Creates a connection"""

        response = authentication.login(connection=self)

        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Authentication error. Check user credentials or REST API URL and try again.')
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))
        else:
            self.auth_token, self.cookies = response.headers['X-MSTR-AuthToken'], dict(response.cookies)

        # Fetch the list of projects the user has access to
        response = projects.projects(connection=self)

        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Error connecting to project %s. Check project name and try again.' % self.project_name)
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))
        else:
            _projects = response.json()

            # Find which project ID matches the project name provided
            for _project in _projects:
                if _project['name'] == self.project_name:  # Enter the desired project name here
                    self.project_id = _project['id']

    def close(self):
        """Closes a connection with MicroStrategy REST API"""
        authentication.logout(connection=self)

    def get_report(self, report_id, offset=0, limit=1000):
        """
        Extracts the contents of a report into a Pandas Data Frame

        :param report_id: Unique ID of the report you wish to extract information from
        :param offset: (optional) To extract all data from the report, use 0 (default)
        :param limit: (optional) Used to control data extract behavior on datasets with a large
        number of rows. The default is 1000. As an example, if the dataset has 50,000 rows,
        get_report() will incrementally extract all 50,000 rows in 1,000 row chunks. Depending
        on system resources, a higher limit (e.g. 10,000) may reduce the total time
        required to extract the entire dataset
        :return: Pandas Data Frame containing the report contents
        """

        response = reports.report_instance(connection=self,
                                           report_id=report_id,
                                           offset=offset,
                                           limit=limit)
        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Error getting report contents.')
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))
        else:
            json_response = response.json()
            instance_id = json_response['instanceId']

            # Gets the pagination totals from the response object
            pagination = json_response['result']['data']['paging']

            # If there are more rows to fetch, fetch them
            if pagination['current'] != pagination['total']:

                # initialize a list to capture slices from each query, and append the first request's result to the list
                table_data = [parsejson(response=json_response)]

                # Fetch add'l rows from this object instance from the intelligence server
                for _offset in range(limit, pagination['total'], limit):
                    response = reports.report_instance_id(connection=self,
                                                          report_id=report_id,
                                                          instance_id=instance_id,
                                                          offset=_offset,
                                                          limit=limit)
                    table_data.append(parsejson(response=response.json()))
                return pd.concat(table_data)
            else:
                return parsejson(response=json_response)

    def get_cube(self, cube_id, offset=0, limit=1000):
        """
        Extracts the contents of a cube into a Pandas Data Frame

        :param cube_id: Unique ID of the cube you wish to extract information from.
        :param offset: (optional) To extract all data from the report, use 0 (default)
        :param limit: (optional) Used to control data extract behavior on datasets with a large
        number of rows. The default is 1000. As an example, if the dataset has 50,000 rows,
        get_cube() will incrementally extract all 50,000 rows in 1,000 row chunks. Depending
        on system resources, a higher limit (e.g. 10,000) may reduce the total time
        required to extract the entire dataset
        :return: Pandas Data Frame containing the cube contents
        """

        response = cubes.cube_instance(connection=self, cube_id=cube_id, offset=offset, limit=limit)

        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Error getting cube contents.')
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))
        else:
            json_response = response.json()
            instance_id = json_response['instanceId']

            # Gets the pagination totals from the response object
            pagination = json_response['result']['data']['paging']

            # If there are more rows to fetch, fetch them
            if pagination['current'] != pagination['total']:

                # initialize a list to capture slices from each query, and append the first request's result to the list
                table_data = [parsejson(response=json_response)]

                # Fetch add'l rows from this object instance from the intelligence server
                for _offset in range(limit, pagination['total'], limit):
                    response = cubes.cube_instance_id(connection=self,
                                                      cube_id=cube_id,
                                                      instance_id=instance_id,
                                                      offset=_offset,
                                                      limit=limit)
                    table_data.append(parsejson(response=response.json()))
                return pd.concat(table_data)
            else:
                return parsejson(response=json_response)

    def create_dataset(self, data_frame, dataset_name, table_name, to_metric=None, to_attribute=None):
        """
        Create an in-memory MicroStrategy dataset from a Pandas Data Frame

        :param data_frame: A Pandas Data Frame from which an in-memory dataset will be created
        :param dataset_name: Name of the in-memory dataset
        :param table_name: Name of the table to create within the dataset
        :param to_metric: (optional) A vector of column names from the Data.Frame to format as metrics
        in the dataset. By default, numeric types are formatted as metrics while character and date types are formatted
        as attributes. For example, a column of integer-like strings ("1", "2", "3") would
        appear as an attribute in the newly created dataset. If the intent is to format this data as a metric, provide
        the corresponding column name as \code{to_metric=c('myStringIntegers')}
        :param to_attribute: (optional) Logical opposite of to_metric. Helpful for formatting an integer-based row
        identifier as a primary key in the dataset
        :return: Unique identifiers of the dataset and table within the newly created dataset. Required for
        update_dataset()
        """

        # Replace any leading/trailing whitespace in df names, replace '.' with '_'
        _df = data_frame.copy()
        _df.columns = _df.columns.str.replace(".", "_")
        _df.columns = _df.columns.str.strip()

        # Base 64 encoding
        data_encoded = b64encode(_df.to_json(orient='records', date_format='iso').encode('utf-8')).decode('utf-8')

        # Create the json body string
        column_headers, attribute_list, metric_list = formjson(df=_df,
                                                               table_name=table_name,
                                                               as_metrics=to_metric,
                                                               as_attributes=to_attribute)

        json_body = json.loads(json.dumps({'name': dataset_name,
                                           'tables': [{'name': table_name,
                                                       'columnHeaders': column_headers,
                                                       'data': data_encoded}],
                                           'attributes': attribute_list,
                                           'metrics': metric_list}))

        # Create dataset
        response = datasets.create_dataset(connection=self, json_body=json_body)
        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Error creating the dataset.')
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))

        else:
            json_response = response.json()
            _dataset_id, _table_id = json_response['datasetId'], json_response['tables'][0]['id']
            return _dataset_id, _table_id

    def update_dataset(self, data_frame, dataset_id, table_name, update_policy, table_id=None):

        # TODO: Support for table_id and/or table_name (10.11 defect)

        """
        Update a previously created dataset with an Pandas Data Frame

        :param data_frame: Pandas Data Frame to use to update an in-memory dataset
        :param dataset_id: Identifier of the dataset to update, provided by create_dataset()
        :param table_name: Name of the table to update within the dataset
        :param table_id: Not used
        :param update_policy: Update operation to perform. One of 'add' (inserts new, unique rows), 'update'
        (updates data in existing rows and columns), 'upsert' (updates existing
        data and inserts new rows), 'replace' (similar to truncate and load, replaces the existing data with new data)
        """

        # Replace any leading/trailing whitespace in df names, replace '.' with '_'
        _df = data_frame.copy()
        _df.columns = _df.columns.str.replace(".", "_")
        _df.columns = _df.columns.str.strip()

        # Base 64 encoding
        data_encoded = b64encode(_df.to_json(orient='records', date_format='iso').encode('utf-8')).decode('utf-8')

        # Create the json body string
        column_headers, attribute_list, metric_list = formjson(df=_df, table_name=table_name)

        # Pass json body to request handler
        json_body = json.loads(json.dumps({'name': table_name,
                                           'columnHeaders': column_headers,
                                           'data': data_encoded}))

        response = datasets.update_dataset(connection=self, dataset_id=dataset_id,
                                           table_name=table_name, update_policy=update_policy,
                                           json_body=json_body)
        if not response.ok:
            # print error message
            errmsg = json.loads(response.content)
            print('Error updating the data set. Check for data type inconsistencies.')
            print("HTTP %i %s" % (response.status_code, response.reason))
            print("I-Server Error %s, %s" % (errmsg['code'], errmsg['message']))
