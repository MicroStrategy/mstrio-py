# TODO (srigney): Create method to select project, call it 'select_project'
from packaging import version

from mstrio.api import authentication, cubes, misc, projects, reports
from mstrio.dataset import Dataset
import mstrio.utils.helper as helper
from mstrio.utils.parser import Parser


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
    __VRCH = "11.1.0400"

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

        self.base_url = helper.url_check(base_url)
        self.username = username
        self.password = password
        if project_id is not None and project_name is not None:
            helper.exception_handler(msg="Provide either Project ID or Project Name.", exception_type=ValueError)
        else:
            self.project_id = project_id
            self.project_name = project_name
        self.login_mode = login_mode
        self.ssl_verify = ssl_verify
        self.web_version = None
        self.iserver_version = None

    def connect(self):
        """Creates a connection"""
        if Connection.__check_version(self):
            response = authentication.login(connection=self)
            self.auth_token, self.cookies = response.headers['X-MSTR-AuthToken'], dict(response.cookies)

            # Fetch the list of projects the user has access to
            msg = "Error connecting to project '{}'. Check project name and try again.".format(self.project_name)
            response = projects.projects(connection=self, error_msg=msg)

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
            """.format(self.iserver_version, self.web_version))
            helper.exception_handler(msg="MicroStrategy Version not supported.", exception_type=VersionException)

    def close(self):
        """Closes a connection with MicroStrategy REST API"""
        authentication.logout(connection=self)

    def renew(self):
        """Checks if the session is still alive. If so, renews the session and extends session expiration."""
        _ = authentication.sessions(connection=self)

        print("MicroStrategy connection was renewed.")

    def __check_version(self):
        """Checks version of I-Server and MicroStrategy Web"""
        response = misc.server_status(self)

        json_response = response.json()
        self.iserver_version = json_response["iServerVersion"][:9]
        self.web_version = json_response["webVersion"][:9]

        iserver_version_ok = version.parse(self.iserver_version) >= version.parse(self.__VRCH)
        web_version_ok = version.parse(self.web_version) >= version.parse(self.__VRCH)

        return iserver_version_ok and web_version_ok


class VersionException(Exception):
    pass
