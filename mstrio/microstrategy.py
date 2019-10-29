# TODO (srigney): Create method to select project, call it 'select_project'
import warnings
import pandas as pd

from mstrio.dataset import Dataset
from mstrio.api import projects, cubes, reports, authentication, misc
from mstrio.utils.parsejson import parsejson
from packaging import version


class Connection(object):
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and manages the user's connection
    with the MicroStrategy REST and Intelligence Servers.

    # import
    from mstrio import microstrategy

    # connect to the environment and chosen project
    conn = microstrategy.Connection(base_url="https://demo.microstrategy.com/MicroStrategyLibrary/api",
                                    username="username",
                                    password="password",
                                    project_name="MicroStrategy Tutorial")
    conn.connect()

    # disconnect
    conn.close()

    Attributes:
        base_url: URL of the MicroStrategy REST API server.
        username: Username.
        password: Password.
        project_name: Name of the connected MicroStrategy Project.
        project_id: Id of the connected MicroStrategy Project.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates with each request.
    """

    auth_token = None
    cookies = None
    project_id = None
    application_code = 64
    __VRCH ="11.1.0400"

    def __init__(self, base_url=None, username=None, password=None, project_name=None, project_id=None,
                 login_mode=1, ssl_verify=True):
        """
        Establishes a connection with MicroStrategy REST API

        Args:
            base_url (str, optional): URL of the MicroStrategy REST API server. Typically of the form
            https://<mstr_env>.com/MicroStrategyLibrary/api
            username (str, optional): Username
            password (str, optional): Password
            project_name (str, optional): Name of the project you intend to connect to.Case-sensitive.
                            You should provide either Project ID or Project Name.
            project_id (str, optional): Id of the project you intend to connect to. Case-sensitive.
                            You should provide either Project ID or Project Name.
            login_mode (int, optional): Specifies the authentication mode to use. Supported authentication modes are: 
                            Standard (1) (default) or LDAP (16)
            ssl_verify (bool, optional): If True (default), verifies the server's SSL certificates with each request
        """

        self.base_url = base_url
        self.username = username
        self.password = password
        if project_id is not None and project_name is not None:
            raise ValueError("Provide either Project ID or Project Name.")
        else:
            self.project_id = project_id
            self.project_name = project_name
        self.login_mode = login_mode
        self.ssl_verify = ssl_verify
        self.__web_version = None
        self.__iserver_version = None

    def connect(self):
        """Creates a connection"""
        if self.__check_version():
            response = authentication.login(connection=self)

            if not response.ok:
                msg = 'Authentication error. Check user credentials or REST API URL and try again.'
                self.__response_handler(response=response, msg=msg)
            else:
                self.auth_token, self.cookies = response.headers['X-MSTR-AuthToken'], dict(response.cookies)

                # Fetch the list of projects the user has access to
                response = projects.projects(connection=self)

                if not response.ok:
                    msg = "Error connecting to project '{}'. Check project name and try again.".format(self.project_name)
                    self.__response_handler(response=response, msg=msg)
                else:
                    # Find which project ID matches the project name provided
                    _projects = response.json()

                    if self.project_name is not None:
                        # Find which project ID matches the project name provided
                        for _project in _projects:
                            if _project['name'] == self.project_name:  # Enter the desired project name here
                                self.project_id = _project['id']

                    else:
                        # Find which project name matches the project ID provided
                        for _project in _projects:
                            if _project['id'] == self.project_id:  # Enter the desired project id here
                                self.project_name = _project['name']
        else:
            print("""
            This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.
            Current Intelligence Server version: {}
            Current MicroStrategy Web version: {}
            """.format(self.__iserver_version,self.__web_version))
            raise VersionException('MicroStrategy Version not supported.')

    def close(self):
        """Closes a connection with MicroStrategy REST API"""
        authentication.logout(connection=self)

    def __check_version(self):
        """Checks version of I-Server and MicroStrategy Web"""
        response = misc.server_status(self)
        if not response.ok:
            msg = 'Failed to check server status'
            self.__response_handler(response=response, msg=msg)
        else:
            json_response = response.json()
            self.__iserver_version = json_response["iServerVersion"][:9]
            self.__web_version = json_response["webVersion"][:9]
            
            iserver_version_ok = version.parse(self.__iserver_version) >= version.parse(self.__VRCH)
            web_version_ok = version.parse(self.__web_version) >= version.parse(self.__VRCH)
            
            return iserver_version_ok and web_version_ok

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

        # warning for future deprecation / replacement by Report class
        warnings.warn(
            "This method will be deprecated. The Report constructor is preferred.",
            DeprecationWarning
        )

        response = reports.report_instance(connection=self,
                                           report_id=report_id,
                                           offset=offset,
                                           limit=limit)

        if not response.ok:
            msg = "Error getting report contents."
            self.__response_handler(response=response, msg=msg)
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

        # warning for future deprecation / replacement by Cube class
        warnings.warn(
            "This method will be deprecated. The Cube constructor is preferred and supports multi-table data.",
            DeprecationWarning
        )

        response = cubes.cube_instance(connection=self, cube_id=cube_id, offset=offset, limit=limit)

        if not response.ok:
            msg = "Error getting cube contents."
            self.__response_handler(response=response, msg=msg)
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

    def create_dataset(self, data_frame, dataset_name, table_name, to_metric=None, to_attribute=None, folder_id=None):
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
        :param folder_id: (optional) ID of the shared folder that the dataset should be created within. If `None`,
            defaults to the user's My Reports folder.
        :return: Unique identifiers of the dataset and table within the newly created dataset. Required for
        update_dataset()
        """

        # warning for future deprecation / replacement by Datasets class
        warnings.warn(
            "This method will be deprecated. The Dataset constructor is preferred and supports multi-table data.",
            DeprecationWarning
        )

        # Replace any leading/trailing whitespace in df names, replace '.' with '_'
        _df = data_frame.copy()
        _df.columns = _df.columns.str.replace(".", "_")
        _df.columns = _df.columns.str.strip()

        if folder_id is None:
            folder_id = ""
        else:
            folder_id = folder_id

        # create dataset instance
        ds = Dataset(connection=self, name=dataset_name)

        # add table to the dataset
        ds.add_table(name=table_name, data_frame=_df, update_policy='add', to_metric=to_metric, to_attribute=to_attribute)

        # publish the dataset
        ds.create(folder_id=folder_id)

        return ds.dataset_id

    def update_dataset(self, data_frame, dataset_id, table_name, update_policy):

        """
        Update a previously created dataset with an Pandas Data Frame

        :param data_frame: Pandas Data Frame to use to update an in-memory dataset
        :param dataset_id: Identifier of the dataset to update, provided by create_dataset()
        :param table_name: Name of the table to update within the dataset
        :param update_policy: Update operation to perform. One of 'add' (inserts new, unique rows), 'update'
        (updates data in existing rows and columns), 'upsert' (updates existing
        data and inserts new rows), 'replace' (similar to truncate and load, replaces the existing data with new data)
        """

        # warning for future deprecation / replacement by Datasets class
        warnings.warn(
            "This method will be deprecated. The Dataset constructor is preferred and supports multi-table data.",
            DeprecationWarning
        )

        # Replace any leading/trailing whitespace in df names, replace '.' with '_'
        _df = data_frame.copy()
        _df.columns = _df.columns.str.replace(".", "_")
        _df.columns = _df.columns.str.strip()

        # create dataset instance, add table, then publish the updates to the dataset
        ds = Dataset(connection=self, dataset_id=dataset_id)
        ds.add_table(name=table_name, data_frame=_df, update_policy=update_policy)
        ds.update()
        ds.publish()

    def renew(self):
        """Checks if the session is still alive. If so, renews the session and extends session expiration."""
        response = authentication.sessions(connection=self)

        if not response.ok:
            msg = "Session expired. Please reconnect to MicroStrategy."
            self.__response_handler(response=response, msg=msg)
        else:
            print("MicroStrategy connection was renewed.")

    @staticmethod
    def __response_handler(response, msg):
        """Generic error message handler for transactions against datasets.

        Args:
            response: Response object returned by HTTP request.
            msg (str): Message to print in addition to any server-generated error message(s).

        """

        if response.status_code == 204:
            warnings.warn(
                '204 No Content: The server successfully processed the request and is not returning any content.')
        else:
            res = response.json()
            print("I-Server Error %s, %s" % (res['code'], res['message']))
            response.raise_for_status()

class VersionException(Exception):
    pass
